# generic (ảnh + video)

## Định dạng prompt
- **Ảnh:** 1 đoạn văn tiếng Anh, 60–110 từ: chủ thể → hành động → vật thể trong mơ → bối cảnh → ánh sáng/giờ → góc máy → STYLE BLOCK → palette phrase. Ghi rõ `vertical 9:16`.
- **Video:** 1–3 câu, chỉ mô tả CHUYỂN ĐỘNG (camera + thứ đang chuyển động trong cảnh), không mô tả lại toàn bộ ảnh.

## Tham chiếu nhân vật / phong cách
- Dán khóa ngoại hình của nhân vật vào prompt.
- Nếu công cụ cho phép tải ảnh lên: đính kèm `library/characters/<id>/ref-sheet.png` và một ảnh style anchor (`library/style-anchors/`).

## Tham số
- Tỉ lệ 9:16. Độ dài clip 5–8s.

## Lỗi thường gặp
- Tay méo → ưu tiên góc máy giấu bớt tay hoặc cận tay đơn giản.
- Chữ rác trên nhãn, biển hiệu → thêm negative `text, letters` hoặc yêu cầu nhãn trống.
