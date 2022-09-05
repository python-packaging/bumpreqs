import unittest

from packaging.specifiers import Specifier, SpecifierSet

from ..vrange import TooComplicated, VersionIntervals


class VersionIntervalsTest(unittest.TestCase):
    def test_init(self) -> None:
        self.assertEqual("", str(VersionIntervals()))

        self.assertEqual(">=2", str(VersionIntervals.from_specifier(Specifier(">=2"))))
        self.assertEqual("<9", str(VersionIntervals.from_specifier(Specifier("<9"))))

        self.assertEqual(
            ">=2,<9", str(VersionIntervals.from_specifier_set(SpecifierSet(">=2,<9")))
        )

        self.assertEqual(">=2.0,<3", str(VersionIntervals.from_str("==2.*")))
        self.assertEqual(">=2.1.0,<2.2", str(VersionIntervals.from_str("==2.1.*")))
        self.assertEqual(">=2.0.0,<2.0.1", str(VersionIntervals.from_str("==2.0.0")))

        # TODO somewhere might need to care about this precision...
        self.assertEqual(">=2.0.0,<2.0.1", str(VersionIntervals.from_str("==2")))
        self.assertEqual(">=2.0.0,<2.0.1", str(VersionIntervals.from_str("==2.0")))

        self.assertEqual(
            ">=2.6,<3.0.0,>=3.3,<4",
            str(VersionIntervals.from_str(">=2.6, !=3.0.*, !=3.1.*, !=3.2.*, <4")),
        )

    def test_complex(self) -> None:
        with self.assertRaises(TooComplicated):
            VersionIntervals.from_str("<=9")

    def test_intersect_interval(self) -> None:
        a = VersionIntervals.from_str(">=3.7")
        self.assertEqual(
            ">=3.7,<4",
            str(a.intersect(VersionIntervals.from_str("<4"))),
        )

    def test_intersect_no_change(self) -> None:
        a = VersionIntervals.from_str(">=3.7")
        b = VersionIntervals.from_str(">=3.1")
        c = a.intersect(b)
        self.assertEqual(">=3.7", str(c))
        self.assertTrue(c)

    def test_intersect_impossible(self) -> None:
        a = VersionIntervals.from_str(">=3.7")
        b = VersionIntervals.from_str("<3.7")
        c = a.intersect(b)
        self.assertEqual("NONE", str(c))
        self.assertFalse(c)

    def test_simplify(self) -> None:
        a = VersionIntervals.from_str("<3.7")
        b = VersionIntervals.from_str(">=3.7,<4")
        c = a.union(b)
        self.assertEqual("<4", str(c))
        self.assertTrue(c)

    def test_eq(self) -> None:
        a = VersionIntervals.from_str("<3.7")
        b = VersionIntervals.from_str(">=3.7,<4")
        self.assertFalse(a == b)
        self.assertTrue(a == a)

    def test_not_equal_no_star(self) -> None:
        with self.assertRaises(TooComplicated):
            VersionIntervals.from_str("!=1.2.3")
