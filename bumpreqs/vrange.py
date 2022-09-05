from __future__ import annotations

from typing import List, Optional, Tuple

from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version

IN = 1
OUT = -1

SELF = "SELF"
OTHER = "OTHER"

MIN = Version("0")
MAX = Version("999!1")

Event = Tuple[Version, int]
EventList = List[Event]


class TooComplicated(Exception):
    pass


class VersionIntervals:
    """
    Envision version constraints as intervals on a line.
    """

    def __init__(self, events: Optional[EventList] = None) -> None:
        if events is not None:
            self._events = events[:]
        else:
            self._events = [
                (MIN, IN),
                (MAX, OUT),
            ]

    @classmethod
    def from_specifier(cls, specifier: Specifier) -> VersionIntervals:
        t = cls()
        t.add_specifier(specifier)
        return t

    @classmethod
    def from_specifier_set(cls, specifier_set: SpecifierSet) -> VersionIntervals:
        t = cls()
        for spec in specifier_set._specs:
            if not isinstance(spec, Specifier):  # pragma: no cover
                raise ValueError(f"Unknown specifier type {type(spec)}")
            t.add_specifier(spec)
        return t

    @classmethod
    def from_str(cls, s: str) -> VersionIntervals:
        t = cls.from_specifier_set(SpecifierSet(s))
        return t

    def add_specifier(self, specifier: Specifier) -> VersionIntervals:
        tmp: EventList
        if specifier.operator == "<":
            tmp = [
                (MIN, IN),
                (Version(specifier.version), OUT),
            ]
        elif specifier.operator == ">=":
            tmp = [
                (Version(specifier.version), IN),
                (MAX, OUT),
            ]
        elif specifier.operator == "==":
            parts = specifier.version.split(".")
            # TODO: This is a little inexact
            try:
                idx = parts.index("*")
                next_parts = parts[: idx - 1] + [str(int(parts[idx - 1]) + 1)]
                tmp = [
                    (Version(specifier.version.replace("*", "0")), IN),
                    (Version(".".join(next_parts)), OUT),
                ]
            except ValueError:
                while len(parts) < 3:
                    parts.append("0")

                next_parts = parts[:-1] + [str(int(parts[-1]) + 1)]
                tmp = [
                    (Version(".".join(parts)), IN),
                    (Version(".".join(next_parts)), OUT),
                ]
        elif specifier.operator == "!=":
            parts = specifier.version.split(".")
            try:
                idx = parts.index("*")
                next_parts = parts[: idx - 1] + [str(int(parts[idx - 1]) + 1)]
                tmp = [
                    (MIN, IN),
                    (Version(specifier.version.replace("*", "0")), OUT),
                    (Version(".".join(next_parts)), IN),
                    (MAX, OUT),
                ]
            except ValueError:
                # TODO
                raise TooComplicated

        else:
            raise TooComplicated(specifier.operator)

        self._events = self._intersect(self._events + tmp)

        return self

    def intersect(self, other: VersionIntervals) -> VersionIntervals:
        t = VersionIntervals(
            self._intersect(self._events + other._events),
        )
        return t

    @classmethod
    def _intersect(self, other: EventList) -> EventList:

        new_events: EventList = []
        state = 0
        # Need "OUT" handled before "IN"
        for (v, ev) in sorted(other, key=lambda i: (i[0], i[1])):
            old_state = state
            state += ev
            if state == 2:
                new_events.append((v, ev))
            elif old_state == 2:
                new_events.append((v, ev))

        assert state == 0
        return new_events

    def union(self, other: VersionIntervals) -> VersionIntervals:
        t = VersionIntervals(
            self._union(self._events + other._events),
        )
        return t

    @classmethod
    def _union(self, other: EventList) -> EventList:

        new_events: EventList = []
        state = 0
        # Need "OUT" handled before "IN"
        for (v, ev) in sorted(other, key=lambda i: (i[0], i[1])):
            old_state = state
            state += ev
            if state >= 1:
                if new_events and new_events[-1] == (v, -ev):
                    del new_events[-1]
                else:
                    new_events.append((v, ev))
            elif old_state >= 1:
                new_events.append((v, ev))

        assert state == 0
        return new_events

    def __str__(self) -> str:
        buf: List[str] = []

        if self._events == []:
            return "NONE"

        for (v, ev) in self._events:
            if (ev == IN and v == MIN) or (ev == OUT and v == MAX):
                continue

            if ev == IN:
                buf.append(f">={v}")
            elif ev == OUT:
                buf.append(f"<{v}")
            else:  # pragma: no cover
                raise ValueError((v, ev))

        return ",".join(buf)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, VersionIntervals) and self._events == other._events

    def __bool__(self) -> bool:
        return bool(self._events)
