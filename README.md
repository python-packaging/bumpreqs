# bumpreqs

Usage

```shell-session
$ pip install bumpreqs
$ python -m bumpreqs --write requirements*.txt
```

It will update the requirements to all use the latest versions.  It doesn't care
about `requires_python` or really any other constraints.  Similar in that
respect to dependabot or pyup, although it won't update to a pre unless it's
already on a pre.


# License

bumpreqs is copyright [Tim Hatch](https://timhatch.com/), and licensed under
the MIT license.  I am providing code in this repository to you under an open
source license.  This is my personal repository; the license you receive to
my code is from me and not from my employer. See the `LICENSE` file for details.
