import json
import tempfile
import unittest
from pathlib import Path

from tests import helpers
import episode_state as es

OLD = {
    "id": "ep009", "series": "night-shift", "palette": "night-shift", "characters": ["ong-moon"],
    "concept": {"logline_vi": "x"}, "title": "t", "status": "draft", "video_tool": "generic",
    "music_profile": helpers.TEST_PROFILE,
    "shots": [
        {"n": 1, "role": "hook", "angle": "low", "dur": 6, "scene_vi": "a", "characters": ["ong-moon"],
         "image_prompt": "p1", "motion_prompt": "m1", "negative": "n1"},
        {"n": 2, "role": "process", "angle": "medium", "dur": 5, "scene_vi": "b", "characters": [],
         "image_prompt": "p2", "motion_prompt": "m2", "negative": ""},
    ],
}


def make_ep(tmp, data):
    d = Path(tmp) / data["id"]
    (d / "images").mkdir(parents=True)
    (d / "clips").mkdir()
    (d / "script.json").write_text(json.dumps(data), encoding="utf-8")
    return d


class MigrateTest(unittest.TestCase):
    def test_old_fields_removed_and_defaults_added(self):
        s = es.migrate(OLD)
        self.assertEqual(s["version"], 1)
        self.assertTrue(s["storyboard_approved"])
        self.assertEqual(s["beats_per_scene"], 4)
        self.assertEqual(s["concept"]["custom_idea"], "")
        for sh in s["shots"]:
            self.assertNotIn("dur", sh)
            self.assertNotIn("role", sh)
            self.assertIsNone(sh["locked_image"])
            self.assertFalse(sh["motion_stale"])
            self.assertEqual(sh["edited"], [])
        self.assertIn("dur", OLD["shots"][0])  # đầu vào không bị sửa

    def test_empty_episode(self):
        s = es.migrate({"id": "ep010", "shots": []})
        self.assertFalse(s["storyboard_approved"])
        self.assertIsNone(s["beats_per_scene"])


class SaveTest(unittest.TestCase):
    def test_save_increments_version_and_keeps_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_ep(tmp, OLD)
            s = es.load(d)
            s["title"] = "new"
            saved = es.save(d, s, s["version"])
            self.assertEqual(saved["version"], 2)
            self.assertEqual(json.loads((d / "script.json").read_text(encoding="utf-8"))["title"], "new")
            self.assertEqual(len(list((d / ".history").glob("*.json"))), 1)

    def test_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_ep(tmp, OLD)
            a = es.load(d)
            b = es.load(d)
            es.save(d, a, a["version"])
            with self.assertRaises(es.VersionConflict):
                es.save(d, b, b["version"])

    def test_missing_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(es.StateError):
                es.load(Path(tmp))

    def test_shot_seconds(self):
        s = es.migrate(OLD)
        self.assertEqual(es.shot_seconds(s), [3.0, 3.0])


if __name__ == "__main__":
    unittest.main()
