---
description: Lên kế hoạch và viết sẵn phân cảnh + prompt ảnh cho nhiều tập (mặc định 7)
---

# /weekly-batch

1. Đọc `library/episode-log.md` và `library/series.json`. Hỏi số tập (mặc định 7).
2. Lập lịch đa dạng: không quá 2 tập liền cùng series, không lặp vật thể trong tuần, có ít nhất 1 tập Phố Mơ. Trình bảng (ngày, series, ý tưởng 1 dòng) để người dùng duyệt.
3. Với từng tập: tạo tập (`python tools/new_episode.py ...`), viết phân cảnh theo skill **dream** và in bảng phân cảnh. Đợi người dùng duyệt **tất cả** bảng (có thể duyệt một lần "ok cả 7").
4. Sau khi duyệt: `approve` từng tập, viết prompt ảnh, `export_prompts.py`.
5. Tạo `episodes/batch-<YYYY-MM-DD>.md`: bảng ep_id, tiêu đề, số cảnh, link `prompts.md`; tổng số ảnh và clip cần tạo trong tuần.
6. Prompt video viết sau, khi từng tập đã chốt đủ ảnh (gọi `/dream epNNN`).
