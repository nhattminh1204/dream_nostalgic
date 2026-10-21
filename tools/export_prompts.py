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
