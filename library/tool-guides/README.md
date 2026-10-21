# Tool guides

Mỗi file mô tả cách viết prompt cho một công cụ. `config.json` → `image_tool` / `video_tool` chọn file nào được dùng.

| id | Loại | Ghi chú nhanh |
|---|---|---|
| `generic` | ảnh + video | Mặc định khi chưa chọn công cụ |
| `nano-banana` | ảnh | Gemini (app hoặc API). Giữ nhân vật tốt, sửa ảnh bằng lời |
| `midjourney` | ảnh | Thẩm mỹ mạnh, có `--cref`/`--sref`/`--oref` tùy phiên bản; không có API chính thức |
| `flux` | ảnh | Qua fal.ai / Replicate / ComfyUI; dễ tự động hóa |
| `veo` | video | Gemini / Flow; clip ~8s, có thể sinh âm thanh |
| `kling` | video | Image-to-video mạnh, chuyển động tự nhiên |
| `hailuo` | video | MiniMax; rẻ, chuyển động mượt |
| `runway` | video | Gen-4; điều khiển camera tốt |

> Các công cụ AI cập nhật rất nhanh. Tham số và tên model trong các file này có thể đã cũ. Khi công cụ thay đổi, sửa file guide tương ứng; skill sẽ tự dùng bản mới.

## Thêm công cụ mới
Copy `generic.md` → `<id>.md`, điền 4 mục: **Định dạng prompt**, **Tham chiếu nhân vật/phong cách**, **Tham số**, **Lỗi thường gặp**.
