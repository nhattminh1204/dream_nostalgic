import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from tests import helpers
import episode_state as es


def shot(n, **kw):
    base = {"n": n, "angle": "wide", "scene_vi": f"cảnh {n}", "characters": [],
            "image_prompt": f"img {n}", "negative": "", "motion_prompt": f"mot {n}"}
    base.update(kw)
    return base


def make(tmp, shots, name="ep050", **top):
    d = Path(tmp) / name
    (d / "images").mkdir(parents=True)
    (d / "clips").mkdir()
    data = {"id": name, "status": "draft", "storyboard_approved": True, "beats_per_scene": 4,
            "music_profile": helpers.TEST_PROFILE, "shots": shots, **top}
    (d / "script.json").write_text(json.dumps(data), encoding="utf-8")
    return d


def touch(p, content=b"x"):
    p.write_bytes(content)


class PhaseTest(unittest.TestCase):
    def test_idea_and_storyboard(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make(tmp, [])
            self.assertEqual(es.phase(es.load(d), d), "idea")
            d2 = make(tmp, [shot(1)], name="ep051", storyboard_approved=False)
            self.assertEqual(es.phase(es.load(d2), d2), "storyboard")

    def test_images_then_video_then_clips_then_final(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make(tmp, [shot(1, image_prompt=""), shot(2)])
            s = es.load(d)
            self.assertEqual(es.phase(s, d), "image_prompts")
            s["shots"][0]["image_prompt"] = "p"
            self.assertEqual(es.phase(s, d), "images")

            touch(d / "images" / "s01.png")
            touch(d / "images" / "s02.png")
            es.lock_all(s, d)
            self.assertEqual(es.phase(s, d), "clips")  # đã có motion_prompt

            s["shots"][1]["motion_prompt"] = ""
            self.assertEqual(es.phase(s, d), "video_prompts")
            s["shots"][1]["motion_prompt"] = "m"

            touch(d / "clips" / "s01.mp4")
            touch(d / "clips" / "s02.mp4")
            self.assertEqual(es.phase(s, d), "final")
            touch(d / "final.mp4")
            self.assertEqual(es.phase(s, d), "final")
            s["status"] = "published"
            self.assertEqual(es.phase(s, d), "published")

    def test_final_without_locks_is_not_final(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make(tmp, [shot(1)])
            touch(d / "clips" / "s01.mp4")
            touch(d / "final.mp4")
            self.assertEqual(es.phase(es.load(d), d), "images")


class LockTest(unittest.TestCase):
    def test_lock_requires_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make(tmp, [shot(1)])
            s = es.load(d)
            with self.assertRaises(es.StateError):
                es.lock(s, d, 1)

    def test_lock_all_reports_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make(tmp, [shot(1), shot(2)])
            touch(d / "images" / "s01.png")
            s = es.load(d)
            with self.assertRaisesRegex(es.StateError, "2"):
                es.lock_all(s, d)

    def test_unlock_marks_neighbours_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make(tmp, [shot(1), shot(2), shot(3), shot(4)])
            s = es.load(d)
            es.unlock(s, 2)
            self.assertEqual([sh["motion_stale"] for sh in s["shots"]], [True, True, True, False])

    def test_replacing_locked_file_unlocks_on_sync(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make(tmp, [shot(1), shot(2)])
            img = d / "images" / "s01.png"
            touch(img, b"aaa")
            s = es.load(d)
            es.lock(s, d, 1)
            self.assertTrue(es.is_locked(d, s["shots"][0]))
            touch(img, b"bbbbbb")
            later = time.time() + 5
            os.utime(img, (later, later))
            self.assertFalse(es.is_locked(d, s["shots"][0]))
            self.assertTrue(es.sync(s, d))
            self.assertIsNone(s["shots"][0]["locked_image"])
            self.assertTrue(s["shots"][0]["motion_stale"])

    def test_next_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make(tmp, [shot(1, image_prompt="")])
            st = es.next_step(es.load(d), d)
            self.assertEqual(st["phase"], "image_prompts")
            self.assertEqual(st["by"], "ai")


if __name__ == "__main__":
    unittest.main()
