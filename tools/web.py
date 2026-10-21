"""Giao diện web chạy trên máy: quản lý tập, copy prompt, kéo-thả ảnh/clip, dựng video.

  python tools/web.py               # mở http://127.0.0.1:8765
  python tools/web.py --port 9000 --no-browser

Chỉ lắng nghe trên 127.0.0.1 (máy bạn); không đưa gì lên mạng.
"""
import argparse
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from assemble import find_clip
from common import EPISODES, LIB, LOG, ROOT, by_id, config, load_json, save_json

WEB = ROOT / "web"
TOOLS = ROOT / "tools"
EP_RE = re.compile(r"^ep\d{3,}$")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
CLIP_EXTS = (".mp4", ".mov", ".webm", ".mkv")
SERVABLE = (EPISODES, LIB)
EDITABLE_META = ("title", "description", "hashtags", "status", "link", "music")
EDITABLE_CONFIG = ("image_tool", "video_tool", "default_music", "use_clip_audio")


def find_image(d, n):
    for ext in IMAGE_EXTS:
        p = d / "images" / f"s{n:02d}{ext}"
        if p.exists():
            return p
    return None


def rel(p):
    return p.relative_to(ROOT).as_posix() if p else None


def run_tool(script, *args):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, str(TOOLS / script), *args], cwd=ROOT, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


def episode_summary(d, full=False):
    s = load_json(d / "script.json")
    shots = []
    for sh in sorted(s.get("shots", []), key=lambda x: x["n"]):
        item = {**sh} if full else {"n": sh["n"]}
        item["image"] = rel(find_image(d, sh["n"]))
        item["clip"] = rel(find_clip(d / "clips", sh["n"]))
        shots.append(item)
    out = {k: v for k, v in s.items() if k != "shots"} if full else {
        k: s.get(k) for k in ("id", "series", "title", "status", "palette", "link")}
    out["logline_vi"] = s.get("concept", {}).get("logline_vi", "")
    out["updated"] = int(max(p.stat().st_mtime for p in [d / "script.json", *d.glob("*/*"), *d.glob("*.mp4")]))
    out["shots"] = shots
    for name in ("final.mp4", "preview.mp4"):
        p = d / name
        out[name.split(".")[0]] = {"path": rel(p), "mtime": int(p.stat().st_mtime)} if p.exists() else None
    return out


def update_log(ep_id, title=None, status=None, link=None):
    lines = LOG.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == ep_id and len(cells) >= 7:
            if title is not None:
                cells[4] = title.replace("|", "/")
            if status is not None:
                cells[5] = status
            if link is not None:
                cells[6] = link
            lines[i] = "| " + " | ".join(cells) + " |"
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")


def meta():
    mats = load_json(LIB / "materials.json")
    objects, verbs = by_id(mats["dream_objects"]), by_id(mats["verbs"])
    series = []
    for s in load_json(LIB / "series.json"):
        series.append({
            "id": s["id"], "name": s["name"], "vi": s["vi"], "palette": s["palette"],
            "characters": s["characters"],
            "objects": [{"id": o, "vi": objects[o]["vi"], "emoji": objects[o]["emoji"],
                         "verbs": [{"id": v, "vi": verbs[v]["vi"]} for v in objects[o]["verbs"]]}
                        for o in s["objects"]],
        })
    characters = []
    for md in sorted((LIB / "characters").glob("*.md")):
        ref = next((p for p in (LIB / "characters" / md.stem).glob("ref-sheet.*")), None)
        head = md.read_text(encoding="utf-8").splitlines()
        characters.append({"id": md.stem, "name": head[0].lstrip("# ").split(" (")[0] if head else md.stem,
                           "ref": rel(ref), "md": md.read_text(encoding="utf-8")})
    tools = sorted(p.stem for p in (LIB / "tool-guides").glob("*.md") if p.stem != "README")
    music = sorted(rel(p) for p in (ROOT / "music").glob("*") if p.suffix.lower() in (".mp3", ".wav", ".m4a", ".aac", ".ogg"))
    brand = {"endcard": (LIB / "brand" / "endcard.png").exists(), "lut": (LIB / "lut" / "film.cube").exists()}
    return {"series": series, "palettes": load_json(LIB / "palettes.json"), "characters": characters,
            "tools": tools, "music": music, "brand": brand, "config": config()}


class Handler(BaseHTTPRequestHandler):
    server_version = "Dreamnostalgic/1.0"

    def log_message(self, fmt, *args):
        if "/api/" in (args[0] if args else ""):
            sys.stderr.write("%s\n" % (fmt % args))

    # ---------- helpers ----------
    def send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def error(self, msg, code=400):
        self.send_json({"error": msg}, code)

    def read_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def episode(self, ep_id):
        if not EP_RE.match(ep_id or ""):
            return None
        d = EPISODES / ep_id
        return d if (d / "script.json").exists() else None

    def send_file(self, path):
        size = path.stat().st_size
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        start, end = 0, size - 1
        rng = self.headers.get("Range")
        m = re.match(r"bytes=(\d*)-(\d*)", rng or "")
        if m and (m[1] or m[2]):
            if m[1]:
                start = int(m[1])
                end = int(m[2]) if m[2] else end
            else:
                start = max(size - int(m[2]), 0)
            end = min(end, size - 1)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        with path.open("rb") as f:
            f.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = f.read(min(1 << 20, remaining))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (ConnectionResetError, BrokenPipeError):
                    return
                remaining -= len(chunk)

    # ---------- GET ----------
    def do_GET(self):
        url = urlparse(self.path)
        parts = [p for p in url.path.split("/") if p]

        if url.path in ("/", "/index.html"):
            return self.send_file(WEB / "index.html")
        if parts[:1] == ["files"]:
            target = (ROOT / unquote("/".join(parts[1:]))).resolve()
            if any(target.is_relative_to(base.resolve()) for base in SERVABLE) and target.is_file():
                return self.send_file(target)
            return self.error("not found", 404)
        if parts == ["api", "meta"]:
            return self.send_json(meta())
        if parts == ["api", "episodes"]:
            eps = [episode_summary(d) for d in sorted(EPISODES.glob("ep*"), reverse=True)
                   if (d / "script.json").exists()]
            return self.send_json(eps)
        if len(parts) == 3 and parts[:2] == ["api", "episodes"]:
            d = self.episode(parts[2])
            return self.send_json(episode_summary(d, full=True)) if d else self.error("không có tập này", 404)
        if parts == ["api", "suggest"]:
            q = parse_qs(url.query)
            out = []
            for _ in range(3):
                seed = str(int(time.time() * 1000) % 1_000_000 + len(out) * 7919)
                args = ["--dry-run", "--json", "--seed", seed]
                for k in ("series", "object", "verb"):
                    if q.get(k, [""])[0]:
                        args += [f"--{k}", q[k][0]]
                code, text = run_tool("new_episode.py", *args)
                if code:
                    return self.error(text.splitlines()[-1] if text else "lỗi")
                out.append({**json.loads(text.splitlines()[-1]), "seed": seed})
            return self.send_json(out)
        return self.error("not found", 404)

    # ---------- POST / PUT ----------
    def do_POST(self):
        parts = [p for p in urlparse(self.path).path.split("/") if p]

        if parts == ["api", "config"]:
            body = self.read_json()
            cfg = config()
            for k in EDITABLE_CONFIG:
                if k in body:
                    cfg[k] = body[k]
            save_json(ROOT / "config.json", cfg)
            return self.send_json(cfg)

        if parts == ["api", "episodes"]:
            body = self.read_json()
            args = ["--json"]
            for k in ("series", "object", "verb", "seed"):
                if body.get(k):
                    args += [f"--{k}", str(body[k])]
            code, text = run_tool("new_episode.py", *args)
            if code:
                return self.error(text.splitlines()[-1] if text else "lỗi")
            return self.send_json(json.loads(text.splitlines()[-1]))

        if len(parts) == 4 and parts[:2] == ["api", "episodes"]:
            d = self.episode(parts[2])
            if not d:
                return self.error("không có tập này", 404)
            action = parts[3]
            if action == "meta":
                body = self.read_json()
                s = load_json(d / "script.json")
                for k in EDITABLE_META:
                    if k in body:
                        s[k] = body[k]
                save_json(d / "script.json", s)
                update_log(d.name, title=body.get("title"), status=body.get("status"), link=body.get("link"))
                return self.send_json({"ok": True})
            if action == "assemble":
                body = self.read_json()
                args = [d.name] + (["--preview"] if body.get("preview") else [])
                if body.get("clip_audio"):
                    args.append("--clip-audio")
                code, text = run_tool("assemble.py", *args)
                return self.send_json({"ok": code == 0, "log": text})
            if action == "export":
                code, text = run_tool("export_prompts.py", d.name)
                return self.send_json({"ok": code == 0, "log": text})
            if action == "open":
                if hasattr(os, "startfile"):
                    os.startfile(d)
                else:
                    subprocess.Popen(["xdg-open", str(d)])
                return self.send_json({"ok": True})
        return self.error("not found", 404)

    def do_PUT(self):
        # PUT /api/episodes/<ep>/upload?kind=image|clip&n=1&ext=png  (body = raw file)
        # PUT /api/episodes/<ep>/upload?kind=final&ext=mp4           (video đã dựng ở nơi khác)
        url = urlparse(self.path)
        parts = [p for p in url.path.split("/") if p]
        if not (len(parts) == 4 and parts[:2] == ["api", "episodes"] and parts[3] == "upload"):
            return self.error("not found", 404)
        d = self.episode(parts[2])
        if not d:
            return self.error("không có tập này", 404)
        q = parse_qs(url.query)
        kind = q.get("kind", [""])[0]
        ext = "." + q.get("ext", [""])[0].lower().lstrip(".")
        try:
            n = int(q.get("n", ["0"])[0])
        except ValueError:
            n = 0
        # Giữ bản cũ thay vì ghi đè: s01.png -> s01_v<timestamp>.png
        stamp = time.strftime("%Y%m%d-%H%M%S")
        if kind == "final":
            if ext != ".mp4":
                return self.error("Video hoàn chỉnh cần là file .mp4")
            target = d / "final.mp4"
            if target.exists():
                target.rename(d / f"final_v{stamp}.mp4")
        else:
            allowed = IMAGE_EXTS if kind == "image" else CLIP_EXTS if kind == "clip" else ()
            if ext not in allowed or not 1 <= n <= 99:
                return self.error(f"File không hợp lệ. Ảnh: {', '.join(IMAGE_EXTS)} · Clip: {', '.join(CLIP_EXTS)}")
            folder = d / ("images" if kind == "image" else "clips")
            folder.mkdir(exist_ok=True)
            for old_ext in allowed:
                old = folder / f"s{n:02d}{old_ext}"
                if old.exists():
                    old.rename(folder / f"s{n:02d}_v{stamp}{old_ext}")
            target = folder / f"s{n:02d}{ext}"
        remaining = int(self.headers.get("Content-Length") or 0)
        with target.open("wb") as f:
            while remaining > 0:
                chunk = self.rfile.read(min(1 << 20, remaining))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
        return self.send_json({"ok": True, "path": rel(target)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    EPISODES.mkdir(exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}"
    print(f"Dreamnostalgic Studio: {url}  (Ctrl+C để tắt)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
