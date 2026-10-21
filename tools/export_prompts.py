"""Xuất episodes/<id>/prompts.md: bảng prompt để copy-paste vào app ảnh / video.

  python tools/export_prompts.py ep001
"""
import sys

from common import LIB, episode_dir, load_json


def main():
    if len(sys.argv) != 2:
        sys.exit("Cách dùng: python tools/export_prompts.py <ep_id>")
    d = episode_dir(sys.argv[1])
    s = load_json(d / "script.json")
    if not s["shots"]:
        sys.exit("script.json chưa có shots. Chạy skill episode-script trước.")

    palette = load_json(LIB / "palettes.json")[s["palette"]]
    total = sum(sh["dur"] for sh in s["shots"])
    out = [
        f"# {s['id']}: {s['title']}",
        "",
        f"- Series: `{s['series']}` · Palette: **{palette['name']}** · Tổng: ~{total}s · {len(s['shots'])} cảnh",
        f"- Công cụ ảnh: `{s['image_tool']}` · Công cụ video: `{s['video_tool']}`",
        f"- Ý tưởng: {s['concept']['logline_vi']}",
        "",
        "## Ảnh tham chiếu cần đính kèm",
    ]
    for c in s["characters"]:
        out.append(f"- `{c}`: library/characters/{c}/ref-sheet.png")
    out.append("- Style anchor (nếu có): library/style-anchors/")
    out.append("")

    for sh in s["shots"]:
        n = f"s{sh['n']:02d}"
        out += [
            f"## Cảnh {sh['n']}: {sh.get('role', '')} · {sh.get('angle', '')} · {sh['dur']}s",
            "",
            f"> {sh.get('scene_vi', '')}",
            "",
            f"Nhân vật: {', '.join(sh.get('characters', [])) or 'không'}",
            "",
            "**Prompt ảnh**",
            "```",
            sh["image_prompt"],
            "```",
        ]
        if sh.get("negative"):
            out += ["**Negative**", "```", sh["negative"], "```"]
        out += [
            "**Prompt chuyển động**",
            "```",
            sh["motion_prompt"],
            "```",
            f"Lưu ảnh: `images/{n}.png`, lưu clip: `clips/{n}.mp4`",
            "",
        ]

    (d / "prompts.md").write_text("\n".join(out), encoding="utf-8")
    print(f"Đã xuất {d / 'prompts.md'}")


if __name__ == "__main__":
    main()
