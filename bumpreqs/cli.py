import sys
from pathlib import Path

from typing import List

import click

import requests

from moreorless.click import echo_color_unified_diff
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import parse as parse_version, Version


def fix(text: str) -> str:
    new_lines = []
    for line in text.splitlines(True):
        (value, _, comment) = line.strip().partition("#")
        right_whitespace = value[len(value.rstrip()) :]
        value = value.rstrip()

        req = Requirement(value)
        if req.url:
            # Skip git, etc
            new_lines.append(line)
            continue

        if "==" not in line and any(x in line for x in "<>=~"):
            # Skip non-concrete deps in the hackiest way possible
            new_lines.append(line)
            continue

        obj = requests.get(f"https://pypi.org/pypi/{req.name}/json").json()
        releases = [parse_version(v) for v in obj["releases"].keys()]

        # TODO this ought to use the install_requires from the project if easily
        # accessible, which would also give a hint on whether pre are allowed.
        # Right now this will downgrade any pre
        latest_version = max([v for v in releases if not v.is_prerelease])

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


@click.command()
@click.option("--diff", is_flag=True, default=True)
@click.option("--write", is_flag=True)
@click.argument("filenames", nargs=-1)
def main(diff: bool, write: bool, filenames: List[str]) -> None:
    if not filenames:
        click.echo("Provide filenames")
        return

    for f in filenames:
        old_text = Path(f).read_text()
        new_text = fix(old_text)
        if diff:
            echo_color_unified_diff(old_text, new_text, f)
        if write:
            Path(f).write_text(new_text)


if __name__ == "__main__":
    main()
