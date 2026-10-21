# runway (video: Gen-4 trở lên)

## Định dạng prompt
- Image-to-video. Prompt tập trung vào chuyển động, không mô tả lại hình:
  `The camera slowly dollies forward as the worker rolls pink paint across the cloud.`
- Runway khuyên: mô tả chuyển động đơn giản, rõ ràng; tránh prompt phủ định trong văn bản.

## Tham chiếu
- References / ảnh tham chiếu để giữ nhân vật giữa các cảnh.
- Điều khiển camera chi tiết (tùy phiên bản) → dùng cho cảnh toàn cảnh mở đầu.

## Tham số
- 9:16, 5s hoặc 10s.

## Lỗi thường gặp
- Mất chất phim (quá sạch) → không sao, `tools/assemble.py` sẽ thêm grain + grade đồng bộ.
