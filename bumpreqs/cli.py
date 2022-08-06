from pathlib import Path

from typing import List, Optional

import click
from moreorless.click import echo_color_unified_diff

from .core import fix


@click.command()
@click.option("--diff", is_flag=True, default=None)
@click.option("--write", is_flag=True)
@click.argument("filenames", nargs=-1)
def main(diff: Optional[bool], write: bool, filenames: List[str]) -> None:
    if not filenames:
        click.echo("Provide filenames")
        return

    if diff is None and not write:
        diff = True

    for f in filenames:
        print(f)
        old_text = Path(f).read_text()
        new_text = fix(old_text)
        if diff:
            echo_color_unified_diff(old_text, new_text, f)
        if write:
            Path(f).write_text(new_text)


if __name__ == "__main__":
    main()
