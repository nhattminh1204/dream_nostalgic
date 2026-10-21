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
import argparse
import copy
import json
import math
import sys
import time
from pathlib import Path

from common import EPISODES, LIB, config, load_json, save_json

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


# ---------- file & chốt ảnh ----------
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
CLIP_EXTS = (".mp4", ".mov", ".webm", ".mkv")
PHASES = ("idea", "storyboard", "image_prompts", "images", "video_prompts", "clips", "final", "published")


def _find(folder, n, exts):
    for ext in exts:
        p = folder / f"s{n:02d}{ext}"
        if p.exists():
            return p
    return None


def find_image(ep_dir, n):
    return _find(ep_dir / "images", n, IMAGE_EXTS)


def find_clip(ep_dir, n):
    return _find(ep_dir / "clips", n, CLIP_EXTS)


def file_sig(p):
    st = p.stat()
    return f"{st.st_size}:{int(st.st_mtime)}"


def _shot(s, n):
    for sh in s["shots"]:
        if sh["n"] == n:
            return sh
    raise StateError(f"Không có cảnh {n}.")


def is_locked(ep_dir, sh):
    rel = sh.get("locked_image")
    if not rel:
        return False
    p = ep_dir / rel
    return p.exists() and sh.get("locked_sig") == file_sig(p)


def _mark_stale(s, n):
    for m in (n - 1, n, n + 1):
        for sh in s["shots"]:
            if sh["n"] == m and sh["motion_prompt"]:
                sh["motion_stale"] = True


def lock(s, ep_dir, n):
    sh = _shot(s, n)
    img = find_image(ep_dir, n)
    if not img:
        raise StateError(f"Cảnh {n} chưa có ảnh để chốt.")
    sh["locked_image"] = img.relative_to(ep_dir).as_posix()
    sh["locked_sig"] = file_sig(img)
    return s


def lock_all(s, ep_dir):
    missing = [sh["n"] for sh in s["shots"] if not find_image(ep_dir, sh["n"])]
    if missing:
        raise StateError("Chưa có ảnh cho cảnh: " + ", ".join(map(str, missing)))
    for sh in s["shots"]:
        lock(s, ep_dir, sh["n"])
    return s


def unlock(s, n):
    sh = _shot(s, n)
    sh["locked_image"] = None
    sh["locked_sig"] = None
    _mark_stale(s, n)
    return s


def sync(s, ep_dir):
    changed = False
    for sh in s["shots"]:
        if sh["locked_image"] and not is_locked(ep_dir, sh):
            unlock(s, sh["n"])
            changed = True
    return changed


# ---------- giai đoạn ----------
def phase(s, ep_dir):
    shots = s["shots"]
    if not shots:
        return "idea"
    if not s.get("storyboard_approved"):
        return "storyboard"
    if any(not sh["image_prompt"] for sh in shots):
        return "image_prompts"
    if any(not is_locked(ep_dir, sh) for sh in shots):
        return "images"
    if any(not sh["motion_prompt"] or sh["motion_stale"] for sh in shots):
        return "video_prompts"
    if any(not find_clip(ep_dir, sh["n"]) for sh in shots):
        return "clips"
    if s.get("status") == "published" and (ep_dir / "final.mp4").exists():
        return "published"
    return "final"


def next_step(s, ep_dir):
    ph = phase(s, ep_dir)
    shots = s["shots"]
    if ph == "images":
        todo = [sh["n"] for sh in shots if not is_locked(ep_dir, sh)]
        msg = "Tạo, thả và chốt ảnh cảnh: " + ", ".join(map(str, todo))
    elif ph == "clips":
        todo = [sh["n"] for sh in shots if not find_clip(ep_dir, sh["n"])]
        msg = "Tạo và thả clip cảnh: " + ", ".join(map(str, todo))
    elif ph == "final":
        msg = ("Đã có video: điền thông tin và đăng." if (ep_dir / "final.mp4").exists()
               else "Dựng video (Studio hoặc python tools/assemble.py), hoặc ghép nơi khác rồi tải final.mp4 lên.")
    else:
        msg = {
            "idea": "Viết phân cảnh.",
            "storyboard": "Duyệt hoặc sửa bảng phân cảnh.",
            "image_prompts": "Viết prompt ảnh.",
            "video_prompts": "Viết prompt video dựa trên ảnh đã chốt.",
            "published": "Hoàn tất.",
        }[ph]
    by = {"idea": "ai", "storyboard": "user", "image_prompts": "ai", "images": "user",
          "video_prompts": "ai", "clips": "user", "final": "user", "published": "done"}[ph]
    return {"phase": ph, "by": by, "message": msg}


# ---------- kiểm tra & ghi kết quả AI ----------
KINDS = ("storyboard", "image_prompts", "video_prompts", "seo")


def _known_characters():
    return {p.stem for p in (LIB / "characters").glob("*.md")}


def _known_angles():
    return {a["id"] for a in load_json(LIB / "materials.json")["angles"]}


def _hashtags(tags):
    return ["#" + t.strip().lstrip("#") for t in tags if t.strip().lstrip("#")]


def validate(s, kind, data):
    if kind not in KINDS:
        return {}, [f"Loại kết quả không hợp lệ: {kind}"], []
    errors, warnings = [], []
    if kind == "storyboard":
        expected = plan_for(s)["scenes"]
        shots = data.get("shots") or []
        if len(shots) != expected:
            errors.append(f"Cần đúng {expected} cảnh, AI trả {len(shots)} cảnh.")
        chars, angles = _known_characters(), _known_angles()
        clean = []
        for i, sh in enumerate(shots, 1):
            angle = sh.get("angle", "")
            if angle not in angles:
                warnings.append(f"Cảnh {i}: góc máy '{angle}' không có, đổi thành 'medium'.")
                angle = "medium"
            unknown = [c for c in sh.get("characters", []) if c not in chars]
            if unknown:
                warnings.append(f"Cảnh {i}: bỏ nhân vật không tồn tại: {', '.join(unknown)}.")
            scene = (sh.get("scene_vi") or "").strip()
            if not scene:
                errors.append(f"Cảnh {i}: thiếu mô tả cảnh (scene_vi).")
            clean.append({"n": i, "angle": angle, "scene_vi": scene,
                          "characters": [c for c in sh.get("characters", []) if c in chars]})
        out = {"shots": clean}
        for k in ("title", "description"):
            if k in data:
                out[k] = str(data[k]).strip()
        if "hashtags" in data:
            out["hashtags"] = _hashtags(data["hashtags"])
        return out, errors, warnings
    if kind == "seo":
        title = str(data.get("title", "")).strip()
        if not title:
            errors.append("Thiếu tiêu đề.")
        if len(title) > 100:
            errors.append("Tiêu đề quá 100 ký tự.")
        return {"title": title, "description": str(data.get("description", "")).strip(),
                "hashtags": _hashtags(data.get("hashtags", []))}, errors, warnings
    field = "image_prompt" if kind == "image_prompts" else "motion_prompt"
    existing = {sh["n"] for sh in s["shots"]}
    clean = []
    for item in data.get("shots") or []:
        n = item.get("n")
        if n not in existing:
            errors.append(f"Không có cảnh {n}.")
            continue
        text = str(item.get(field, "")).strip()
        if not text:
            errors.append(f"Cảnh {n}: {field} rỗng.")
            continue
        row = {"n": n, field: text}
        if kind == "image_prompts":
            row["negative"] = str(item.get("negative", "")).strip()
        clean.append(row)
    if not clean and not errors:
        errors.append("Không có cảnh nào trong kết quả.")
    return {"shots": clean}, errors, warnings


def apply(s, kind, data, overwrite_edited=False):
    clean, errors, warnings = validate(s, kind, data)
    if errors:
        raise StateError("\n".join(errors))
    if kind == "storyboard":
        plan = plan_for(s)
        old = {sh["n"]: sh for sh in s["shots"]}
        keep_old = bool(s.get("storyboard_approved")) and len(old) == len(clean["shots"])
        new_shots = []
        for sh in clean["shots"]:
            prev = old.get(sh["n"]) if keep_old else None
            same = prev is not None and all(prev[k] == sh[k] for k in ("angle", "scene_vi", "characters"))
            base = copy.deepcopy(prev) if same else {**copy.deepcopy(SHOT_DEFAULTS), "n": sh["n"]}
            base.update(sh)
            new_shots.append(base)
        s["shots"] = new_shots
        s["beats_per_scene"] = plan["beats_per_scene"]
        if not keep_old:
            s["storyboard_approved"] = False
        warnings += plan["warnings"]
        for k in ("title", "description", "hashtags"):
            if k in clean:
                s[k] = clean[k]
        return warnings
    if kind == "seo":
        s.update(clean)
        return warnings
    field = "image_prompt" if kind == "image_prompts" else "motion_prompt"
    for row in clean["shots"]:
        sh = _shot(s, row["n"])
        if field in sh["edited"] and not overwrite_edited:
            warnings.append(f"Cảnh {row['n']}: giữ {field} bạn đã sửa tay.")
            continue
        sh[field] = row[field]
        if field in sh["edited"]:
            sh["edited"].remove(field)
        if kind == "image_prompts":
            sh["negative"] = row["negative"]
        else:
            sh["motion_stale"] = False
    return warnings


def approve(s):
    if not s["shots"]:
        raise StateError("Chưa có phân cảnh để duyệt.")
    s["storyboard_approved"] = True
    return s


# ---------- dòng lệnh (cho agent Antigravity) ----------
def _ep_dir(arg):
    p = Path(arg)
    d = p if (p / "script.json").exists() else EPISODES / arg
    if not (d / "script.json").exists():
        raise StateError(f"Không tìm thấy tập {arg}")
    return d


def _print(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Trạng thái tập Dreamnostalgic")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("phase", "plan", "show", "approve"):
        sub.add_parser(name).add_argument("ep")
    a = sub.add_parser("apply")
    a.add_argument("ep")
    a.add_argument("kind", choices=KINDS)
    a.add_argument("file")
    a.add_argument("--overwrite-edited", action="store_true")
    lk = sub.add_parser("lock")
    lk.add_argument("ep")
    lk.add_argument("n")
    ul = sub.add_parser("unlock")
    ul.add_argument("ep")
    ul.add_argument("n", type=int)
    args = ap.parse_args(argv)

    try:
        d = _ep_dir(args.ep)
        s = load(d)
        v = s["version"]
        if args.cmd == "phase":
            if sync(s, d):
                s = save(d, s, v)
            _print(next_step(s, d))
        elif args.cmd == "plan":
            plan = plan_for(s)
            bpm = music_profile(s.get("music_profile"))["bpm"]
            n = len(s["shots"]) or plan["scenes"]
            bps = s["beats_per_scene"] or plan["beats_per_scene"]
            _print({**plan, "scenes": n, "beats_per_scene": bps, "cuts": cut_times(bps, n, bpm),
                    "max_clip": max_clip_seconds(s.get("video_tool") or config().get("video_tool"))})
        elif args.cmd == "show":
            _print(s)
        elif args.cmd == "approve":
            save(d, approve(s), v)
            print("Đã duyệt phân cảnh.")
        elif args.cmd == "apply":
            data = json.loads(Path(args.file).read_text(encoding="utf-8"))
            warnings = apply(s, args.kind, data, args.overwrite_edited)
            save(d, s, v)
            print(f"Đã ghi {args.kind} vào {d.name}.")
            for w in warnings:
                print("Lưu ý:", w)
        elif args.cmd == "lock":
            save(d, lock_all(s, d) if args.n == "all" else lock(s, d, int(args.n)), v)
            print("Đã chốt ảnh.")
        elif args.cmd == "unlock":
            save(d, unlock(s, args.n), v)
            print(f"Đã bỏ chốt cảnh {args.n}.")
    except StateError as e:
        sys.exit(f"Lỗi: {e}")


if __name__ == "__main__":
    main()
