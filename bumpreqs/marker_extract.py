from typing import Any, Iterator, Optional, Tuple

from packaging.markers import Marker, Variable

from .vrange import TooComplicated, VersionIntervals

# This does not include all operators, notably the string comparisons "in", "not
# in", and "~=" have no way to flip.
CONVERSE_MAP = {
    "===": "===",
    "==": "==",
    "!=": "!=",
    "<": ">=",
    "<=": ">",
    ">": "<=",
    ">=": "<",
}

# This is largely patterend after packaging/markers.py:_evaluate_markers
# The  tuple is e.g. ("python_version", ">=", "3.0") and the version will always
# be the last item.
def _extract_python_internal(markers: Any) -> Iterator[Tuple[str, str, str]]:
    for marker in markers:
        if isinstance(marker, list):
            yield from _extract_python_internal(marker)
        elif isinstance(marker, tuple):
            lhs, op, rhs = marker

            # packaging appears to have an additional restriction not mentioned
            # in the grammar, that you can't compare two Variables or two
            # literals.  Duplicate that here.
            if isinstance(lhs, Variable):
                if lhs.value in ("python_version", "python_full_version"):
                    yield (lhs.value, op.value, rhs.value)
            else:
                if rhs.value in ("python_version", "python_full_version"):
                    if op.value in CONVERSE_MAP:
                        yield (rhs.value, CONVERSE_MAP[op.value], lhs.value)
                    else:
                        raise TooComplicated
        # TODO: else 'and' 'or'


def extract_python(markers: Optional[Marker]) -> Optional[VersionIntervals]:
    allow_all = VersionIntervals()
    vi = VersionIntervals()

    if markers is None:
        return None

    for (var, op, value) in _extract_python_internal(markers._markers):
        vi = vi.intersect(VersionIntervals.from_str(f"{op}{value}"))

    if vi == allow_all:
        return None

    return vi
