# veo (video: app Gemini / Flow / Gemini API)

## Định dạng prompt
- Dùng **ảnh cảnh làm khung đầu** (image-to-video / frames-to-video trong Flow).
- Prompt mô tả chuyển động + không khí, 1–3 câu:
  `Slow gentle push-in. The man moves the buffer in small circles; faint sparkles drift off the moon. Calm, dreamy, no fast movement.`
- Veo có thể sinh âm thanh: thêm `Ambient sound: soft wind, quiet machine hum, no music, no dialogue.` Nếu sẽ thay nhạc thì không cần.

## Tham chiếu
- Flow có tính năng dùng nhiều ảnh thành phần (nhân vật, bối cảnh) trong một cảnh: dùng ref-sheet nhân vật để giữ mặt.
- Muốn nối liền 2 cảnh: lấy khung cuối clip trước làm khung đầu clip sau.

## Tham số
- Tỉ lệ dọc 9:16 (chọn trong cài đặt). Clip khoảng 8s → trong script đặt `dur` 5–8.

## Lỗi thường gặp
- Nhân vật tự nói hoặc nhép miệng → thêm `no dialogue, mouth closed`.
- Hạn mức gói thuê bao thấp → chỉ đưa vào Veo những ảnh đã duyệt kỹ.
- Kiểm tra watermark hiển thị trên clip của gói bạn dùng trước khi sản xuất hàng loạt.
