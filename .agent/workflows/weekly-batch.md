---
description: Lên kế hoạch và viết sẵn kịch bản + prompt cho nhiều tập (mặc định 7) trong một lần
---

# /weekly-batch

1. Đọc `library/episode-log.md` và `library/series.json`. Hỏi người dùng số tập (mặc định 7) và tỉ lệ series nếu họ có ý muốn.
2. Lập lịch đa dạng: không quá 2 tập liền cùng series, không lặp vật thể trong cùng tuần, có ít nhất 1 tập Phố Mơ. Trình bảng kế hoạch (ngày, series, ý tưởng 1 dòng) để người dùng duyệt.
3. Sau khi duyệt, với từng tập: chạy `python tools/new_episode.py --series <id> --object <id> --verb <id>`, rồi dùng skill **episode-script** điền shots, rồi `python tools/export_prompts.py <ep_id>`.
4. Tạo `episodes/batch-<YYYY-MM-DD>.md`: bảng tổng hợp gồm ep_id, tiêu đề, số cảnh, link tới từng `prompts.md`, và danh sách ảnh tham chiếu cần chuẩn bị.
5. Báo người dùng tổng số ảnh và clip cần tạo trong tuần để họ ước lượng hạn mức của công cụ.
