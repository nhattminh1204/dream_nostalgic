# flux (ảnh: fal.ai / Replicate / ComfyUI / các app dùng Flux)

## Định dạng prompt
- Câu văn tự nhiên, chi tiết, 60–120 từ; Flux bám prompt sát.
- Đặt chi tiết quan trọng nhất (chủ thể + vật thể trong mơ) ở đầu câu.

## Tham chiếu nhân vật / phong cách
- Dùng biến thể có hỗ trợ ảnh tham chiếu (Kontext / Redux / IP-Adapter, tùy nền tảng) để giữ nhân vật.
- Muốn ổn định lâu dài: train LoRA nhân vật từ 15–30 ảnh ref.

## Tham số gợi ý
- Kích thước 768×1344 hoặc 1088×1920 (9:16).
- Guidance vừa phải; quá cao sẽ làm màu gắt, mất chất phim.

## Lỗi thường gặp
- Da quá mịn, nhựa → thêm `natural skin texture, film grain, candid`.
- Dễ tự động hóa qua API → phù hợp khi muốn chạy hàng loạt.
