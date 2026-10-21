"""Bộ não dùng chung của quy trình /dream.

Giai đoạn của tập, lưới phách khớp nhạc, chốt ảnh, kiểm tra và ghi kết quả AI an toàn.
Dùng bởi agent Antigravity (qua dòng lệnh), Studio (tools/web.py) và tools/assemble.py.

  python tools/episode_state.py phase ep001
  python tools/episode_state.py plan ep001
  python tools/episode_state.py apply ep001 storyboard <file.json>
  python tools/episode_state.py approve ep001
  python tools/episode_state.py lock ep001 3        # hoặc: lock ep001 all
  python tools/episode_state.py unlock ep001 3
"""
import copy
import math
import time

from common import LIB, config, load_json, save_json

FPS = 30
HEAD_TRIM = 0.5
SLOWDOWN_LIMIT = 0.10
BEAT_CHOICES = (4, 6, 8)
MIN_SCENES = 5
DEFAULT_PROFILE = {"name": "Mặc định", "bpm": 80.0, "start_offset": 0.0, "intro_seconds": 30.0}


class StateError(Exception):
    """Lỗi người dùng cần biết (thông báo tiếng Việt)."""


class VersionConflict(StateError):
    """script.json đã bị nơi khác sửa trong lúc đang làm."""


# ---------- nhạc & lưới phách ----------
def music_profile(profile_id=None):
    path = LIB / "music-profiles.json"
    profiles = load_json(path) if path.exists() else {}
    pid = profile_id or config().get("music_profile", "")
    found = profiles.get(pid, {})
    return {**DEFAULT_PROFILE, **{k: found[k] for k in DEFAULT_PROFILE if k in found}}


def max_clip_seconds(video_tool):
    limits = load_json(LIB / "tool-guides" / "limits.json")
    return float(limits.get(video_tool or "generic", limits["generic"]))


def plan_shape(bpm, start_offset, intro_seconds, scene_target, video_range, max_clip):
    b = 60.0 / bpm
    warnings = []
    fitting = [k for k in BEAT_CHOICES if k * b <= max_clip - HEAD_TRIM + 1e-9]
    if not fitting:
        fitting = [BEAT_CHOICES[0]]
        warnings.append(f"Cảnh ngắn nhất ({BEAT_CHOICES[0]} phách = {BEAT_CHOICES[0] * b:.2f}s) "
                        f"vẫn dài hơn clip tối đa {max_clip:g}s của app video.")
    bps = min(fitting, key=lambda k: (abs(k * b - scene_target), k))
    scene_s = bps * b
    limit = min(video_range[1], intro_seconds - start_offset)
    max_n = max(int(math.floor(limit / scene_s + 1e-9)), 0)
    aligned = [n for n in range(max_n, MIN_SCENES - 1, -1) if (n * bps) % 4 == 0]
    if aligned:
        n, bar_aligned = aligned[0], True
    elif max_n >= MIN_SCENES:
        n, bar_aligned = max_n, False
        warnings.append("Không chia được vừa đủ cảnh vừa đúng ô nhịp: video kết thúc giữa ô nhịp.")
    else:
        n, bar_aligned = MIN_SCENES, (MIN_SCENES * bps) % 4 == 0
        warnings.append(f"Đoạn intro dùng được ({limit:.1f}s) ngắn hơn {MIN_SCENES} cảnh: video sẽ dài hơn intro.")
    total = n * scene_s
    if total + 1e-9 < video_range[0] and not warnings:
        warnings.append(f"Tổng {total:.1f}s ngắn hơn mục tiêu {video_range[0]:g}s.")
    return {"beats_per_scene": bps, "scenes": n, "scene_seconds": round(scene_s, 6),
            "total_seconds": round(total, 6), "bar_aligned": bar_aligned, "warnings": warnings}


def cut_times(beats_per_scene, scenes, bpm, fps=FPS):
    step = beats_per_scene * 60.0 / bpm
    return [round(k * step * fps) / fps for k in range(scenes + 1)]


# ---------- load / migrate / save ----------
SHOT_DEFAULTS = {"angle": "medium", "scene_vi": "", "characters": [], "image_prompt": "", "negative": "",
                 "locked_image": None, "locked_sig": None, "motion_prompt": "", "motion_stale": False, "edited": []}


def plan_for(s):
    cfg = config()
    prof = music_profile(s.get("music_profile"))
    return plan_shape(prof["bpm"], prof["start_offset"], prof["intro_seconds"],
                      float(cfg.get("scene_seconds_target", 3.5)),
                      tuple(cfg.get("video_seconds_target", [15, 20])),
                      max_clip_seconds(s.get("video_tool") or cfg.get("video_tool")))


def migrate(s):
    s = copy.deepcopy(s)
    s.setdefault("version", 1)
    s.setdefault("storyboard_approved", bool(s.get("shots")))
    s.setdefault("music_profile", config().get("music_profile", ""))
    s.setdefault("concept", {}).setdefault("custom_idea", "")
    shots = []
    for sh in sorted(s.get("shots", []), key=lambda x: x["n"]):
        clean = {k: v for k, v in sh.items() if k not in ("dur", "role")}
        for k, v in SHOT_DEFAULTS.items():
            clean.setdefault(k, copy.deepcopy(v))
        shots.append(clean)
    s["shots"] = shots
    if shots and not s.get("beats_per_scene"):
        s["beats_per_scene"] = plan_for(s)["beats_per_scene"]
    s.setdefault("beats_per_scene", None)
    return s


def load(ep_dir):
    path = ep_dir / "script.json"
    if not path.exists():
        raise StateError(f"Không tìm thấy {path}")
    return migrate(load_json(path))


def save(ep_dir, s, expected_version):
    path = ep_dir / "script.json"
    current = load_json(path) if path.exists() else {}
    if current.get("version", 1) != expected_version:
        raise VersionConflict(f"{ep_dir.name} vừa được cập nhật ở nơi khác. Hãy tải lại rồi làm lại.")
    if current:
        hist = ep_dir / ".history"
        hist.mkdir(exist_ok=True)
        save_json(hist / f"{time.strftime('%Y%m%d-%H%M%S')}-v{expected_version}.json", current)
    out = copy.deepcopy(s)
    out["version"] = expected_version + 1
    save_json(path, out)
    return out


def shot_seconds(s):
    if not s["shots"]:
        return []
    bpm = music_profile(s.get("music_profile"))["bpm"]
    cuts = cut_times(s["beats_per_scene"], len(s["shots"]), bpm)
    return [round(cuts[i + 1] - cuts[i], 6) for i in range(len(s["shots"]))]
