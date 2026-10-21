import json
import tempfile
import unittest
from pathlib import Path

from tests import helpers
import new_episode
import web


class BuildScriptTest(unittest.TestCase):
    def test_new_fields(self):
        s = new_episode.build_script("ep001", {"id": "night-shift", "palette": "night-shift", "characters": ["ong-moon"]},
                                     "polish", "moon", "rooftop", "night", "T", "L", "ông Moon sửa đồng hồ",
                                     {"music_profile": "faded-intro", "video_tool": ""})
        self.assertEqual(s["version"], 1)
        self.assertFalse(s["storyboard_approved"])
        self.assertEqual(s["music_profile"], "faded-intro")
        self.assertIsNone(s["beats_per_scene"])
        self.assertEqual(s["concept"]["custom_idea"], "ông Moon sửa đồng hồ")
        self.assertEqual(s["video_tool"], "generic")


class WebSummaryTest(unittest.TestCase):
    def test_old_script_gets_dur_and_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "ep070"
            (d / "images").mkdir(parents=True)
            (d / "clips").mkdir()
            (d / "images" / "s01.png").write_bytes(b"x")
            (d / "script.json").write_text(json.dumps({
                "id": "ep070", "series": "night-shift", "palette": "night-shift",
                "music_profile": helpers.TEST_PROFILE, "beats_per_scene": 4, "status": "draft", "title": "t",
                "concept": {"logline_vi": "l"},
                "shots": [{"n": 1, "role": "hook", "dur": 6, "angle": "low", "scene_vi": "a",
                           "image_prompt": "p", "motion_prompt": "m"}]}), encoding="utf-8")
            out = web.episode_summary(d, full=True)
            sh = out["shots"][0]
            self.assertEqual(sh["dur"], 3.0)
            self.assertEqual(sh["role"], "4 phách")
            self.assertTrue(sh["image"].endswith("images/s01.png"))
            self.assertIsNone(sh["clip"])


if __name__ == "__main__":
    unittest.main()
