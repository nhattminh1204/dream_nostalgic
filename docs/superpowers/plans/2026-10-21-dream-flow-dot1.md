# Quy trình `/dream` – Đợt 1 (Nền tảng) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây bộ não dùng chung (`tools/episode_state.py`) cho quy trình `/dream`: suy ra giai đoạn, lưới phách khớp nhạc, chốt ảnh, kiểm tra và ghi kết quả AI an toàn; dựng video hard cut theo lưới phách có tiếng gõ nhịp; skill `/dream` cho Antigravity; Studio hiện tại không bị hỏng.

**Architecture:** Mọi logic trạng thái nằm trong `tools/episode_state.py` (hàm thuần + CLI). `assemble.py`, `export_prompts.py`, `web.py` và agent Antigravity đều gọi module này. Dữ liệu tập vẫn là `episodes/epNNN/script.json`, có `version` để chặn ghi đè và `.history/` để khôi phục. Hướng dẫn sáng tạo tách ra `library/guides/` để cả agent lẫn (sau này) Studio dùng chung.

**Tech Stack:** Python 3.10+ (máy người dùng: 3.14), chỉ thư viện chuẩn + `imageio-ffmpeg` (đã có); ffmpeg; `unittest` (không thêm pytest).

**Spec:** `docs/superpowers/specs/2026-10-21-dream-flow-design.md`

## Global Constraints

- Không thêm thư viện Python mới ngoài `imageio-ffmpeg`.
- Chỉ **hard cut**; không có chuyển cảnh khác.
- Mỗi cảnh **bắt buộc** có ảnh đã chốt **và** clip; không có đường tắt.
- Mọi cảnh dài **bằng nhau**: `beats_per_scene` ∈ {4, 6, 8}, chọn gần `scene_seconds_target` = 3.5 nhất, không vượt `max_clip − 0.5`.
- Video mục tiêu `[15, 20]` giây, tối thiểu **5** cảnh, ưu tiên tổng số phách là bội của 4.
- Điểm cắt `t_k = k × beats_per_scene × 60 / bpm`, làm tròn **từng điểm** về 1/30 giây (FPS = 30).
- Bỏ 0,5 giây đầu mỗi clip (`HEAD_TRIM = 0.5`); clip thiếu ≤ 10% thì làm chậm, thiếu hơn thì báo lỗi.
- Bản cuối **không có nhạc** (trừ khi người dùng truyền `--music` với file có quyền dùng).
- Hồ sơ nhạc mặc định: `bpm 80.0`, `start_offset 0.0`, `intro_seconds 30.0`.
- Thông báo cho người dùng bằng **tiếng Việt**; prompt cho AI bằng **tiếng Anh**.
- `Video/` là tư liệu tham khảo: không đọc/sửa/dùng làm chất liệu.
- Chạy kiểm thử từ thư mục gốc dự án: `python -m unittest discover -s tests -v`.

## File Structure

| File | Trạng thái | Trách nhiệm |
|---|---|---|
| `tools/episode_state.py` | Create | Bộ não: nhạc & lưới phách, load/migrate/save có version, giai đoạn, chốt ảnh, validate/apply kết quả AI, CLI |
| `library/music-profiles.json` | Create | Hồ sơ nhạc (`faded-intro`) |
| `library/tool-guides/limits.json` | Create | Độ dài clip tối đa theo app video |
| `config.json` | Modify | Thêm `music_profile`, `scene_seconds_target`, `video_seconds_target` |
| `tools/assemble.py` | Rewrite | Dựng theo lưới phách, trim đầu, làm chậm ≤10%, tiếng gõ nhịp |
| `tools/new_episode.py` | Modify | Khung script mới (version, storyboard_approved, music_profile, custom_idea) |
| `tools/export_prompts.py` | Modify | Dùng số giây tính từ lưới phách, bỏ `role`/`dur` |
| `tools/web.py` | Modify | Dùng `episode_state` (migrate + `dur` tính sẵn) để Studio cũ không hỏng |
| `tools/flip.py` | Modify | Import `find_clip` từ `episode_state` |
| `library/guides/*.md` | Create | Hướng dẫn sáng tạo: storyboard, image-prompts, video-prompts, seo |
| `.agent/skills/dream/SKILL.md` | Create | Điều phối `/dream` |
| `.agent/workflows/dream.md` | Create | Lệnh `/dream` |
| `.agent/workflows/new-episode.md`, `weekly-batch.md` | Modify | Trỏ về `/dream` |
| `.agent/skills/episode-script/` | Delete | Thay bằng `dream` + guides |
| `.agent/skills/prompt-writer/SKILL.md`, `seo-metadata/SKILL.md` | Modify | Trỏ tới guides |
| `.agent/rules/dreamnostalgic.md`, `README.md` | Modify | Cập nhật quy trình mới |
| `tests/__init__.py`, `tests/helpers.py`, `tests/test_*.py` | Create | Kiểm thử |

---

### Task 0: Khởi tạo git (cần người dùng đồng ý)

Thư mục dự án chưa là git repo. Các bước "Commit" trong kế hoạch cần git. **Hỏi người dùng trước khi chạy.** Nếu người dùng từ chối: bỏ qua mọi bước Commit.

- [ ] **Step 1: Hỏi người dùng** có đồng ý `git init` trong `E:\Youtube\Dreamnostalgic` không (để lưu lịch sử thay đổi, khôi phục khi lỗi).

- [ ] **Step 2: Nếu đồng ý, tạo `.gitignore` và commit đầu**

`.gitignore`:
```
Video/
episodes/*/images/
episodes/*/clips/
episodes/*/*.mp4
episodes/*/.history/
episodes/*/.metronome.wav
__pycache__/
.claude/
```

```bash
git init
git add .gitignore README.md config.json library tools web .agent docs Mo-Studio.bat
git commit -m "chore: snapshot before dream flow"
```

---

### Task 1: Hồ sơ nhạc, giới hạn clip và lưới phách

**Files:**
- Create: `library/music-profiles.json`, `library/tool-guides/limits.json`, `tools/episode_state.py`, `tests/__init__.py`, `tests/helpers.py`, `tests/test_beat_grid.py`
- Modify: `config.json`

**Interfaces:**
- Produces:
  - `episode_state.FPS = 30`, `HEAD_TRIM = 0.5`, `SLOWDOWN_LIMIT = 0.10`, `BEAT_CHOICES = (4, 6, 8)`, `MIN_SCENES = 5`
  - `class StateError(Exception)`
  - `music_profile(profile_id: str | None = None) -> dict` (keys `name, bpm, start_offset, intro_seconds`)
  - `max_clip_seconds(video_tool: str | None) -> float`
  - `plan_shape(bpm: float, start_offset: float, intro_seconds: float, scene_target: float, video_range: tuple[float, float], max_clip: float) -> dict` (keys `beats_per_scene, scenes, scene_seconds, total_seconds, bar_aligned, warnings`)
  - `cut_times(beats_per_scene: int, scenes: int, bpm: float, fps: int = FPS) -> list[float]` (độ dài `scenes + 1`, phần tử đầu 0.0)

- [ ] **Step 1: Tạo dữ liệu**

`library/music-profiles.json`:
```json
{
  "faded-intro": {
    "name": "Faded – Rapid Town Baby (intro không lời)",
    "bpm": 80.0,
    "start_offset": 0.0,
    "intro_seconds": 30.0,
    "note": "Khi đăng: chọn bài trong app, kéo điểm bắt đầu tới start_offset"
  }
}
```

`library/tool-guides/limits.json`:
```json
{
  "_note": "Độ dài clip tối đa (giây) mỗi app video tạo được trong 1 lần. Dùng để giới hạn độ dài cảnh.",
  "generic": 5,
  "veo": 8,
  "kling": 10,
  "hailuo": 6,
  "runway": 10
}
```

Thêm vào `config.json` (giữ nguyên các khóa cũ), ngay sau `"use_clip_audio": false`:
```json
  "use_clip_audio": false,
  "music_profile": "faded-intro",
  "scene_seconds_target": 3.5,
  "video_seconds_target": [15, 20]
```

`tests/__init__.py`: file rỗng.

`tests/helpers.py`:
```python
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
```

- [ ] **Step 2: Viết test thất bại**

`tests/test_beat_grid.py`:
```python
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
        for bpm in (72, 79.5, 80, 90):
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
```

- [ ] **Step 3: Chạy test, xác nhận thất bại**

Run: `python -m unittest tests.test_beat_grid -v`
Expected: FAIL / ERROR `ModuleNotFoundError: No module named 'episode_state'`

- [ ] **Step 4: Viết phần đầu `tools/episode_state.py`**

```python
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
```

- [ ] **Step 5: Chạy test, xác nhận đạt**

Run: `python -m unittest tests.test_beat_grid -v`
Expected: 9 tests OK

- [ ] **Step 6: Commit**

```bash
git add library/music-profiles.json library/tool-guides/limits.json config.json tools/episode_state.py tests/
git commit -m "feat(state): music profiles, clip limits and beat grid"
```

---

### Task 2: Load, migrate và ghi có version + lịch sử

**Files:**
- Modify: `tools/episode_state.py`
- Create: `tests/test_storage.py`

**Interfaces:**
- Consumes: `music_profile`, `max_clip_seconds`, `plan_shape`, `cut_times`, `StateError` (Task 1)
- Produces:
  - `class VersionConflict(StateError)`
  - `migrate(s: dict) -> dict` (bản sao, không sửa đầu vào)
  - `plan_for(s: dict) -> dict` (kết quả `plan_shape` cho tập)
  - `load(ep_dir: Path) -> dict` (đã migrate)
  - `save(ep_dir: Path, s: dict, expected_version: int) -> dict` (trả bản đã ghi, `version` tăng 1; ném `VersionConflict` nếu lệch)
  - `shot_seconds(s: dict) -> list[float]`

Cấu trúc mỗi cảnh sau migrate: `n, angle, scene_vi, characters, image_prompt, negative, locked_image, locked_sig, motion_prompt, motion_stale, edited`.

- [ ] **Step 1: Viết test thất bại**

`tests/test_storage.py`:
```python
import json
import tempfile
import unittest
from pathlib import Path

from tests import helpers  # noqa: F401
import episode_state as es

OLD = {
    "id": "ep009", "series": "night-shift", "palette": "night-shift", "characters": ["ong-moon"],
    "concept": {"logline_vi": "x"}, "title": "t", "status": "draft", "video_tool": "generic",
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
        self.assertIn("beats_per_scene", s)
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

    def test_shot_seconds(self):
        s = es.migrate({**OLD, "beats_per_scene": 4, "music_profile": "faded-intro"})
        self.assertEqual(es.shot_seconds(s), [3.0, 3.0])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy test, xác nhận thất bại**

Run: `python -m unittest tests.test_storage -v`
Expected: ERROR `AttributeError: module 'episode_state' has no attribute 'migrate'`

- [ ] **Step 3: Thêm vào `tools/episode_state.py`**

Thêm `import copy`, `import time`, `from common import save_json` vào phần import (giữ import cũ):
```python
import copy
import math
import time

from common import LIB, config, load_json, save_json
```

Thêm sau `class StateError`:
```python
class VersionConflict(StateError):
    """script.json đã bị nơi khác sửa trong lúc đang làm."""
```

Thêm cuối file:
```python
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
```

- [ ] **Step 4: Chạy toàn bộ test**

Run: `python -m unittest discover -s tests -v`
Expected: tất cả OK (14 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/episode_state.py tests/test_storage.py
git commit -m "feat(state): migrate old scripts, versioned save with history"
```

---

### Task 3: Giai đoạn, chốt ảnh, đánh dấu cần cập nhật

**Files:**
- Modify: `tools/episode_state.py`
- Create: `tests/test_phase.py`

**Interfaces:**
- Consumes: `load`, `migrate`, `StateError` (Task 1–2)
- Produces:
  - `IMAGE_EXTS`, `CLIP_EXTS`, `PHASES = ("idea","storyboard","image_prompts","images","video_prompts","clips","final","published")`
  - `find_image(ep_dir: Path, n: int) -> Path | None`, `find_clip(ep_dir: Path, n: int) -> Path | None`
  - `file_sig(p: Path) -> str`, `is_locked(ep_dir: Path, sh: dict) -> bool`
  - `lock(s, ep_dir, n) -> dict`, `lock_all(s, ep_dir) -> dict`, `unlock(s, n) -> dict`, `sync(s, ep_dir) -> bool` (tự bỏ chốt khi file đã đổi; trả True nếu có thay đổi)
  - `phase(s, ep_dir) -> str`, `next_step(s, ep_dir) -> dict` (keys `phase, by, message`; `by` ∈ `"ai"`, `"user"`, `"done"`)

**Lưu ý:** `find_clip(ep_dir, n)` nhận **thư mục tập**, khác chữ ký cũ trong `assemble.py` (nhận thư mục `clips`). Task 5–6 cập nhật nơi gọi.

- [ ] **Step 1: Viết test thất bại**

`tests/test_phase.py`:
```python
import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from tests import helpers  # noqa: F401
import episode_state as es


def shot(n, **kw):
    base = {"n": n, "angle": "wide", "scene_vi": f"cảnh {n}", "characters": [],
            "image_prompt": f"img {n}", "negative": "", "motion_prompt": f"mot {n}"}
    base.update(kw)
    return base


def make(tmp, shots, **top):
    d = Path(tmp) / "ep050"
    (d / "images").mkdir(parents=True)
    (d / "clips").mkdir()
    data = {"id": "ep050", "status": "draft", "storyboard_approved": True, "beats_per_scene": 4,
            "music_profile": "faded-intro", "shots": shots, **top}
    (d / "script.json").write_text(json.dumps(data), encoding="utf-8")
    return d


def touch(p, content=b"x"):
    p.write_bytes(content)


class PhaseTest(unittest.TestCase):
    def test_full_progression(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make(tmp, [])
            self.assertEqual(es.phase(es.load(d), d), "idea")

            d2 = Path(tmp) / "b"
            d2.mkdir()
            (d2 / "script.json").write_text(json.dumps({"id": "b", "shots": [shot(1)], "storyboard_approved": False}),
                                            encoding="utf-8")
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
```

- [ ] **Step 2: Chạy test, xác nhận thất bại**

Run: `python -m unittest tests.test_phase -v`
Expected: ERROR `AttributeError: module 'episode_state' has no attribute 'phase'`

- [ ] **Step 3: Thêm vào cuối `tools/episode_state.py`**

```python
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
```

- [ ] **Step 4: Chạy toàn bộ test**

Run: `python -m unittest discover -s tests -v`
Expected: tất cả OK

- [ ] **Step 5: Commit**

```bash
git add tools/episode_state.py tests/test_phase.py
git commit -m "feat(state): derive phase, lock/unlock images, stale motion prompts"
```

---

### Task 4: Kiểm tra & ghi kết quả AI, duyệt phân cảnh, CLI

**Files:**
- Modify: `tools/episode_state.py`
- Create: `tests/test_apply.py`

**Interfaces:**
- Consumes: Task 1–3
- Produces:
  - `KINDS = ("storyboard", "image_prompts", "video_prompts", "seo")`
  - `validate(s: dict, kind: str, data: dict) -> tuple[dict, list[str], list[str]]` (dữ liệu sạch, lỗi, cảnh báo)
  - `apply(s: dict, kind: str, data: dict, overwrite_edited: bool = False) -> list[str]` (sửa `s` tại chỗ, trả cảnh báo; ném `StateError` nếu có lỗi)
  - `approve(s: dict) -> dict`
  - CLI `main()` với lệnh `phase | plan | show | apply | approve | lock | unlock`

**Định dạng JSON đầu vào của `apply`:**
- `storyboard`: `{"shots": [{"angle": str, "scene_vi": str, "characters": [str]}...], "title": str, "description": str, "hashtags": [str]}` — số phần tử `shots` phải bằng `plan_for(s)["scenes"]`.
- `image_prompts`: `{"shots": [{"n": int, "image_prompt": str, "negative": str}]}`
- `video_prompts`: `{"shots": [{"n": int, "motion_prompt": str}]}`
- `seo`: `{"title": str, "description": str, "hashtags": [str]}`

- [ ] **Step 1: Viết test thất bại**

`tests/test_apply.py`:
```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests import helpers
import episode_state as es

N = es.plan_for({"music_profile": "faded-intro", "video_tool": "generic"})["scenes"]


def board(n=N, **over):
    shots = [{"angle": "wide", "scene_vi": f"cảnh {i}", "characters": ["ong-moon"]} for i in range(1, n + 1)]
    data = {"shots": shots, "title": "POV: polishing the moon 🌙", "description": "d", "hashtags": ["moon", "#cozy"]}
    data.update(over)
    return data


def new_ep(tmp):
    d = Path(tmp) / "ep060"
    (d / "images").mkdir(parents=True)
    (d / "clips").mkdir()
    (d / "script.json").write_text(json.dumps({"id": "ep060", "music_profile": "faded-intro",
                                               "video_tool": "generic", "shots": []}), encoding="utf-8")
    return d


class StoryboardTest(unittest.TestCase):
    def test_apply_storyboard(self):
        s = es.migrate({"id": "x", "music_profile": "faded-intro", "video_tool": "generic", "shots": []})
        warns = es.apply(s, "storyboard", board())
        self.assertEqual(len(s["shots"]), N)
        self.assertEqual([sh["n"] for sh in s["shots"]], list(range(1, N + 1)))
        self.assertEqual(s["beats_per_scene"], 4)
        self.assertFalse(s["storyboard_approved"])
        self.assertEqual(s["hashtags"], ["#moon", "#cozy"])
        self.assertEqual(warns, [])

    def test_wrong_count_is_error(self):
        s = es.migrate({"id": "x", "music_profile": "faded-intro", "shots": []})
        with self.assertRaisesRegex(es.StateError, "cảnh"):
            es.apply(s, "storyboard", board(n=N + 2))

    def test_unknown_character_and_angle_are_fixed_with_warning(self):
        s = es.migrate({"id": "x", "music_profile": "faded-intro", "shots": []})
        data = board()
        data["shots"][0]["characters"] = ["ong-moon", "mickey"]
        data["shots"][0]["angle"] = "dutch"
        warns = es.apply(s, "storyboard", data)
        self.assertEqual(s["shots"][0]["characters"], ["ong-moon"])
        self.assertEqual(s["shots"][0]["angle"], "medium")
        self.assertEqual(len(warns), 2)

    def test_edit_after_approval_resets_only_changed_shots(self):
        s = es.migrate({"id": "x", "music_profile": "faded-intro", "shots": []})
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
        self.s = es.migrate({"id": "x", "music_profile": "faded-intro", "shots": []})
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy test, xác nhận thất bại**

Run: `python -m unittest tests.test_apply -v`
Expected: ERROR `AttributeError: module 'episode_state' has no attribute 'apply'`

- [ ] **Step 3: Thêm vào cuối `tools/episode_state.py`**

Thêm `import argparse`, `import json`, `import sys`, `from pathlib import Path` và `from common import EPISODES, ROOT` vào phần import:
```python
import argparse
import copy
import json
import math
import sys
import time
from pathlib import Path

from common import EPISODES, LIB, ROOT, config, load_json, save_json
```

Thêm cuối file:
```python
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
        keep_old = s.get("storyboard_approved") and len(old) == len(clean["shots"])
        new_shots = []
        for sh in clean["shots"]:
            prev = old.get(sh["n"]) if keep_old else None
            same = prev and all(prev[k] == sh[k] for k in ("angle", "scene_vi", "characters"))
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
```

- [ ] **Step 4: Chạy toàn bộ test**

Run: `python -m unittest discover -s tests -v`
Expected: tất cả OK

- [ ] **Step 5: Commit**

```bash
git add tools/episode_state.py tests/test_apply.py
git commit -m "feat(state): validate/apply AI output, approve storyboard, CLI"
```

---

### Task 5: Cập nhật new_episode, export_prompts, web.py, flip.py theo cấu trúc mới

**Files:**
- Modify: `tools/new_episode.py`, `tools/export_prompts.py`, `tools/web.py:21-69`, `tools/flip.py`
- Create: `tests/test_compat.py`

**Interfaces:**
- Consumes: `es.load`, `es.save`, `es.shot_seconds`, `es.find_image`, `es.find_clip`, `es.is_locked` (Task 2–3)
- Produces:
  - `new_episode.build_script(ep_id, series, verb_id, obj_id, setting, time, title, logline, custom_idea, cfg) -> dict`
  - `web.episode_summary(d, full=False)`: mỗi cảnh khi `full=True` có thêm `dur` (float, giây) và `role` (`"<n> phách"`), để Studio hiện tại chạy không đổi.

- [ ] **Step 1: Viết test thất bại**

`tests/test_compat.py`:
```python
import json
import tempfile
import unittest
from pathlib import Path

from tests import helpers  # noqa: F401
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
                "id": "ep070", "series": "night-shift", "palette": "night-shift", "music_profile": "faded-intro",
                "beats_per_scene": 4, "status": "draft", "title": "t", "concept": {"logline_vi": "l"},
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
```

- [ ] **Step 2: Chạy test, xác nhận thất bại**

Run: `python -m unittest tests.test_compat -v`
Expected: ERROR `AttributeError: module 'new_episode' has no attribute 'build_script'`

- [ ] **Step 3: Sửa `tools/new_episode.py`**

Thêm hàm sau `make_title`:
```python
def build_script(ep_id, series, verb_id, obj_id, setting, time, title, logline, custom_idea, cfg):
    return {
        "id": ep_id,
        "version": 1,
        "series": series["id"],
        "palette": series["palette"],
        "characters": series["characters"],
        "concept": {"verb": verb_id, "object": obj_id, "setting": setting, "time": time,
                    "logline_vi": logline, "custom_idea": custom_idea},
        "title": title,
        "description": "",
        "hashtags": [],
        "image_tool": cfg.get("image_tool") or "generic",
        "video_tool": cfg.get("video_tool") or "generic",
        "music_profile": cfg.get("music_profile", ""),
        "storyboard_approved": False,
        "beats_per_scene": None,
        "status": "draft",
        "shots": [],
    }
```

Trong `main()`, thêm tham số sau `--seed`:
```python
    ap.add_argument("--idea", default="", help="ý tưởng tự gõ (AI ưu tiên khi viết phân cảnh)")
```

Thay khối `save_json(d / "script.json", {...})` (dòng 90–107) bằng:
```python
    save_json(d / "script.json", build_script(
        ep_id, series, verb_id, obj_id, setting["id"], time["id"], title,
        result["logline_vi"], args.idea.strip(), cfg))
```

Thay dòng in cuối:
```python
        print(f"\nĐã tạo {d}\nBước tiếp: gọi /dream {ep_id} để viết phân cảnh.")
```

- [ ] **Step 4: Sửa `tools/export_prompts.py`** (thay toàn bộ file)

```python
"""Xuất episodes/<id>/prompts.md: bảng prompt để copy-paste vào app ảnh / video.

  python tools/export_prompts.py ep001
"""
import sys

import episode_state as es
from common import LIB, episode_dir, load_json


def main():
    if len(sys.argv) != 2:
        sys.exit("Cách dùng: python tools/export_prompts.py <ep_id>")
    d = episode_dir(sys.argv[1])
    s = es.load(d)
    if not s["shots"]:
        sys.exit("Tập chưa có phân cảnh. Gọi /dream trước.")

    palette = load_json(LIB / "palettes.json")[s["palette"]]
    secs = es.shot_seconds(s)
    clip_need = max(secs) + es.HEAD_TRIM
    out = [
        f"# {s['id']}: {s['title']}",
        "",
        f"- Series: `{s['series']}` · Palette: **{palette['name']}** · {len(s['shots'])} cảnh × "
        f"{secs[0]:.2f}s = {sum(secs):.1f}s · {s['beats_per_scene']} phách/cảnh · hard cut",
        f"- Công cụ ảnh: `{s['image_tool']}` · Công cụ video: `{s['video_tool']}` · tạo clip dài ≥ {clip_need:.1f}s",
        f"- Ý tưởng: {s['concept'].get('custom_idea') or s['concept'].get('logline_vi', '')}",
        "",
        "## Ảnh tham chiếu cần đính kèm",
    ]
    for c in s["characters"]:
        out.append(f"- `{c}`: library/characters/{c}/ref-sheet.png")
    out.append("- Style anchor (nếu có): library/style-anchors/")
    out.append("")

    for sh, sec in zip(s["shots"], secs):
        n = f"s{sh['n']:02d}"
        locked = "✓ đã chốt" if es.is_locked(d, sh) else "chưa chốt"
        out += [
            f"## Cảnh {sh['n']} · {sh['angle']} · {sec:.2f}s · ảnh {locked}",
            "",
            f"> {sh['scene_vi']}",
            "",
            f"Nhân vật: {', '.join(sh['characters']) or 'không'}",
            "",
            "**Prompt ảnh**",
            "```",
            sh["image_prompt"] or "(chưa có — gọi /dream)",
            "```",
        ]
        if sh["negative"]:
            out += ["**Negative**", "```", sh["negative"], "```"]
        motion = sh["motion_prompt"] or "(chốt đủ ảnh rồi gọi /dream để viết)"
        if sh["motion_stale"]:
            motion += "\n(⚠ cần cập nhật vì ảnh đã đổi)"
        out += ["**Prompt chuyển động**", "```", motion, "```",
                f"Lưu ảnh: `images/{n}.png`, lưu clip: `clips/{n}.mp4`", ""]

    (d / "prompts.md").write_text("\n".join(out), encoding="utf-8")
    print(f"Đã xuất {d / 'prompts.md'}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Sửa `tools/web.py`**

Thay dòng 21 `from assemble import find_clip` bằng:
```python
import episode_state as es
```

Xóa hàm `find_image` (dòng 34–39). Thay hàm `rel` (dòng 42–43) bằng:
```python
def rel(p):
    if not p:
        return None
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()
```

Thay 8 dòng đầu thân `episode_summary` (dòng 54–60) bằng:
```python
    s = es.load(d)
    secs = es.shot_seconds(s)
    shots = []
    for sh, sec in zip(s["shots"], secs):
        item = {**sh, "dur": sec, "role": f"{s['beats_per_scene']} phách"} if full else {"n": sh["n"]}
        item["image"] = rel(es.find_image(d, sh["n"]))
        item["clip"] = rel(es.find_clip(d, sh["n"]))
        shots.append(item)
```

Trong `do_PUT`, tìm chỗ dùng `find_image(` hoặc `find_clip(` (nếu có) và đổi sang `es.find_image(d, n)` / `es.find_clip(d, n)`. Chạy `python -c "import ast,sys; ast.parse(open('tools/web.py',encoding='utf-8').read())"` để chắc cú pháp đúng, rồi tìm còn sót:

Run: `python -c "import re;t=open('tools/web.py',encoding='utf-8').read();print([m for m in re.findall(r'\b(?<!es\.)find_(?:image|clip)\(',t)])"`
Expected: `[]`

- [ ] **Step 6: Sửa `tools/flip.py`**

Thay `from assemble import find_clip` bằng `from episode_state import find_clip`, và thay `clip = find_clip(d / "clips", int(sys.argv[2].lstrip("s")))` bằng:
```python
    clip = find_clip(d, int(sys.argv[2].lstrip("s")))
```

- [ ] **Step 7: Chạy toàn bộ test**

Run: `python -m unittest discover -s tests -v`
Expected: tất cả OK

- [ ] **Step 8: Kiểm tra Studio vẫn chạy**

Run (nền): `python tools/web.py --port 8799 --no-browser`, rồi:
`python -c "import urllib.request,json;print(len(json.load(urllib.request.urlopen('http://127.0.0.1:8799/api/episodes'))))"`
Expected: in ra số tập (≥ 0), không lỗi. Dừng server.

- [ ] **Step 9: Commit**

```bash
git add tools/new_episode.py tools/export_prompts.py tools/web.py tools/flip.py tests/test_compat.py
git commit -m "refactor: tools use episode_state; Studio stays compatible"
```

---

### Task 6: Dựng video theo lưới phách + tiếng gõ nhịp

**Files:**
- Rewrite: `tools/assemble.py`
- Create: `tests/test_assemble.py`

**Interfaces:**
- Consumes: `es.load`, `es.music_profile`, `es.cut_times`, `es.find_clip`, `es.HEAD_TRIM`, `es.SLOWDOWN_LIMIT`, `es.FPS`, `es.StateError`; `common.probe`, `common.ffmpeg_exe`
- Produces:
  - `class AssembleError(Exception)`
  - `write_metronome(path: Path, bpm: float, total: float, rate: int = 48000) -> None`
  - `build(ep_dir: Path, preview=False, clip_audio=False, music=None, metronome=False) -> Path`
  - re-export `find_clip` (tương thích ngược)

- [ ] **Step 1: Viết test thất bại**

`tests/test_assemble.py`:
```python
import json
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path

from tests import helpers  # noqa: F401
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
        "id": "ep080", "palette": "cotton-morning", "music_profile": "faded-intro", "beats_per_scene": 4,
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
```

- [ ] **Step 2: Chạy test, xác nhận thất bại**

Run: `python -m unittest tests.test_assemble -v`
Expected: ERROR `AttributeError: module 'assemble' has no attribute 'build'`

- [ ] **Step 3: Viết lại `tools/assemble.py`** (thay toàn bộ file)

```python
"""Dựng video theo lưới phách: mọi cảnh dài bằng nhau, hard cut đúng phách, không nhạc.

  python tools/assemble.py ep001                         # final.mp4 1080x1920
  python tools/assemble.py ep001 --preview               # preview.mp4 540x960
  python tools/assemble.py ep001 --preview --metronome   # kèm tiếng gõ nhịp để kiểm tra khớp nhạc
  python tools/assemble.py ep001 --clip-audio            # giữ âm thanh gốc của clip
  python tools/assemble.py ep001 --music music/x.mp3     # chỉ dùng nhạc bạn có quyền sử dụng

Mỗi clip bỏ 0.5s đầu; clip thiếu ≤10% được làm chậm cho vừa, thiếu hơn thì báo lỗi.
Film look: library/lut/film.cube nếu có. Endcard: library/brand/endcard.png ở 2.5s cuối nếu có.
"""
import argparse
import math
import struct
import subprocess
import sys
import wave
from pathlib import Path

import episode_state as es
from common import LIB, ROOT, config, episode_dir, ffmpeg_exe, load_json, probe
from episode_state import find_clip  # noqa: F401  (tools/flip.py và mã cũ import từ đây)

# Nâng vùng tối, giảm vùng sáng, giảm bão hòa, hạt phim, viền tối.
FILM_LOOK = ("curves=all='0/0.06 0.5/0.5 1/0.95',"
             "eq=saturation=0.87:contrast=0.97,"
             "noise=alls=7:allf=t,"
             "vignette=angle=PI/5")
ENDCARD_SECONDS = 2.5


class AssembleError(Exception):
    """Lỗi dựng video người dùng cần biết (tiếng Việt)."""


def write_metronome(path, bpm, total, rate=48000):
    beat = 60.0 / bpm
    n = int(round(total * rate))
    click = int(0.04 * rate)
    buf = bytearray(n * 2)
    k = 0
    while True:
        start = int(round(k * beat * rate))
        if start >= n:
            break
        accent = k % 4 == 0
        freq, amp = (1500.0, 0.6) if accent else (1000.0, 0.4)
        for i in range(min(click, n - start)):
            v = amp * math.sin(2 * math.pi * freq * (i + 1) / rate) * (1 - i / click)
            struct.pack_into("<h", buf, (start + i) * 2, int(32767 * v))
        k += 1
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(buf))


def _plan_clips(ep_dir, s, cuts):
    plans, problems = [], []
    for i, sh in enumerate(s["shots"]):
        name = f"s{sh['n']:02d}"
        need = cuts[i + 1] - cuts[i]
        clip = es.find_clip(ep_dir, sh["n"])
        if not clip:
            problems.append(f"{name}: chưa có clip")
            continue
        clip_dur, has_audio = probe(clip)
        if clip_dur >= need:
            plans.append((clip, min(es.HEAD_TRIM, clip_dur - need), 1.0, need, has_audio))
        elif clip_dur >= need * (1 - es.SLOWDOWN_LIMIT):
            plans.append((clip, 0.0, need / clip_dur, need, has_audio))
        else:
            problems.append(f"{name}: clip dài {clip_dur:.2f}s, cần ≥ {need:.2f}s "
                            f"(thiếu {need - clip_dur:.2f}s) → tạo lại clip dài hơn")
    if problems:
        raise AssembleError("Chưa dựng được:\n" + "\n".join(problems))
    return plans


def build(ep_dir, preview=False, clip_audio=False, music=None, metronome=False):
    cfg = config()
    s = es.load(ep_dir)
    if not s["shots"]:
        raise AssembleError("Tập chưa có phân cảnh.")
    bpm = es.music_profile(s.get("music_profile"))["bpm"]
    cuts = es.cut_times(s["beats_per_scene"], len(s["shots"]), bpm)
    total = cuts[-1]
    plans = _plan_clips(ep_dir, s, cuts)
    W, H = (540, 960) if preview else (cfg["output"]["width"], cfg["output"]["height"])
    fps = es.FPS

    inputs, graph = [], []
    for i, (clip, start, factor, need, has_audio) in enumerate(plans):
        inputs += ["-ss", f"{start:.3f}", "-i", str(clip)]
        graph.append(f"[{i}:v]setpts=(PTS-STARTPTS)*{factor:.6f},"
                     f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                     f"fps={fps},trim=duration={need:.6f},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v{i}]")
    n = len(plans)
    use_clip_audio = clip_audio and not metronome and not music
    if use_clip_audio:
        for i, (_, _, factor, need, has_audio) in enumerate(plans):
            if has_audio:
                graph.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                             f"atempo={1 / factor:.6f},atrim=0:{need:.6f},asetpts=PTS-STARTPTS[a{i}]")
            else:
                graph.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{need:.6f}[a{i}]")

    look = FILM_LOOK
    lut = LIB / "lut" / "film.cube"
    if lut.exists():
        look = f"lut3d=file='{lut.relative_to(ROOT).as_posix()}'," + look
    grade = load_json(LIB / "palettes.json").get(s.get("palette"), {}).get("grade")
    if grade:
        look += "," + grade
    graph.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vc]")
    graph.append(f"[vc]{look}[vg]")
    vout, next_input = "[vg]", n

    endcard = LIB / "brand" / "endcard.png"
    if endcard.exists():
        start_at = max(total - ENDCARD_SECONDS, 0)
        inputs += ["-loop", "1", "-framerate", str(fps), "-t", f"{total:.3f}", "-i", str(endcard)]
        graph.append(f"[{next_input}:v]scale={int(W * 0.22)}:-1,format=rgba,"
                     f"fade=in:st={start_at:.2f}:d=0.6:alpha=1[logo]")
        graph.append(f"{vout}[logo]overlay=(W-w)/2:H*0.80:enable='gte(t,{start_at:.2f})'[vl]")
        vout, next_input = "[vl]", next_input + 1

    aout = None
    if metronome:
        wav = ep_dir / ".metronome.wav"
        write_metronome(wav, bpm, total)
        inputs += ["-i", str(wav)]
        graph.append(f"[{next_input}:a]aformat=sample_rates=48000:channel_layouts=stereo[am]")
        aout = "[am]"
    elif music:
        music_path = Path(music) if Path(music).is_absolute() else ROOT / music
        if not music_path.exists():
            raise AssembleError(f"Không thấy file nhạc: {music_path}")
        inputs += ["-stream_loop", "-1", "-i", str(music_path)]
        graph.append(f"[{next_input}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,"
                     f"afade=t=out:st={max(total - 1.5, 0):.3f}:d=1.5,loudnorm=I=-14:TP=-1.5,"
                     f"aformat=sample_rates=48000:channel_layouts=stereo[am]")
        aout = "[am]"
    elif use_clip_audio:
        graph.append("".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[ac]")
        aout = "[ac]"

    out = ep_dir / ("preview.mp4" if preview else "final.mp4")
    graph_file = ep_dir / ".filtergraph.txt"
    graph_file.write_text(";\n".join(graph), encoding="utf-8")
    cmd = [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", *inputs,
           "-filter_complex_script", str(graph_file), "-map", vout]
    if aout:
        cmd += ["-map", aout, "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast" if preview else "medium",
            "-crf", "23" if preview else "18", "-pix_fmt", "yuv420p", "-r", str(fps),
            "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, errors="replace")
    graph_file.unlink(missing_ok=True)
    if r.returncode:
        raise AssembleError("ffmpeg lỗi:\n" + r.stderr.strip()[-2000:])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep_id")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--clip-audio", action="store_true")
    ap.add_argument("--music")
    ap.add_argument("--metronome", action="store_true")
    args = ap.parse_args()
    d = episode_dir(args.ep_id)
    try:
        s = es.load(d)
        secs = es.shot_seconds(s)
        print(f"Dựng {len(secs)} cảnh × {secs[0]:.2f}s = {sum(secs):.2f}s"
              + (" · tiếng gõ nhịp" if args.metronome else "") if secs else "")
        out = build(d, args.preview, args.clip_audio, args.music, args.metronome)
    except (AssembleError, es.StateError) as e:
        sys.exit(str(e))
    print(f"Xong: {out}")
    if not (args.metronome or args.music or args.clip_audio):
        print("Video không có nhạc: chọn nhạc trong app khi đăng (kéo tới start_offset của hồ sơ nhạc).")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Chạy test dựng video**

Run: `python -m unittest tests.test_assemble -v`
Expected: 6 tests OK (mất khoảng 30–60 giây)

Nếu `test_cuts_land_on_beat_grid` lệch màu đúng tại điểm cắt: kiểm tra bộ lọc `fps` đặt **trước** `trim` và lệnh có `-r 30`; độ dài từng cảnh lấy từ `cut_times` (đã làm tròn về 1/30s) nên số khung hình mỗi cảnh là số nguyên.

- [ ] **Step 5: Chạy toàn bộ test**

Run: `python -m unittest discover -s tests -v`
Expected: tất cả OK

- [ ] **Step 6: Commit**

```bash
git add tools/assemble.py tests/test_assemble.py
git commit -m "feat(assemble): beat-grid hard cuts, head trim, slowdown <=10%, metronome"
```

---

### Task 7: Hướng dẫn sáng tạo, skill `/dream`, cập nhật agent và README

**Files:**
- Create: `library/guides/storyboard.md`, `library/guides/image-prompts.md`, `library/guides/video-prompts.md`, `library/guides/seo.md`, `.agent/skills/dream/SKILL.md`, `.agent/workflows/dream.md`
- Modify: `.agent/workflows/new-episode.md`, `.agent/workflows/weekly-batch.md`, `.agent/skills/prompt-writer/SKILL.md`, `.agent/skills/seo-metadata/SKILL.md`, `.agent/skills/assemble-video/SKILL.md`, `.agent/rules/dreamnostalgic.md`, `README.md`
- Delete: `.agent/skills/episode-script/`

**Interfaces:**
- Consumes: CLI `python tools/episode_state.py phase|plan|show|apply|approve|lock|unlock` (Task 4); `python tools/assemble.py --preview --metronome` (Task 6); `python tools/export_prompts.py` (Task 5)

- [ ] **Step 1: Tạo `library/guides/storyboard.md`**

````markdown
# Hướng dẫn: viết phân cảnh

Dùng chung cho agent Antigravity và (sau này) nút AI trong Studio.

## Hình dạng (bắt buộc)
- Số cảnh và độ dài lấy từ `python tools/episode_state.py plan <ep>`: viết **đúng** `scenes` cảnh.
- Mọi cảnh **dài bằng nhau** (vd. 3,0 giây). Chỉ **hard cut**.

## Cấu trúc
- **Không có hook, không có reveal.** Mọi cảnh ngang hàng: mỗi cảnh là một khoảnh khắc kỳ diệu trọn vẹn trong cùng một thế giới.
- Liền mạch về không khí: cùng thế giới, cùng bảng màu của series, cùng giờ trong ngày hoặc chuyển dần (chiều → hoàng hôn → đêm).
- Luân phiên góc máy (`wide`, `medium`, `hands`, `low`, `over-shoulder`, `detail`); **không** để hai cảnh liền nhau cùng góc.
- Cảnh 1 phải đọc được trong 1 giây: vật thể kỳ diệu + người đang làm việc, rõ ràng.
- Mỗi cảnh **một** hành động chậm, vừa trong khoảng 3 giây.
- Nhân vật: chỉ dùng id trong danh sách của series (`library/series.json`); tối đa 2 nhân vật mỗi cảnh; Golden xuất hiện 1–2 cảnh.
- Nếu `concept.custom_idea` có nội dung: phát triển ý đó thay vì logline.

## Đầu ra (JSON, ghi vào file tạm rồi `apply ... storyboard`)
```json
{
  "shots": [
    {"angle": "wide", "scene_vi": "Ông Moon đứng trên xe nâng, đánh bóng mặt trăng khổng lồ trên thị trấn", "characters": ["ong-moon"]}
  ],
  "title": "POV: your job is polishing the moon 🌙",
  "description": "The moon gets a little dusty every night. Someone has to polish it.",
  "hashtags": ["#dreamnostalgic", "#shorts", "#nostalgia", "#dreamcore", "#moon", "#cozy"]
}
```
`scene_vi`: tiếng Việt, 1 câu. Tiêu đề/mô tả/hashtag theo `library/guides/seo.md`.
````

- [ ] **Step 2: Tạo `library/guides/image-prompts.md`**

````markdown
# Hướng dẫn: viết prompt ảnh

## Đọc trước
1. `config.json` → `image_tool` (hoặc `image_tool` trong script.json); trống = `generic`. Theo đúng `library/tool-guides/<image_tool>.md`.
2. `library/prompt-vocab.md`: STYLE BLOCK, ánh sáng, negative.
3. `library/palettes.json` → `prompt_phrase` của palette tập.
4. `library/characters/<id>.md` → **khóa ngoại hình**: dán NGUYÊN VĂN, không diễn đạt lại.

## Khung prompt (tiếng Anh, 60–110 từ, một đoạn văn)
```
[Tỉ lệ dọc 9:16 theo cách tool yêu cầu]. [Khóa ngoại hình nhân vật hoặc người lao động chung]
[hành động thủ công tỉ mỉ] [vật thể trong mơ] [bối cảnh], [giờ trong ngày]. [Đạo cụ].
[Góc máy của cảnh]. [Một chi tiết cảm xúc].
[STYLE BLOCK]. [palette prompt_phrase]. [Điều cần tránh nếu tool không có ô negative.]
```
- Một hành động chính mỗi cảnh; vật thể trong mơ lớn, rõ trong khung dọc.
- Chừa 15% đáy khung trống chi tiết quan trọng.
- Nhãn, biển hiệu: yêu cầu để trống (`blank labels`).
- Giữ nhất quán giữa các cảnh: cùng trang phục, cùng giờ/ánh sáng theo phân cảnh.

## Đầu ra (JSON, `apply ... image_prompts`)
```json
{"shots": [{"n": 1, "image_prompt": "Create a vertical 9:16 photograph...", "negative": "text, watermark, ..."}]}
```
Tool không có ô negative → để `negative` rỗng và đưa phần tránh vào cuối `image_prompt`.
````

- [ ] **Step 3: Tạo `library/guides/video-prompts.md`**

````markdown
# Hướng dẫn: viết prompt video

Chỉ viết khi **mọi cảnh đã chốt ảnh**. Luôn **xem ảnh đã chốt** (`locked_image` trong script.json) trước khi viết: mô tả chuyển động khớp với đúng những gì có trong ảnh.

## Mỗi cảnh
- Tiếng Anh, 1–3 câu: [chuyển động camera] + [một hành động nhỏ, chậm của chủ thể] + [chuyển động môi trường] + `calm, dreamy pace, no fast movement, no dialogue`.
- Không mô tả lại toàn bộ ảnh; chỉ mô tả cái gì chuyển động.
- Theo cách viết của `library/tool-guides/<video_tool>.md`.

## Liền mạch qua hard cut
- Xem cả chuỗi cảnh: tránh hai cảnh liền nhau có hướng camera ngược nhau (vd. push-in rồi pull-back).
- Ưu tiên `slow push-in`, `locked-off static`, `gentle parallax`; mỗi tập dùng tối đa 2 kiểu camera.
- Chuyển động bắt đầu ngay từ đầu clip (clip bị cắt 0,5 giây đầu và chỉ dùng khoảng 3 giây).

## Độ dài clip cần tạo
`plan` → `scene_seconds + 0.5` giây; chọn chế độ ngắn nhất của app ≥ con số này.

## Đầu ra (JSON, `apply ... video_prompts`)
```json
{"shots": [{"n": 1, "motion_prompt": "Slow gentle push-in. The man moves the buffer in small circles; faint sparkles drift off the moon. Calm, dreamy pace, no fast movement, no dialogue."}]}
```
Nếu chỉ có vài cảnh `motion_stale`: chỉ trả các cảnh đó (và giữ liền mạch với cảnh kề bên).
````

- [ ] **Step 4: Tạo `library/guides/seo.md`**

```markdown
# Hướng dẫn: tiêu đề, mô tả, hashtag

## Tiêu đề (tiếng Anh, ≤ 60 ký tự, 1 emoji cuối)
Dùng `title_patterns` của series làm gốc. Kiểu hiệu quả: `POV: your job is polishing the moon 🌙`, `Someone has to keep the stars running ✨`, `How sunset clouds are made 🌸`. Không clickbait sai sự thật, không viết hoa toàn bộ.

## Mô tả
- Dòng 1: 1–2 câu thơ ngắn, hoài niệm (series Phố Mơ thêm 1 dòng tiếng Việt).
- Dòng 2: tên series, vd. `Night Shift · a tiny job in a dreamy world.`

## Hashtag (5–8)
- Luôn có: `#dreamnostalgic #shorts #nostalgia #dreamcore`
- Theo chủ đề (1–2): `#moon #clouds #rainbow`…
- Theo phong cách (1–2): `#cozy #surreal #aiart`
```

- [ ] **Step 5: Tạo `.agent/skills/dream/SKILL.md`**

````markdown
---
name: dream
description: Điều phối quy trình làm một tập Dreamnostalgic (ý tưởng → phân cảnh → prompt ảnh → chốt ảnh → prompt video → clip → video → đăng). Dùng khi người dùng gọi /dream, muốn tạo tập mới, hoặc làm tiếp một tập đang dở.
---

# /dream

Mỗi lần được gọi: **xác định tập → xem giai đoạn → làm đúng MỘT bước → dừng và nói người dùng việc tiếp theo.** AI ghi nhớ qua file, không qua cuộc trò chuyện.

## 1. Xác định tập
- `/dream epNNN` → tập đó.
- `/dream` không đối số → đọc `library/episode-log.md`, liệt kê các tập chưa `published` kèm giai đoạn (`python tools/episode_state.py phase <ep>`), hỏi: làm tiếp tập nào hay tạo tập mới.
- Tạo tập mới: chạy `python tools/new_episode.py --dry-run` 3 lần (seed khác nhau) đưa 3 ý tưởng; người dùng chọn số, gõ "random", hoặc gõ ý riêng. Tạo bằng `python tools/new_episode.py --series <id> --object <id> --verb <id> --seed <seed>` (ý riêng: thêm `--idea "<ý tưởng>"`). Sau đó tiếp tục bước 2 ngay.

## 2. Xem giai đoạn
`python tools/episode_state.py phase <ep>` → `{phase, by, message}`. Làm theo bảng:

| phase | Làm |
|---|---|
| `idea` | Chạy `plan <ep>`; viết phân cảnh theo `library/guides/storyboard.md`; ghi JSON ra file tạm (vd. `episodes/<ep>/.ai-storyboard.json`); `apply <ep> storyboard <file>`; in **bảng phân cảnh** (dưới) rồi hỏi "ok hay sửa gì?" |
| `storyboard` | Người dùng trả "ok" → `approve <ep>` rồi làm luôn bước `image_prompts`. Người dùng góp ý → sửa JSON, `apply` lại, in lại bảng |
| `image_prompts` | Viết theo `library/guides/image-prompts.md` → `apply <ep> image_prompts <file>` → `python tools/export_prompts.py <ep>` → nhắc mở Studio hoặc `prompts.md`, tạo ảnh, thả vào và **Chốt** (hoặc `lock <ep> all`) |
| `images` | Nói cảnh nào chưa chốt (từ `message`). Không tự chốt hộ trừ khi người dùng yêu cầu |
| `video_prompts` | **Mở xem từng ảnh đã chốt** (`show <ep>` → `locked_image`), viết theo `library/guides/video-prompts.md` (chỉ cảnh thiếu hoặc `motion_stale`) → `apply <ep> video_prompts <file>` → `export_prompts.py` → nhắc tạo clip dài ≥ `scene_seconds + 0.5` giây |
| `clips` | Nói cảnh nào thiếu clip |
| `final` | Nếu chưa có `final.mp4`: đề nghị `python tools/assemble.py <ep> --preview --metronome` để kiểm tra nhịp, rồi bản cuối `python tools/assemble.py <ep>`. Nếu đã có: đưa tiêu đề/mô tả/hashtag, nhắc chọn nhạc trong app và **kéo tới `start_offset`** của hồ sơ nhạc, rồi dán link vào Studio |
| `published` | Báo hoàn tất |

## Bảng phân cảnh (in cho người dùng duyệt)
```
01 · wide   · 3.0s · Ông Moon trên xe nâng, đánh bóng mặt trăng khổng lồ
02 · hands  · 3.0s · bàn tay xoay máy đánh bóng, bụi trăng lấp lánh
...
Tổng: 6 cảnh × 3.0s = 18.0s · 4 phách/cảnh · hard cut
```

## Quy tắc
- Mỗi lần chỉ làm một bước rồi dừng. Không bỏ qua bước; ảnh và clip là bắt buộc.
- Lỗi từ `apply` (in "Lỗi: ...") → sửa JSON theo nội dung lỗi và `apply` lại một lần; vẫn lỗi thì báo người dùng.
- `Lưu ý: ... giữ ... bạn đã sửa tay` → báo người dùng; chỉ dùng `--overwrite-edited` khi họ đồng ý.
- Lỗi "vừa được cập nhật ở nơi khác" → đọc lại tập (`show`) rồi làm lại.
- Xóa file JSON tạm sau khi `apply` thành công.
- Trả lời người dùng bằng tiếng Việt.
````

- [ ] **Step 6: Tạo `.agent/workflows/dream.md`, sửa `new-episode.md` và `weekly-batch.md`**

`.agent/workflows/dream.md`:
```markdown
---
description: Làm một tập Dreamnostalgic theo từng bước (gọi /dream hoặc /dream epNNN)
---

Làm theo skill **dream** (`.agent/skills/dream/SKILL.md`). Mỗi lần gọi chỉ làm một bước rồi dừng.
```

`.agent/workflows/new-episode.md` (thay toàn bộ):
```markdown
---
description: Tạo tập mới (lối tắt của /dream)
---

Làm theo skill **dream**, bắt đầu bằng phần "Tạo tập mới".
```

`.agent/workflows/weekly-batch.md` (thay toàn bộ):
```markdown
---
description: Lên kế hoạch và viết sẵn phân cảnh + prompt ảnh cho nhiều tập (mặc định 7)
---

# /weekly-batch

1. Đọc `library/episode-log.md` và `library/series.json`. Hỏi số tập (mặc định 7).
2. Lập lịch đa dạng: không quá 2 tập liền cùng series, không lặp vật thể trong tuần, có ít nhất 1 tập Phố Mơ. Trình bảng (ngày, series, ý tưởng 1 dòng) để người dùng duyệt.
3. Với từng tập: tạo tập (`python tools/new_episode.py ...`), viết phân cảnh theo skill **dream** và in bảng phân cảnh. Đợi người dùng duyệt **tất cả** bảng (có thể duyệt một lần "ok cả 7").
4. Sau khi duyệt: `approve` từng tập, viết prompt ảnh, `export_prompts.py`.
5. Tạo `episodes/batch-<YYYY-MM-DD>.md`: bảng ep_id, tiêu đề, số cảnh, link `prompts.md`; tổng số ảnh và clip cần tạo trong tuần.
6. Prompt video viết sau, khi từng tập đã chốt đủ ảnh (gọi `/dream epNNN`).
```

- [ ] **Step 7: Cập nhật các skill cũ**

Xóa thư mục `.agent/skills/episode-script/`.

`.agent/skills/prompt-writer/SKILL.md` (thay toàn bộ):
```markdown
---
name: prompt-writer
description: Viết hoặc viết lại prompt ảnh / prompt video cho một hoặc vài cảnh, kể cả khi người dùng đổi công cụ AI. Dùng khi người dùng yêu cầu sửa prompt cụ thể ngoài quy trình /dream.
---

# Viết prompt cho cảnh

- Prompt ảnh: theo `library/guides/image-prompts.md`. Prompt video: theo `library/guides/video-prompts.md` (luôn xem ảnh đã chốt).
- Ghi kết quả bằng `python tools/episode_state.py apply <ep> image_prompts|video_prompts <file.json>`; người dùng đã sửa tay thì chỉ thêm `--overwrite-edited` khi họ đồng ý.
- Đổi công cụ: viết lại mọi cảnh của tập đang làm theo tool guide mới, rồi `python tools/export_prompts.py <ep>`.
```

`.agent/skills/seo-metadata/SKILL.md` (thay toàn bộ):
```markdown
---
name: seo-metadata
description: Viết lại tiêu đề, mô tả, hashtag cho Shorts Dreamnostalgic. Dùng khi người dùng muốn đổi thông tin đăng.
---

# Tiêu đề, mô tả, hashtag

Theo `library/guides/seo.md`. Đưa 3 phương án tiêu đề cho người dùng chọn, rồi ghi bằng
`python tools/episode_state.py apply <ep> seo <file.json>` với `{"title": ..., "description": ..., "hashtags": [...]}`.
Nhắc người dùng khai báo nội dung AI trung thực khi YouTube hỏi.
```

`.agent/skills/assemble-video/SKILL.md`: thay bảng "Lệnh" bằng:
```markdown
| Mục đích | Lệnh |
|---|---|
| Xem nhanh + kiểm tra nhịp | `python tools/assemble.py <ep_id> --preview --metronome` |
| Bản cuối 1080×1920 (không nhạc) | `python tools/assemble.py <ep_id>` |
| Giữ âm thanh gốc của clip | `... --clip-audio` |
| Nhạc có quyền dùng | `... --music music/<file>.mp3` |
| Lật ngang 1 clip | `python tools/flip.py <ep_id> s03` |
```
và thay đoạn "Độ dài mỗi cảnh = `dur`..." bằng:
```markdown
- Độ dài cảnh tính từ lưới phách (hồ sơ nhạc + `beats_per_scene`), mọi cảnh bằng nhau, chỉ hard cut. Mỗi clip bỏ 0,5s đầu; thiếu ≤10% tự làm chậm; thiếu hơn → báo cảnh cần tạo lại clip.
```

- [ ] **Step 8: Cập nhật rules và README**

Trong `.agent/rules/dreamnostalgic.md`, thay dòng `- Công thức cảnh: ...` bằng:
```markdown
- Công thức cảnh: người lao động bình thường + hành động thủ công tỉ mỉ + vật thể trong mơ + bối cảnh hoài niệm + ánh sáng ấm. Mọi cảnh **ngang hàng** (không hook/reveal), dài bằng nhau (~3–4s), chỉ **hard cut**, cắt đúng phách nhạc (hồ sơ nhạc trong `library/music-profiles.json`).
```
Thay dòng `- Quy trình KHÔNG cố định. ...` bằng:
```markdown
- Quy trình làm tập: skill **dream** (`/dream`). Mỗi cảnh **bắt buộc** có ảnh đã chốt và clip. Ảnh/clip tạo ở bất kỳ web nào; video có thể dựng bằng Studio/`assemble.py` hoặc ghép nơi khác (CapCut) sau khi đủ ảnh chốt và clip. Video xuất **không nhạc**; người dùng chọn nhạc trong app khi đăng.
- Mọi thay đổi `script.json` đi qua `python tools/episode_state.py` (có kiểm tra và chặn ghi đè). Hướng dẫn sáng tạo nằm ở `library/guides/`.
```

Trong `README.md`, thay mục `## Quy trình một tập (linh hoạt)` (đến hết danh sách "Không bước nào bắt buộc") bằng:
```markdown
## Quy trình một tập (/dream)
Gọi `/dream` trong Antigravity (hoặc `/dream ep003` để làm tiếp). Mỗi lần gọi, AI làm đúng một bước rồi dừng:

ý tưởng → **phân cảnh** (bạn duyệt) → prompt ảnh → **bạn tạo & chốt ảnh** → prompt video (AI xem ảnh đã chốt) → **bạn tạo clip** → dựng (hard cut theo nhịp) → đăng (chọn nhạc trong app, kéo tới `start_offset`).

- Mọi cảnh dài bằng nhau (~3–4s), 5–6 cảnh, ~15–20s, cắt đúng phách đoạn intro của bài nhạc (`library/music-profiles.json`).
- Mỗi cảnh bắt buộc có ảnh đã chốt và clip; ảnh/clip làm ở web nào cũng được.
- Kiểm tra khớp nhịp: `python tools/assemble.py ep003 --preview --metronome`.
- Trạng thái tập: `python tools/episode_state.py phase ep003`.
```

- [ ] **Step 9: Kiểm tra tham chiếu cũ**

Run: `python -c "import pathlib;print([str(p) for p in pathlib.Path('.agent').rglob('*.md') if 'episode-script' in p.read_text(encoding='utf-8')])"`
Expected: `[]` (không còn skill/workflow nào tham chiếu skill đã xóa)

Run: `python -c "import pathlib;print(pathlib.Path('.agent/skills/episode-script').exists())"`
Expected: `False`

Run: `python -m unittest discover -s tests -v`
Expected: tất cả OK

- [ ] **Step 10: Commit**

```bash
git add -A .agent library/guides README.md
git commit -m "docs(agent): /dream skill, shared creative guides, updated rules"
```

---

## Kiểm tra cuối Đợt 1 (thủ công, cùng người dùng)

- [ ] `python tools/episode_state.py plan` trên một tập mới in `scenes: 6`, `beats_per_scene: 4`, `cuts: [0.0, 3.0, ..., 18.0]` với hồ sơ mặc định.
- [ ] Mở Studio (`Mo-Studio.bat`): trang Tổng quan, Các tập, một tập có phân cảnh mới đều hiển thị không lỗi (cảnh hiện `3.0s`, nhãn `4 phách`).
- [ ] Trong Antigravity gõ `/dream`: agent liệt kê tập dở hoặc đưa 3 ý tưởng.
