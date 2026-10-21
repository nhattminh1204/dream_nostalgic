import json
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path

from tests import helpers
import assemble
from common import ffmpeg_exe, probe

COLORS = ["red", "green", "blue"] * 2


def make_clip(path, color, seconds, size="720x1280"):
    subprocess.run([ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                    "-i", f"color=c={color}:size={size}:rate=24:duration={seconds}",
                    "-pix_fmt", "yuv420p", str(path)], check=True)


def make_ep(tmp, durations):
    d = Path(tmp) / "ep080"
    (d / "clips").mkdir(parents=True)
    (d / "images").mkdir()
    shots = []
    for i, (color, dur) in enumerate(zip(COLORS, durations), 1):
        make_clip(d / "clips" / f"s{i:02d}.mp4", color, dur, "1280x720" if i == 2 else "720x1280")
        shots.append({"n": i, "angle": "wide", "scene_vi": "x", "image_prompt": "p", "motion_prompt": "m"})
    (d / "script.json").write_text(json.dumps({
        "id": "ep080", "palette": "cotton-morning", "music_profile": helpers.TEST_PROFILE, "beats_per_scene": 4,
        "storyboard_approved": True, "shots": shots}), encoding="utf-8")
    return d


def dominant(video, t):
    raw = subprocess.run([ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(video),
                          "-frames:v", "1", "-vf", "scale=1:1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return ["red", "green", "blue"][max(range(3), key=lambda c: raw[c])]


class BuildTest(unittest.TestCase):
    def test_cuts_land_on_beat_grid(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_ep(tmp, [5] * 6)
            out = assemble.build(d, preview=True)
            dur, has_audio = probe(out)
            self.assertAlmostEqual(dur, 18.0, delta=1 / 30 + 0.02)
            self.assertFalse(has_audio)
            for k in range(1, 6):  # điểm cắt 3,6,9,12,15 giây
                t = 3.0 * k
                self.assertEqual(dominant(out, t - 0.1), COLORS[k - 1], (k, "trước"))
                self.assertEqual(dominant(out, t + 0.1), COLORS[k], (k, "sau"))

    def test_short_clip_slowed_within_10_percent(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_ep(tmp, [5, 2.8, 5, 5, 5, 5])
            out = assemble.build(d, preview=True)
            self.assertAlmostEqual(probe(out)[0], 18.0, delta=1 / 30 + 0.02)

    def test_too_short_clip_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_ep(tmp, [5, 2.0, 5, 5, 5, 5])
            with self.assertRaisesRegex(assemble.AssembleError, "s02"):
                assemble.build(d, preview=True)

    def test_missing_clip_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_ep(tmp, [5] * 6)
            (d / "clips" / "s04.mp4").unlink()
            with self.assertRaisesRegex(assemble.AssembleError, "s04"):
                assemble.build(d, preview=True)

    def test_metronome_track(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_ep(tmp, [5] * 6)
            out = assemble.build(d, preview=True, metronome=True)
            self.assertTrue(probe(out)[1])


class MetronomeTest(unittest.TestCase):
    def test_clicks_on_beats(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "m.wav"
            assemble.write_metronome(p, 80, 3.0, rate=8000)
            with wave.open(str(p)) as w:
                self.assertEqual(w.getnframes(), 24000)
                frames = w.readframes(w.getnframes())
            samples = [int.from_bytes(frames[i:i + 2], "little", signed=True) for i in range(0, len(frames), 2)]
            beat = int(0.75 * 8000)
            for k in range(4):
                window = samples[k * beat: k * beat + 300]
                self.assertGreater(max(abs(v) for v in window), 3000, k)
            mid = samples[beat // 2: beat // 2 + 300]
            self.assertEqual(max(abs(v) for v in mid), 0)


if __name__ == "__main__":
    unittest.main()
