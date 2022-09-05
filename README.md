# bumpreqs

Usage

```shell-session
$ pip install bumpreqs
$ python -m bumpreqs --write requirements*.txt
```

It will update the requirements to all use the latest versions.  Most
environment markers are ignored (although preserved on modified lines).


## `python_version` and `full_python_version`

There is some rudimentary support that works for simple comparisons using the
`and` operator (as in `requires_python` using `,`).  If there is _any_ overlap
between the constraint and release's `requires_python`, then it can be bumped.

The reason to check for _any_ overlap rather than _full_ overlap is because many
project specify a constraint like `python_version < "3.7"` without a lower
bound, and when checking against a release that has `Requires-Python: >=3.6` the
check would fail because `3.5` (or `2.1` or any other silly example) is not
included.  See currently open issue for future work.


# License

bumpreqs is copyright [Tim Hatch](https://timhatch.com/), and licensed under
the MIT license.  I am providing code in this repository to you under an open
source license.  This is my personal repository; the license you receive to
my code is from me and not from my employer. See the `LICENSE` file for details.
