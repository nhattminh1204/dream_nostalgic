# kling (video)

## Định dạng prompt
- Image-to-video với ảnh cảnh làm khung đầu.
- Prompt: `[chuyển động chủ thể], [chuyển động môi trường], [camera]`, ngắn gọn, ví dụ:
  `The baker gently lifts the cloud from the oven tray, steam curls upward, slow push-in, calm pace`
- Negative prompt: `fast motion, camera shake, morphing, distorted hands, text`

## Tham chiếu
- Có chế độ khung đầu + khung cuối: hữu ích cho cảnh "trước → sau" (mây trắng → mây hồng).
- Tính năng elements/nhân vật (tùy phiên bản) giúp giữ mặt.

## Tham số
- Tỉ lệ 9:16, 5s hoặc 10s. Chế độ chất lượng cao (Pro/Master) cho cảnh hook.
- Mức "creativity / relevance" để mức vừa: bám ảnh nhưng vẫn có chuyển động.

## Lỗi thường gặp
- Vật thể biến hình (morph) → đơn giản hóa chuyển động, chỉ 1 hành động/clip.
