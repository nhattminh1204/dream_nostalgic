# nano-banana (Gemini image: app Gemini / Google AI Studio / Gemini API)

## Định dạng prompt
- Viết như **mô tả một cảnh phim bằng câu văn đầy đủ**; Gemini hiểu ngữ cảnh tốt hơn khi đọc câu văn so với danh sách từ khóa.
- Mở đầu bằng tỉ lệ: `Create a vertical 9:16 photograph...`
- Khi có ảnh tham chiếu: `Using the man from the first reference image and the visual style of the second image, ...`
- Không có ô negative riêng → viết điều cần tránh ở cuối: `No text, no watermark, no modern objects.`

## Tham chiếu nhân vật / phong cách
- Tải lên tối đa vài ảnh cùng lúc: [ref-sheet nhân vật] + [style anchor]. Nói rõ ảnh nào dùng cho cái gì.
- Giữ nguyên nhân vật giữa các cảnh: tạo cảnh 1 xong, ở cảnh 2 tải **ảnh cảnh 1** lên và nói `Same man, same outfit, now ...`.

## Sửa ảnh bằng lời (rất hữu ích)
- `Keep everything the same but change the time to blue hour.`
- `Remove the text on the crates, keep the labels blank.`
- `Make the moon twice as large, keep the man unchanged.`

## Tham số
- Nếu tỉ lệ ra sai, nói lại: `Output must be vertical 9:16 portrait.`
- Tải ảnh về ở độ phân giải cao nhất có thể.

## Lỗi thường gặp
- Màu quá rực, quá "digital" → nhấn mạnh `muted, faded 1970s film colors, lifted blacks`.
- Mặt nhân vật trôi dần qua nhiều lần sửa → quay lại ref-sheet gốc thay vì sửa chồng nhiều lần.
