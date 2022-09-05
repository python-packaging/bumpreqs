import unittest

from packaging.markers import Marker

from ..marker_extract import _extract_python_internal, extract_python
from ..vrange import TooComplicated


class MarkerExtractTest(unittest.TestCase):
    def test_simple_behavior(self) -> None:
        m = Marker(
            "(python_version >= '3.3' and python_version < '4') and sys_platform=='linux'"
        )
        self.assertEqual(
            [
                ("python_version", ">=", "3.3"),
                ("python_version", "<", "4"),
            ],
            list(_extract_python_internal(m._markers)),
        )

    def test_or_behavior_unfortunate(self) -> None:
        # TODO: This isn't right, but it's what we do currently.  Only about 2%
        # of projects that have version-dependent deps use 'or' and we can't see
        # this in requires_python on the target project -- it would be on the
        # project you're currently running against.
        m = Marker("python_version >= '3.3' or python_version < '4'")
        self.assertEqual(
            [
                ("python_version", ">=", "3.3"),
                ("python_version", "<", "4"),
            ],
            list(_extract_python_internal(m._markers)),
        )

    def test_rhs_variable_flip(self) -> None:
        m = Marker("'3.3' >= python_version")
        self.assertEqual(
            [
                ("python_version", "<", "3.3"),
            ],
            list(_extract_python_internal(m._markers)),
        )

    def test_rhs_variable_flip_toocomplicated(self) -> None:
        m = Marker("'3.3' in python_version")
        with self.assertRaises(TooComplicated):
            list(_extract_python_internal(m._markers))

    def test_extract_python(self) -> None:
        m = Marker("sys_platform == 'linux'")
        self.assertEqual(None, extract_python(m))

        m = Marker("python_version >= '3.3' and python_version < '4'")
        self.assertEqual(">=3.3,<4", str(extract_python(m)))
