import unittest
from typing import Any, Dict
from unittest.mock import patch

from packaging.version import Version

from ..core import _fetch_versions, fix
from ..vrange import VersionIntervals

VERSIONS = [("1.0", None), ("1.2", None), ("1.2.3", ">=3.8")]
PRE_VERSIONS = [("1.2.4a0", ">=3.8"), ("1.2.4a1", ">=3.8")]
FAKE_PROJECT_FOO_METADATA = {
    "releases": {
        str(k): [
            {
                "filename": f"foo-{k}.tgz",
                "packagetype": "sdist",
                "requires_python": rp,
            }
        ]
        for k, rp in VERSIONS
    },
}

PROJECTS = {
    "foo": [Version(x) for x, y in VERSIONS],
    "foup": [Version(x) for x, y in [*VERSIONS, *PRE_VERSIONS]],
    "empty": [],
}


class FakeResponse:
    def __init__(self, status: int, metadata: Dict[Any, Any]) -> None:
        self._status = status
        self._json = metadata

    def raise_for_status(self) -> None:
        if self._status != 200:
            raise Exception(f"Status {self._status}")

    def json(self) -> Dict[Any, Any]:
        return self._json


class FixTest(unittest.TestCase):
    @patch("bumpreqs.core._fetch_versions", side_effect=PROJECTS.get)
    def test_basic(self, fetch_versions_mock: Any) -> None:
        # leave comments alone
        self.assertEqual("  # comment", fix("  # comment"))
        self.assertEqual("  # comment\n", fix("  # comment\n"))

        # fixes missing newline
        self.assertEqual("foo==1.2.3\n", fix("foo==0.9"))
        self.assertEqual("foo==1.2.3\n", fix("foo==0.9\n"))
        self.assertEqual("foo==1.2.3\n", fix("foo\n"))

        # leaves alone >= unless force
        self.assertEqual("foo>=0.9\n", fix("foo>=0.9\n"))
        self.assertEqual("foo==1.2.3\n", fix("foo>=0.9\n", force=True))

        # preserves comment and exact whitespace
        self.assertEqual(
            "foo==1.2.3    # com ment\n", fix("foo==1.2.2    # com ment\n")
        )

        # preserves conditionals
        self.assertEqual(
            'foo==1.2.3; python_version >= "3.6"\n',
            fix('foo==1.2.2 ; python_version >= "3.6"\n'),
        )

    @patch("bumpreqs.core._fetch_versions", side_effect=PROJECTS.get)
    @patch("bumpreqs.core.LOG.warning")
    def test_git_version(self, warning_mock: Any, fetch_versions_mock: Any) -> None:
        url = "-e git+git://...#egg_info"
        self.assertEqual(url, fix(url))
        warning_mock.assert_called_with(
            "Not bumping option/url line for %r", "-e git+git://...#egg_info"
        )

    @patch("bumpreqs.core._fetch_versions", side_effect=PROJECTS.get)
    def test_pre_handling(self, fetch_versions_mock: Any) -> None:
        self.assertEqual("foup==1.2.4a1\n", fix("foup==1.2.4a0"))
        self.assertEqual("foup==1.2.4a1\n", fix("foup==1.2.4a1"))
        # current version doesn't need to exist
        self.assertEqual("foup==1.2.4a1\n", fix("foup==1.2.4a9"))
        # same but without pre- intent
        self.assertEqual("foup==1.2.3\n", fix("foup==1.2.5"))
        # force with pre- intent
        self.assertEqual("foup==1.2.4a1\n", fix("foup>=1.0a1", force=True))

    @patch("bumpreqs.core._fetch_versions", side_effect=lambda x, v=None: PROJECTS[x])
    @patch("bumpreqs.core.LOG.warning")
    def test_fetch_messages(self, warning_mock: Any, fetch_versions_mock: Any) -> None:
        self.assertEqual("nope==1.0", fix("nope==1.0"))
        warning_mock.assert_called_with(
            "Failed to fetch versions for %r: %s", "nope", "KeyError('nope')"
        )

    @patch("bumpreqs.core._fetch_versions", side_effect=lambda x, v=None: PROJECTS[x])
    @patch("bumpreqs.core.LOG.warning")
    def test_no_releases(self, warning_mock: Any, fetch_versions_mock: Any) -> None:
        self.assertEqual("empty==1.0", fix("empty==1.0"))
        warning_mock.assert_called_with("No candidate versions for %r", "empty==1.0")

    @patch("bumpreqs.core._fetch_versions", side_effect=lambda x, v=None: PROJECTS[x])
    @patch("bumpreqs.core.LOG.warning")
    def test_url(self, warning_mock: Any, fetch_versions_mock: Any) -> None:
        self.assertEqual(
            "empty @ https://example.com/", fix("empty @ https://example.com/")
        )
        warning_mock.assert_called_with(
            "Not bumping option/url line for %r", "empty @ https://example.com/"
        )

    @patch("bumpreqs.core._fetch_versions", side_effect=lambda x, v=None: PROJECTS[x])
    @patch("bumpreqs.core.LOG.warning")
    def test_old_python(self, warning_mock: Any, fetch_versions_mock: Any) -> None:
        # The mock doesn't know about py version
        self.assertEqual(
            'foo==1.2.3; python_version < "3.6"\n',
            fix("foo==1.0; python_version<'3.6'"),
        )
        fetch_versions_mock.assert_called_with("foo", VersionIntervals.from_str("<3.6"))

    @patch("bumpreqs.core.LOG.warning")
    def test_too_complicated(self, warning_mock: Any) -> None:
        self.assertEqual(
            "foo==1.0; python_version<='3.6'",
            fix("foo==1.0; python_version<='3.6'"),
        )
        warning_mock.assert_called_with(
            "Python version comparison too complex for %r",
            "foo==1.0; python_version<='3.6'",
        )


class FetchVersionsTest(unittest.TestCase):
    @patch("bumpreqs.core.requests.get")
    def test_success(self, get_mock: Any) -> None:
        get_mock.return_value = FakeResponse(200, FAKE_PROJECT_FOO_METADATA)
        self.assertEqual([Version(x) for x, y in VERSIONS], _fetch_versions("foo"))
        get_mock.assert_called_with("https://pypi.org/pypi/foo/json")

    @patch("bumpreqs.core.requests.get")
    def test_recent_version(self, get_mock: Any) -> None:
        get_mock.return_value = FakeResponse(200, FAKE_PROJECT_FOO_METADATA)
        self.assertEqual(
            [Version(x) for x, y in VERSIONS],
            _fetch_versions("foo", VersionIntervals.from_str("<3.9")),
        )
        self.assertEqual(
            [Version(x) for x, y in VERSIONS],
            _fetch_versions("foo", VersionIntervals.from_str(">=3.6")),
        )
        get_mock.assert_called_with("https://pypi.org/pypi/foo/json")

    @patch("bumpreqs.core.requests.get")
    def test_older_version(self, get_mock: Any) -> None:
        get_mock.return_value = FakeResponse(200, FAKE_PROJECT_FOO_METADATA)
        self.assertEqual(
            [Version("1.0"), Version("1.2")],
            _fetch_versions("foo", VersionIntervals.from_str("<3.8")),
        )
        get_mock.assert_called_with("https://pypi.org/pypi/foo/json")
