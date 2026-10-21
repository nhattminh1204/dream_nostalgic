"""Shared helpers for Dreamnostalgic tools."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "library"
EPISODES = ROOT / "episodes"
LOG = LIB / "episode-log.md"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def config():
    return load_json(ROOT / "config.json")


def by_id(items):
    return {i["id"]: i for i in items}


def episode_dir(ep_id):
    d = EPISODES / ep_id
    if not (d / "script.json").exists():
        sys.exit(f"Không tìm thấy {d / 'script.json'}")
    return d


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("Cần ffmpeg: cài ffmpeg vào PATH hoặc chạy `pip install -r tools/requirements.txt`.")


def probe(path):
    """Return (duration_seconds, has_audio) using ffmpeg's stderr banner."""
    info = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(path)],
                          capture_output=True, text=True, errors="ignore").stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info)
    dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0
    return dur, "Audio:" in info
