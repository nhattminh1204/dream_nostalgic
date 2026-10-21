---
name: prompt-writer
description: Viết hoặc viết lại prompt ảnh / prompt video cho một hoặc vài cảnh, kể cả khi người dùng đổi công cụ AI. Dùng khi người dùng yêu cầu sửa prompt cụ thể ngoài quy trình /dream.
---

# Viết prompt cho cảnh

- Prompt ảnh: theo `library/guides/image-prompts.md`. Prompt video: theo `library/guides/video-prompts.md` (luôn xem ảnh đã chốt).
- Ghi kết quả bằng `python tools/episode_state.py apply <ep> image_prompts|video_prompts <file.json>`; người dùng đã sửa tay thì chỉ thêm `--overwrite-edited` khi họ đồng ý.
- Đổi công cụ: viết lại mọi cảnh của tập đang làm theo tool guide mới, rồi `python tools/export_prompts.py <ep>`.
