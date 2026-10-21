---
name: seo-metadata
description: Viết lại tiêu đề, mô tả, hashtag cho Shorts Dreamnostalgic. Dùng khi người dùng muốn đổi thông tin đăng.
---

# Tiêu đề, mô tả, hashtag

Theo `library/guides/seo.md`. Đưa 3 phương án tiêu đề cho người dùng chọn, rồi ghi bằng
`python tools/episode_state.py apply <ep> seo <file.json>` với `{"title": ..., "description": ..., "hashtags": [...]}`.
Nhắc người dùng khai báo nội dung AI trung thực khi YouTube hỏi.
