---
name: assemble-video
description: Dựng video hoàn chỉnh (final.mp4) cho một tập Dreamnostalgic từ các clip: hard cut đúng phách nhạc, crop 9:16, film look, tiếng gõ nhịp để kiểm tra. Dùng khi người dùng đã có đủ clip và muốn dựng, xem thử, hoặc lật ngang một clip của chính họ.
---

# Dựng video

## Kiểm tra trước
- `python tools/episode_state.py phase <ep_id>` phải là `final` (đủ ảnh đã chốt và clip). Nếu chưa, nói người dùng còn thiếu gì.
- Clip đặt đúng tên `episodes/<ep_id>/clips/s01.mp4`, `s02.mp4`… (.mp4/.mov/.webm/.mkv đều được). Người dùng tải về tên khác: đề xuất đổi tên theo thứ tự cảnh, hỏi lại nếu không chắc.

## Lệnh
| Mục đích | Lệnh |
|---|---|
| Xem nhanh + kiểm tra nhịp | `python tools/assemble.py <ep_id> --preview --metronome` |
| Bản cuối 1080×1920 (không nhạc) | `python tools/assemble.py <ep_id>` |
| Giữ âm thanh gốc của clip | `... --clip-audio` |
| Nhạc có quyền dùng | `... --music music/<file>.mp3` |
| Lật ngang 1 clip của tập | `python tools/flip.py <ep_id> s03` |

## Ghi chú
- Độ dài cảnh tính từ lưới phách (hồ sơ nhạc + `beats_per_scene`), mọi cảnh bằng nhau, chỉ hard cut. Mỗi clip bỏ 0,5s đầu; thiếu ≤10% tự làm chậm; thiếu hơn → báo cảnh cần tạo lại clip.
- Film look: `library/lut/film.cube` nếu có, kèm `grade` của palette. Endcard: `library/brand/endcard.png` ở 2,5s cuối.
- Bản cuối không có nhạc: nhắc người dùng chọn nhạc trong app và kéo tới `start_offset` của hồ sơ nhạc.
- Chỉ dựng từ clip trong `episodes/`. Không dùng file trong `PublishedVideos/`, `UnpublishedVideos/` hay `Video/`.

Sau khi dựng xong: chuyển sang skill **qc-review**.
