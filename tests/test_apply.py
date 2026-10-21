import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests import helpers
import episode_state as es

BASE = {"id": "x", "music_profile": helpers.TEST_PROFILE, "video_tool": "generic", "shots": []}
N = es.plan_for(BASE)["scenes"]


def board(n=N, **over):
    shots = [{"angle": "wide", "scene_vi": f"cảnh {i}", "characters": ["ong-moon"]} for i in range(1, n + 1)]
    data = {"shots": shots, "title": "POV: polishing the moon 🌙", "description": "d", "hashtags": ["moon", "#cozy"]}
    data.update(over)
    return data


def fresh():
    return es.migrate(BASE)


def new_ep(tmp):
    d = Path(tmp) / "ep060"
    (d / "images").mkdir(parents=True)
    (d / "clips").mkdir()
    (d / "script.json").write_text(json.dumps({**BASE, "id": "ep060"}), encoding="utf-8")
    return d


class StoryboardTest(unittest.TestCase):
    def test_apply_storyboard(self):
        s = fresh()
        warns = es.apply(s, "storyboard", board())
        self.assertEqual(len(s["shots"]), N)
        self.assertEqual([sh["n"] for sh in s["shots"]], list(range(1, N + 1)))
        self.assertEqual(s["beats_per_scene"], 4)
        self.assertFalse(s["storyboard_approved"])
        self.assertEqual(s["hashtags"], ["#moon", "#cozy"])
        self.assertEqual(warns, [])

    def test_wrong_count_is_error(self):
        with self.assertRaisesRegex(es.StateError, "cảnh"):
            es.apply(fresh(), "storyboard", board(n=N + 2))

    def test_unknown_character_and_angle_are_fixed_with_warning(self):
        s = fresh()
        data = board()
        data["shots"][0]["characters"] = ["ong-moon", "mickey"]
        data["shots"][0]["angle"] = "dutch"
        warns = es.apply(s, "storyboard", data)
        self.assertEqual(s["shots"][0]["characters"], ["ong-moon"])
        self.assertEqual(s["shots"][0]["angle"], "medium")
        self.assertEqual(len(warns), 2)

    def test_edit_after_approval_resets_only_changed_shots(self):
        s = fresh()
        es.apply(s, "storyboard", board())
        es.approve(s)
        for sh in s["shots"]:
            sh["image_prompt"], sh["motion_prompt"] = "p", "m"
        data = board()
        data["shots"][1]["scene_vi"] = "cảnh mới"
        es.apply(s, "storyboard", data)
        self.assertTrue(s["storyboard_approved"])
        self.assertEqual(s["shots"][1]["image_prompt"], "")
        self.assertEqual(s["shots"][1]["motion_prompt"], "")
        self.assertEqual(s["shots"][0]["image_prompt"], "p")


class PromptsTest(unittest.TestCase):
    def setUp(self):
        self.s = fresh()
        es.apply(self.s, "storyboard", board())
        es.approve(self.s)

    def test_image_prompts_respect_edited(self):
        self.s["shots"][0]["image_prompt"] = "mine"
        self.s["shots"][0]["edited"] = ["image_prompt"]
        data = {"shots": [{"n": i, "image_prompt": f"ai {i}", "negative": "text"} for i in range(1, N + 1)]}
        warns = es.apply(self.s, "image_prompts", data)
        self.assertEqual(self.s["shots"][0]["image_prompt"], "mine")
        self.assertEqual(self.s["shots"][1]["image_prompt"], "ai 2")
        self.assertTrue(any("1" in w for w in warns))
        es.apply(self.s, "image_prompts", data, overwrite_edited=True)
        self.assertEqual(self.s["shots"][0]["image_prompt"], "ai 1")
        self.assertEqual(self.s["shots"][0]["edited"], [])

    def test_video_prompts_clear_stale(self):
        self.s["shots"][2]["motion_stale"] = True
        es.apply(self.s, "video_prompts", {"shots": [{"n": 3, "motion_prompt": "slow push-in"}]})
        self.assertEqual(self.s["shots"][2]["motion_prompt"], "slow push-in")
        self.assertFalse(self.s["shots"][2]["motion_stale"])

    def test_unknown_shot_is_error(self):
        with self.assertRaises(es.StateError):
            es.apply(self.s, "video_prompts", {"shots": [{"n": 99, "motion_prompt": "x"}]})

    def test_empty_prompt_is_error(self):
        with self.assertRaises(es.StateError):
            es.apply(self.s, "image_prompts", {"shots": [{"n": 1, "image_prompt": "  ", "negative": ""}]})

    def test_seo(self):
        es.apply(self.s, "seo", {"title": "New ✨", "description": "x", "hashtags": ["a"]})
        self.assertEqual(self.s["title"], "New ✨")
        self.assertEqual(self.s["hashtags"], ["#a"])


class CliTest(unittest.TestCase):
    def run_cli(self, *args, cwd):
        r = subprocess.run([sys.executable, str(helpers.TOOLS / "episode_state.py"), *args],
                           capture_output=True, text=True, encoding="utf-8", cwd=cwd)
        return r.returncode, r.stdout + r.stderr

    def test_apply_approve_phase_via_ep_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = new_ep(tmp)
            f = Path(tmp) / "out.json"
            f.write_text(json.dumps(board()), encoding="utf-8")
            code, out = self.run_cli("apply", str(d), "storyboard", str(f), cwd=tmp)
            self.assertEqual(code, 0, out)
            code, out = self.run_cli("phase", str(d), cwd=tmp)
            self.assertEqual(json.loads(out)["phase"], "storyboard")
            self.run_cli("approve", str(d), cwd=tmp)
            code, out = self.run_cli("phase", str(d), cwd=tmp)
            self.assertEqual(json.loads(out)["phase"], "image_prompts")
            self.assertEqual(json.loads((d / "script.json").read_text(encoding="utf-8"))["version"], 3)

    def test_bad_input_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = new_ep(tmp)
            f = Path(tmp) / "bad.json"
            f.write_text(json.dumps(board(n=1)), encoding="utf-8")
            code, out = self.run_cli("apply", str(d), "storyboard", str(f), cwd=tmp)
            self.assertNotEqual(code, 0)
            self.assertIn("Lỗi", out)


if __name__ == "__main__":
    unittest.main()
