import logging

from typing import List, Optional, Union

import requests

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import LegacyVersion, parse as parse_version, Version

from .marker_extract import extract_python

from .vrange import TooComplicated, VersionIntervals

LOG = logging.getLogger(__name__)


def fix(text: str, force: Optional[bool] = False) -> str:
    new_lines = []
    for line in text.splitlines(True):
        # This is an overly simplistic parser for requirements files, see
        # pip/req/req_file.py for the real one.
        (value, _, comment) = line.strip().partition("#")
        right_whitespace = value[len(value.rstrip()) :]

        # See COMMENT_RE in pip/req/req_file.py
        if value and comment and not right_whitespace:
            value = line.strip()
            comment = ""
        else:
            value = value.rstrip()

        if not value:
            new_lines.append(line)
            continue

        if value.startswith("-") or "://" in value:
            # Skip git, etc
            LOG.warning("Not bumping option/url line for %r", value)
            new_lines.append(line)
            continue

        req = Requirement(value)
        assert not req.url

        try:
            only_on_python = extract_python(req.marker)
        except TooComplicated:
            LOG.warning("Python version comparison too complex for %r", value)
            new_lines.append(line)
            continue

        # Only operate on `project` and `project==ver` for now.
        # Skip non-concrete specifiers in the hackiest way possible.
        if "==" not in line and any(x in line for x in "<>=~") and not force:
            new_lines.append(line)
            continue

        try:
            releases = _fetch_versions(req.name, only_on_python)
        except Exception as e:
            LOG.warning("Failed to fetch versions for %r: %s", req.name, repr(e))
            new_lines.append(line)
            continue

        # TODO this ought to use the install_requires from the project if easily
        # accessible, which would also give a hint on whether pre are allowed.
        # For now we just get the pre- intent from the existing pin
        if req.specifier.prereleases:
            candidates = releases
        else:
            candidates = [v for v in releases if not v.is_prerelease]

        if not candidates:
            LOG.warning("No candidate versions for %r", value)
            new_lines.append(line)
            continue

        latest_version = max(candidates)

        new_specifier = SpecifierSet(f"=={latest_version}")
        if req.specifier != new_specifier:
            # print(f"Bump {req.name} from {req.specifier} to {new_specifier}")
            pass

        req.specifier = new_specifier

        new_line = str(req)
        if comment:
            new_line += right_whitespace + "#" + comment
        new_lines.append(new_line + "\n")  # Not sorry

    return "".join(new_lines)


def _fetch_versions(
    project_name: str,
    only_for_python: Optional[VersionIntervals] = None,
) -> List[Union[LegacyVersion, Version]]:
    resp = requests.get(f"https://pypi.org/pypi/{project_name}/json")
    resp.raise_for_status()
    obj = resp.json()

    versions: List[Union[LegacyVersion, Version]] = []
    for k, v in obj["releases"].items():
        # Skip older releases that have no archives
        if not v:
            continue
        requires_python = v[0].get("requires_python")
        if requires_python and only_for_python:
            if only_for_python.intersect(VersionIntervals.from_str(requires_python)):
                versions.append(parse_version(k))
        else:
            versions.append(parse_version(k))

    return versions
