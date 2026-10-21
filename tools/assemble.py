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
from episode_state import find_clip  # noqa: F401  (mã cũ import find_clip từ đây)

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
        freq, amp = (1500.0, 0.6) if k % 4 == 0 else (1000.0, 0.4)
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
    for i, (clip, start, factor, need, _) in enumerate(plans):
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
        secs = es.shot_seconds(es.load(d))
        if secs:
            print(f"Dựng {len(secs)} cảnh × {secs[0]:.2f}s = {sum(secs):.2f}s"
                  + (" · tiếng gõ nhịp" if args.metronome else ""))
        out = build(d, args.preview, args.clip_audio, args.music, args.metronome)
    except (AssembleError, es.StateError) as e:
        sys.exit(str(e))
    print(f"Xong: {out}")
    if not (args.metronome or args.music or args.clip_audio):
        print("Video không có nhạc: chọn nhạc trong app khi đăng (kéo tới start_offset của hồ sơ nhạc).")


if __name__ == "__main__":
    main()
