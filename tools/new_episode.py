"""Tạo tập mới: chọn tổ hợp chất liệu chưa dùng, tạo episodes/epNNN/ với script.json khung.

Ví dụ:
  python tools/new_episode.py                         # series ngẫu nhiên
  python tools/new_episode.py --series night-shift
  python tools/new_episode.py --series pho-mo --object rain --verb wind
  python tools/new_episode.py --dry-run               # chỉ in tổ hợp, không tạo file
"""
import argparse
import json
import random
import re

from common import EPISODES, LIB, LOG, by_id, config, load_json, save_json


def used_pairs():
    """(series, verb, object) đã có trong episode-log.md."""
    pairs = set()
    for line in LOG.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and re.fullmatch(r"ep\d+", cells[0]):
            pairs.add((cells[1], cells[2], cells[3]))
    return pairs


def next_id():
    nums = [int(p.name[2:]) for p in EPISODES.glob("ep[0-9]*") if p.name[2:].isdigit()]
    return f"ep{max(nums, default=0) + 1:03d}"


def make_title(pattern, verb, obj):
    return pattern.format(verb_title=verb["ing"], verb_past=verb["s"], object=obj["short"], emoji=obj["emoji"])


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series")
    ap.add_argument("--object")
    ap.add_argument("--verb")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--idea", default="", help="ý tưởng tự gõ (AI ưu tiên khi viết phân cảnh)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true", help="in kết quả dạng JSON (dùng cho giao diện web)")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    mats = load_json(LIB / "materials.json")
    series_list = load_json(LIB / "series.json")
    series_by = by_id(series_list)
    objects, verbs = by_id(mats["dream_objects"]), by_id(mats["verbs"])
    settings, times = by_id(mats["settings"]), by_id(mats["times"])
    used = used_pairs()

    series = series_by[args.series] if args.series else rng.choice(series_list)
    candidates = [
        (v, o)
        for o in series["objects"] if not args.object or o == args.object
        for v in objects[o]["verbs"] if not args.verb or v == args.verb
        if (series["id"], v, o) not in used
    ]
    if not candidates:
        raise SystemExit(f"Hết tổ hợp chưa dùng cho series '{series['id']}' với bộ lọc này. "
                         "Thêm vật thể/động từ vào library/materials.json hoặc series.json.")
    verb_id, obj_id = rng.choice(candidates)
    verb, obj = verbs[verb_id], objects[obj_id]
    setting = settings[rng.choice(series["settings"])]
    time = times[rng.choice(series["times"])]
    title = make_title(rng.choice(series["title_patterns"]), verb, obj)

    result = {
        "series": series["id"], "series_name": series["name"], "verb": verb_id, "object": obj_id,
        "setting": setting["id"], "time": time["id"], "title": title,
        "logline_vi": f"{verb['vi'].capitalize()} {obj['vi']}, {setting['vi']}, {time['vi']}",
    }
    if not args.json:
        print(f"Series : {series['name']} ({series['id']})")
        print(f"Concept: {verb['vi']} {obj['vi']} | {setting['vi']} | {time['vi']}")
        print(f"Title  : {title}")
    if args.dry_run:
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        return

    cfg = config()
    ep_id = next_id()
    d = EPISODES / ep_id
    for sub in ("images", "clips"):
        (d / sub).mkdir(parents=True, exist_ok=True)

    save_json(d / "script.json", build_script(
        ep_id, series, verb_id, obj_id, setting["id"], time["id"], title,
        result["logline_vi"], args.idea.strip(), cfg))

    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"| {ep_id} | {series['id']} | {verb_id} | {obj_id} | {title} | draft | |\n")

    if args.json:
        print(json.dumps({**result, "id": ep_id}, ensure_ascii=False))
    else:
        print(f"\nĐã tạo {d}\nBước tiếp: gọi /dream {ep_id} để viết phân cảnh.")


if __name__ == "__main__":
    main()
