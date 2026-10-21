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
import math

from common import LIB, config, load_json

FPS = 30
HEAD_TRIM = 0.5
SLOWDOWN_LIMIT = 0.10
BEAT_CHOICES = (4, 6, 8)
MIN_SCENES = 5
DEFAULT_PROFILE = {"name": "Mặc định", "bpm": 80.0, "start_offset": 0.0, "intro_seconds": 30.0}


class StateError(Exception):
    """Lỗi người dùng cần biết (thông báo tiếng Việt)."""


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
