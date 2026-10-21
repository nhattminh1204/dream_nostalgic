# Dreamnostalgic: bộ sản xuất YouTube Shorts

Những nghề không có thật, ở một tuổi thơ chưa từng tồn tại. Video AI dọc 9:16, 25–35s.

## Bắt đầu nhanh
1. Cài Python 3.10+ rồi chạy: `pip install -r tools/requirements.txt` (cung cấp ffmpeg nếu máy chưa có).
2. Mở thư mục này trong **Antigravity**. Agent tự đọc `.agent/rules`, `.agent/skills`, `.agent/workflows`.
   > Nếu Antigravity của bạn dùng tên thư mục khác (vd. `.agents/`), đổi tên `.agent/` cho khớp.
3. Chọn công cụ trong `config.json`: `image_tool` / `video_tool` = tên file trong `library/tool-guides/` (vd. `nano-banana`, `veo`, `kling`). Để trống = prompt chung.
4. Tạo ảnh mẫu 3 nhân vật bằng prompt trong `library/characters/*.md`, lưu vào `library/characters/<id>/ref-sheet.png`.
5. Gõ `/new-episode` trong Antigravity.

## Cấu trúc
```
.agent/rules/        quy tắc nền (luôn áp dụng)
.agent/skills/       dream · prompt-writer · assemble-video · seo-metadata · qc-review
.agent/workflows/    /dream · /new-episode · /weekly-batch
library/             kiến thức: chất liệu, series, bảng màu, nhân vật, từ vựng prompt, hướng dẫn từng công cụ, nhật ký tập
  guides/            hướng dẫn sáng tạo dùng chung: phân cảnh, prompt ảnh, prompt video, SEO
  music-profiles.json  hồ sơ nhạc (BPM, start_offset, độ dài intro) để cắt đúng phách
  characters/<id>/   ảnh ref-sheet của nhân vật (bạn tạo)
  style-anchors/     ảnh chuẩn phong cách (bạn tạo, KHÔNG dùng khung hình từ video tải về)
  brand/endcard.png  logo cuối video (tùy chọn, PNG nền trong suốt)
  lut/film.cube      LUT film look (tùy chọn)
music/               nhạc bạn có quyền dùng
episodes/epNNN/      script.json · prompts.md · images/ · clips/ · final.mp4
tools/               script Python (không phụ thuộc IDE); episode_state.py là bộ não của /dream
tests/               kiểm thử: python -m unittest discover -s tests
```

## Giao diện web (Studio)
Bấm đúp **`Mo-Studio.bat`** (hoặc chạy `python tools/web.py`). Trình duyệt sẽ mở `http://127.0.0.1:8765`. Web chỉ chạy trên máy bạn; đóng cửa sổ đen để tắt.
- **Các tập:** gợi ý ý tưởng, tạo tập mới, xem tiến độ ảnh/clip của từng tập.
- **Trang tập:** copy prompt từng cảnh, kéo-thả/dán (Ctrl+V) ảnh và clip vào đúng ô (tự đặt tên `sNN`, bản cũ được giữ với hậu tố `_v`), dựng video, xem video, điền tiêu đề/mô tả/hashtag/link.
- **Nhân vật:** xem ảnh mẫu, copy khóa ngoại hình.
- **Cài đặt:** chọn công cụ ảnh/video, nhạc mặc định.

Kịch bản và prompt vẫn do agent trong Antigravity viết. Web chỉ hiển thị kết quả và giúp bạn thao tác nhanh.

## Lệnh thủ công (không cần agent)
| Việc | Lệnh |
|---|---|
| Tạo tập mới | `python tools/new_episode.py [--series night-shift] [--dry-run]` |
| Xuất bảng prompt | `python tools/export_prompts.py ep001` |
| Giai đoạn của tập | `python tools/episode_state.py phase ep001` |
| Số cảnh, điểm cắt | `python tools/episode_state.py plan ep001` |
| Chốt ảnh | `python tools/episode_state.py lock ep001 all` |
| Dựng bản xem nhanh + kiểm tra nhịp | `python tools/assemble.py ep001 --preview --metronome` |
| Dựng bản cuối (không nhạc) | `python tools/assemble.py ep001` |
| Lật ngang 1 clip | `python tools/flip.py ep001 s03` |

## Quy trình một tập (/dream)
Gọi `/dream` trong Antigravity (hoặc `/dream ep003` để làm tiếp). Mỗi lần gọi, AI làm đúng một bước rồi dừng:

ý tưởng → **phân cảnh** (bạn duyệt) → prompt ảnh → **bạn tạo & chốt ảnh** → prompt video (AI xem ảnh đã chốt) → **bạn tạo clip** → dựng (hard cut theo nhịp) → đăng (chọn nhạc trong app, kéo tới `start_offset`).

- Mọi cảnh dài bằng nhau (~3s), 6 cảnh, ~17s, cắt đúng phách đoạn intro của bài nhạc (`library/music-profiles.json`, hiện 85 BPM).
- Mỗi cảnh bắt buộc có ảnh đã chốt và clip; ảnh/clip làm ở web nào cũng được.
- Kiểm tra khớp nhịp: `python tools/assemble.py ep003 --preview --metronome`.
- Trạng thái tập: `python tools/episode_state.py phase ep003`.

## Mở rộng
- Thêm chất liệu: sửa `library/materials.json` (vật thể mới nhớ khai báo `verbs` phù hợp).
- Thêm series: thêm vào `library/series.json` + bảng màu trong `palettes.json`.
- Thêm công cụ: copy `library/tool-guides/generic.md` → `<tên>.md`.
- Tự động hóa bằng API (sau này): thêm script `tools/gen_images.py` / `tools/gen_clips.py` đọc `script.json` và lưu vào `images/`, `clips/`; phần còn lại giữ nguyên.
