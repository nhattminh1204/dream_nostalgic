"""Lật ngang clip/ảnh trong một tập (dùng khi muốn đảo hướng bố cục cảnh của chính bạn).

  python tools/flip.py ep001 s03          # lật clips/s03.* tại chỗ (giữ bản gốc .orig)
"""
import subprocess
import sys

from assemble import find_clip
from common import episode_dir, ffmpeg_exe


def main():
    if len(sys.argv) != 3:
        sys.exit("Cách dùng: python tools/flip.py <ep_id> sNN")
    d = episode_dir(sys.argv[1])
    clip = find_clip(d / "clips", int(sys.argv[2].lstrip("s")))
    if not clip:
        sys.exit("Không tìm thấy clip.")
    orig = clip.with_name(clip.stem + ".orig" + clip.suffix)
    if not orig.exists():
        clip.rename(orig)
    subprocess.run([ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(orig),
                    "-vf", "hflip", "-c:a", "copy", str(clip)], check=True)
    print(f"Đã lật: {clip} (gốc: {orig.name})")


if __name__ == "__main__":
    main()
