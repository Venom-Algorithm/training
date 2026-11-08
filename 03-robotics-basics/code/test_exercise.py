"""按 --level basic 或 --level advanced 检查作业，默认检查基础。"""
import argparse
import importlib.util
import math
from pathlib import Path
import unittest


def load_solution(path):
    spec = importlib.util.spec_from_file_location("student_solution", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VectorAssertions(unittest.TestCase):
    def assertVectorAlmostEqual(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for a, b in zip(actual, expected):
            self.assertTrue(math.isfinite(a))
            self.assertAlmostEqual(a, b, places=8)


class BasicGeometryTests(VectorAssertions):
    def test_optical_forward(self):
        self.assertVectorAlmostEqual(solution.optical_to_link((0, 0, 3)), (3, 0, 0))

    def test_optical_right_down(self):
        self.assertVectorAlmostEqual(solution.optical_to_link((1, 2, 3)), (3, -1, -2))

    def test_optical_up(self):
        self.assertVectorAlmostEqual(solution.optical_to_link((0, -2, 0)), (0, 0, 2))

    def test_aim_forward(self):
        self.assertVectorAlmostEqual(solution.aim_angles((1, 0, 0)), (0, 0))

    def test_aim_left_and_up_45(self):
        self.assertVectorAlmostEqual(solution.aim_angles((0, 1, 1)), (math.pi / 2, math.pi / 4))

    def test_aim_right_and_down_45(self):
        self.assertVectorAlmostEqual(solution.aim_angles((0, -1, -1)), (-math.pi / 2, -math.pi / 4))

    def test_aim_third_quadrant(self):
        self.assertVectorAlmostEqual(solution.aim_angles((-1, -1, 0)), (-3 * math.pi / 4, 0))

    def test_aim_zero_horizontal(self):
        for p in [(0, 0, 0), (0, 0, 1), (0, 0, -1), (1e-13, 0, 1)]:
            with self.subTest(point=p), self.assertRaises(ValueError):
                solution.aim_angles(p)

    def test_aim_nonfinite(self):
        for p in [(math.nan, 1, 1), (1, math.inf, 1), (1, 1, -math.inf)]:
            with self.subTest(point=p), self.assertRaises(ValueError):
                solution.aim_angles(p)


class AdvancedGeometryTests(VectorAssertions):
    def small_yaw_to_base(self, point=(2, 0, 0.5), big_yaw=0, small_yaw=0,
                          small_offset=(0.3, 0.2, 0), big_offset=(0, 0, 0.2)):
        return solution.small_yaw_to_base(point, big_yaw, small_yaw, small_offset, big_offset)

    def test_no_rotation_or_offset(self):
        actual = self.small_yaw_to_base((1, 2, 3), small_offset=(0, 0, 0), big_offset=(0, 0, 0))
        self.assertVectorAlmostEqual(actual, (1, 2, 3))

    def test_small_yaw_90(self):
        self.assertVectorAlmostEqual(self.small_yaw_to_base(small_yaw=math.pi / 2), (0.3, 2.2, 0.7))

    def test_big_yaw_90(self):
        self.assertVectorAlmostEqual(self.small_yaw_to_base(big_yaw=math.pi / 2), (-0.2, 2.3, 0.7))

    def test_opposite_yaw_with_offset(self):
        actual = self.small_yaw_to_base(big_yaw=math.pi / 2, small_yaw=-math.pi / 2)
        self.assertVectorAlmostEqual(actual, (1.8, 0.3, 0.7))

    def test_offsets_use_their_own_frames(self):
        actual = self.small_yaw_to_base((0, 0, 0), big_yaw=math.pi / 2, small_yaw=-math.pi / 2,
                                       small_offset=(0.3, 0.2, 0.1), big_offset=(1, 2, 0.2))
        self.assertVectorAlmostEqual(actual, (0.8, 2.3, 0.3))

    def test_two_quarter_turns_without_offset(self):
        actual = self.small_yaw_to_base((2, 1, 3), big_yaw=math.pi / 2, small_yaw=math.pi / 2,
                                       small_offset=(0, 0, 0), big_offset=(0, 0, 0))
        self.assertVectorAlmostEqual(actual, (-2, -1, 3))

    def test_small_yaw_mounted_on_right(self):
        actual = self.small_yaw_to_base(big_yaw=math.pi / 2, small_yaw=-math.pi / 2,
                                       small_offset=(0.3, -0.2, 0))
        self.assertVectorAlmostEqual(actual, (2.2, 0.3, 0.7))

    def test_negative_non_right_angles(self):
        actual = self.small_yaw_to_base((2, 1, 0.5), big_yaw=-math.pi / 6, small_yaw=-math.pi / 3,
                                       small_offset=(0.3, 0.2, 0.1), big_offset=(0.4, -0.5, 0.2))
        self.assertVectorAlmostEqual(actual, (1.7598076211353315, -2.4767949192431122, 0.8))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", choices=("basic", "advanced"), default="basic")
    parser.add_argument("--solution", type=Path, default=Path(__file__).with_name("exercise.py"),
                        help="待检查的代码文件，默认 exercise.py")
    args = parser.parse_args()
    global solution
    solution = load_solution(args.solution)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(BasicGeometryTests)
    if args.level == "advanced":
        suite.addTests(loader.loadTestsFromTestCase(AdvancedGeometryTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
