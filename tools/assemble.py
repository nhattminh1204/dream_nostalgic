"""Dựng final.mp4 từ clips/sNN.* theo script.json: cắt độ dài, crop 9:16, film look, nhạc, endcard.

  python tools/assemble.py ep001
  python tools/assemble.py ep001 --preview            # 540x960, nhanh để duyệt
  python tools/assemble.py ep001 --music music/calm-01.mp3
  python tools/assemble.py ep001 --clip-audio         # giữ âm thanh gốc của clip (vd. Veo)

Film look: library/lut/film.cube nếu có, nếu không dùng bộ lọc mặc định bên dưới.
Endcard: library/brand/endcard.png (PNG nền trong suốt) hiện ở 2.5s cuối nếu có.
"""
import argparse
import subprocess
import sys
from pathlib import Path

from common import LIB, ROOT, config, episode_dir, ffmpeg_exe, load_json, probe

# Lift blacks, roll off highlights, desaturate, grain, vignette.
FILM_LOOK = ("curves=all='0/0.06 0.5/0.5 1/0.95',"
             "eq=saturation=0.87:contrast=0.97,"
             "noise=alls=7:allf=t,"
             "vignette=angle=PI/5")
CLIP_EXTS = (".mp4", ".mov", ".webm", ".mkv")
ENDCARD_SECONDS = 2.5


def find_clip(clips_dir, n):
    for ext in CLIP_EXTS:
        p = clips_dir / f"s{n:02d}{ext}"
        if p.exists():
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep_id")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--music")
    ap.add_argument("--clip-audio", action="store_true")
    args = ap.parse_args()

    cfg = config()
    d = episode_dir(args.ep_id)
    s = load_json(d / "script.json")
    shots = sorted(s["shots"], key=lambda sh: sh["n"])
    if not shots:
        sys.exit("script.json chưa có shots.")

    missing = [f"clips/s{sh['n']:02d}.mp4" for sh in shots if not find_clip(d / "clips", sh["n"])]
    if missing:
        sys.exit("Thiếu clip: " + ", ".join(missing))

    W, H = (540, 960) if args.preview else (cfg["output"]["width"], cfg["output"]["height"])
    fps = cfg["output"]["fps"]
    music = args.music or s.get("music") or cfg.get("default_music")
    clip_audio = args.clip_audio or (cfg.get("use_clip_audio") and not music)

    inputs, vf, af = [], [], []
    total = 0.0
    for i, sh in enumerate(shots):
        clip = find_clip(d / "clips", sh["n"])
        clip_dur, has_audio = probe(clip)
        dur = min(float(sh["dur"]), clip_dur) if clip_dur else float(sh["dur"])
        total += dur
        inputs += ["-t", f"{dur:.3f}", "-i", str(clip)]
        vf.append(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                  f"fps={fps},setsar=1,format=yuv420p[v{i}]")
        if clip_audio:
            if has_audio:
                af.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                          f"atrim=0:{dur:.3f},asetpts=PTS-STARTPTS[a{i}]")
            else:
                af.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{dur:.3f}[a{i}]")

    n = len(shots)
    look = FILM_LOOK
    lut = LIB / "lut" / "film.cube"
    if lut.exists():
        look = f"lut3d=file='{lut.relative_to(ROOT).as_posix()}'," + look
    grade = load_json(LIB / "palettes.json").get(s["palette"], {}).get("grade")
    if grade:
        look += "," + grade

    graph = vf + af
    graph.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vc]")
    graph.append(f"[vc]{look}[vg]")
    vout = "[vg]"

    next_input = n
    endcard = LIB / "brand" / "endcard.png"
    if endcard.exists():
        start = max(total - ENDCARD_SECONDS, 0)
        inputs += ["-loop", "1", "-framerate", str(fps), "-t", f"{total:.3f}", "-i", str(endcard)]
        graph.append(f"[{next_input}:v]scale={int(W * 0.22)}:-1,format=rgba,"
                     f"fade=in:st={start:.2f}:d=0.6:alpha=1[logo]")
        graph.append(f"{vout}[logo]overlay=(W-w)/2:H*0.80:enable='gte(t,{start:.2f})'[vl]")
        vout = "[vl]"
        next_input += 1

    aout = None
    if clip_audio:
        graph.append("".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[ac]")
        aout = "[ac]"
    if music:
        music_path = (ROOT / music) if not Path(music).is_absolute() else Path(music)
        if not music_path.exists():
            sys.exit(f"Không thấy file nhạc: {music_path}")
        inputs += ["-stream_loop", "-1", "-i", str(music_path)]
        graph.append(f"[{next_input}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,"
                     f"afade=t=out:st={max(total - 1.5, 0):.3f}:d=1.5,loudnorm=I=-14:TP=-1.5,"
                     f"aformat=sample_rates=48000:channel_layouts=stereo[am]")
        if aout:
            graph.append(f"{aout}volume=0.35[acq];[am][acq]amix=inputs=2:duration=first:normalize=0[amix]")
            aout = "[amix]"
        else:
            aout = "[am]"

    out = d / ("preview.mp4" if args.preview else "final.mp4")
    graph_file = d / ".filtergraph.txt"
    graph_file.write_text(";\n".join(graph), encoding="utf-8")

    cmd = [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", *inputs,
           "-filter_complex_script", str(graph_file), "-map", vout]
    if aout:
        cmd += ["-map", aout, "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast" if args.preview else "medium",
            "-crf", "23" if args.preview else "18", "-pix_fmt", "yuv420p",
            "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)]

    print(f"Dựng {n} cảnh, {total:.1f}s, {W}x{H}" + (f", nhạc: {music}" if music else ", không nhạc"))
    r = subprocess.run(cmd, cwd=ROOT)
    graph_file.unlink(missing_ok=True)
    if r.returncode:
        sys.exit("ffmpeg lỗi (xem thông báo phía trên).")
    print(f"Xong: {out}")
    if not aout:
        print("Lưu ý: video không có âm thanh, thêm nhạc trong app YouTube Shorts khi đăng.")


if __name__ == "__main__":
    main()
