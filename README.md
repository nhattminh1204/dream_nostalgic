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
.agent/skills/       episode-script · prompt-writer · assemble-video · seo-metadata · qc-review
.agent/workflows/    /new-episode · /weekly-batch
library/             kiến thức: chất liệu, series, bảng màu, nhân vật, từ vựng prompt, hướng dẫn từng công cụ, nhật ký tập
  characters/<id>/   ảnh ref-sheet của nhân vật (bạn tạo)
  style-anchors/     ảnh chuẩn phong cách (bạn tạo, KHÔNG dùng khung hình từ Video/)
  brand/endcard.png  logo cuối video (tùy chọn, PNG nền trong suốt)
  lut/film.cube      LUT film look (tùy chọn)
music/               nhạc bạn có quyền dùng
episodes/epNNN/      script.json · prompts.md · images/ · clips/ · final.mp4
tools/               script Python (không phụ thuộc IDE)
Video/               tư liệu tham khảo phong cách, chỉ để xem, không dùng làm chất liệu
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
| Dựng bản xem nhanh | `python tools/assemble.py ep001 --preview` |
| Dựng bản cuối | `python tools/assemble.py ep001 [--music music/x.mp3] [--clip-audio]` |
| Lật ngang 1 clip | `python tools/flip.py ep001 s03` |

## Quy trình một tập (linh hoạt)
`/new-episode` → script.json + prompts.md → **bạn** tạo ảnh (`images/sNN.png`) → duyệt → **bạn** tạo clip (`clips/sNN.mp4`) → `assemble.py` → duyệt → đăng (thêm nhạc trong app nếu chưa có).

Không bước nào bắt buộc:
- Ảnh và clip tạo ở **bất kỳ web/app nào**, Studio chỉ nhận file về.
- **Bỏ qua ảnh** nếu bạn tạo clip thẳng từ prompt (text-to-video).
- **Ghép video ở nơi khác** (CapCut, web AI…) rồi tải `final.mp4` lên trong tab “Video & đăng”, hoặc lưu thẳng vào `episodes/<id>/final.mp4`.
- Không cần dùng Studio: lưu file đúng tên vào thư mục tập là đủ.

## Mở rộng
- Thêm chất liệu: sửa `library/materials.json` (vật thể mới nhớ khai báo `verbs` phù hợp).
- Thêm series: thêm vào `library/series.json` + bảng màu trong `palettes.json`.
- Thêm công cụ: copy `library/tool-guides/generic.md` → `<tên>.md`.
- Tự động hóa bằng API (sau này): thêm script `tools/gen_images.py` / `tools/gen_clips.py` đọc `script.json` và lưu vào `images/`, `clips/`; phần còn lại giữ nguyên.
