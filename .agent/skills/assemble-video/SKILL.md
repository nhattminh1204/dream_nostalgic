---
name: assemble-video
description: Dựng video hoàn chỉnh (final.mp4) cho một tập Dreamnostalgic từ các clip đã tạo: cắt độ dài, crop 9:16, film look, nhạc, endcard. Dùng khi người dùng đã có clip và muốn ghép, xem thử, hoặc lật ngang một clip.
---

# Dựng video

## Kiểm tra trước
- Clip đặt đúng tên: `episodes/<ep_id>/clips/s01.mp4`, `s02.mp4`… (đuôi .mp4/.mov/.webm/.mkv đều được), khớp `n` trong script.json.
- Nếu người dùng tải về với tên khác: đề xuất đổi tên theo thứ tự cảnh, hỏi lại nếu không chắc cảnh nào là cảnh nào.
- Lần đầu chạy trên máy: `pip install -r tools/requirements.txt` (nếu chưa có ffmpeg trong PATH).

## Lệnh
| Mục đích | Lệnh |
|---|---|
| Bản xem nhanh 540×960 | `python tools/assemble.py <ep_id> --preview` |
| Bản cuối 1080×1920 | `python tools/assemble.py <ep_id>` |
| Kèm nhạc | `... --music music/<file>.mp3` (hoặc điền `music` trong script.json) |
| Giữ âm thanh gốc của clip | `... --clip-audio` (khi có nhạc, âm gốc được trộn nhỏ ở 35%) |
| Lật ngang 1 clip của tập | `python tools/flip.py <ep_id> s03` (giữ bản `.orig`) |

## Ghi chú
- Độ dài mỗi cảnh = `dur` trong script.json (hoặc ngắn hơn nếu clip ngắn hơn). Muốn đổi nhịp: sửa `dur` rồi dựng lại.
- Film look: dùng `library/lut/film.cube` nếu có, kèm `grade` của palette. Muốn tăng giảm hạt phim hay độ bạc màu: sửa hằng `FILM_LOOK` trong `tools/assemble.py`.
- Endcard: `library/brand/endcard.png` (PNG nền trong suốt) tự hiện ở 2.5s cuối.
- Không có nhạc → video im lặng; nhắc người dùng thêm nhạc trong app Shorts khi đăng.
- Chỉ dựng từ clip trong `episodes/`. Không bao giờ dùng file trong `Video/`.

Sau khi dựng xong: chuyển sang skill **qc-review**.
