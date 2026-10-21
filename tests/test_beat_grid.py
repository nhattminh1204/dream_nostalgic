import unittest

from tests import helpers  # noqa: F401  (thêm tools/ vào sys.path)
import episode_state as es


class PlanShapeTest(unittest.TestCase):
    def test_80bpm_generic(self):
        p = es.plan_shape(80, 0.0, 30.0, 3.5, (15, 20), 5)
        self.assertEqual(p["beats_per_scene"], 4)
        self.assertEqual(p["scenes"], 6)
        self.assertAlmostEqual(p["scene_seconds"], 3.0)
        self.assertAlmostEqual(p["total_seconds"], 18.0)
        self.assertTrue(p["bar_aligned"])
        self.assertEqual(p["warnings"], [])

    def test_85bpm_target_18s_gives_6_scenes(self):
        p = es.plan_shape(85, 0.0, 30.0, 3.5, (15, 18), 5)
        self.assertEqual(p["beats_per_scene"], 4)
        self.assertEqual(p["scenes"], 6)
        self.assertTrue(p["bar_aligned"])

    def test_100bpm_not_bar_aligned_keeps_min_scenes(self):
        p = es.plan_shape(100, 0.0, 30.0, 3.5, (15, 20), 5)
        self.assertEqual(p["beats_per_scene"], 6)
        self.assertEqual(p["scenes"], 5)
        self.assertFalse(p["bar_aligned"])
        self.assertTrue(any("giữa ô nhịp" in w for w in p["warnings"]))

    def test_max_clip_limits_beats(self):
        # 60 BPM: 4 phách = 4s, 6 phách = 6s; clip tối đa 5s -> chỉ 4 phách hợp lệ
        p = es.plan_shape(60, 0.0, 30.0, 5.5, (15, 20), 5)
        self.assertEqual(p["beats_per_scene"], 4)

    def test_intro_shorter_than_target(self):
        p = es.plan_shape(80, 0.0, 12.0, 3.5, (15, 20), 5)
        self.assertEqual(p["scenes"], 5)
        self.assertTrue(any("intro" in w for w in p["warnings"]))

    def test_start_offset_reduces_usable_intro(self):
        p = es.plan_shape(80, 10.0, 30.0, 3.5, (15, 20), 5)
        self.assertLessEqual(p["total_seconds"], 20.0)
        self.assertEqual(p["scenes"], 6)


class CutTimesTest(unittest.TestCase):
    def test_exact_at_80(self):
        self.assertEqual(es.cut_times(4, 6, 80), [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0])

    def test_no_accumulated_rounding(self):
        for bpm in (72, 79.5, 80, 85, 90):
            cuts = es.cut_times(4, 8, bpm)
            for k, t in enumerate(cuts):
                exact = k * 4 * 60 / bpm
                self.assertLessEqual(abs(t - exact), 1 / 60 + 1e-9, (bpm, k))
                self.assertAlmostEqual(t * 30, round(t * 30), places=6)


class ProfileTest(unittest.TestCase):
    def test_default_when_missing(self):
        p = es.music_profile("does-not-exist")
        self.assertEqual(p["bpm"], 80.0)
        self.assertEqual(p["start_offset"], 0.0)
        self.assertEqual(p["intro_seconds"], 30.0)

    def test_limits(self):
        self.assertEqual(es.max_clip_seconds("veo"), 8.0)
        self.assertEqual(es.max_clip_seconds(""), 5.0)
        self.assertEqual(es.max_clip_seconds("unknown-tool"), 5.0)


if __name__ == "__main__":
    unittest.main()
