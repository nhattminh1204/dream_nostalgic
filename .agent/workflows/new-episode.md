---
description: Tạo trọn một tập Dreamnostalgic, từ ý tưởng đến final.mp4
---

# /new-episode

1. Đọc `config.json` và `library/episode-log.md`. Báo người dùng công cụ ảnh/video đang chọn (trống = generic).
2. Hỏi người dùng (1 câu): muốn chọn series/ý tưởng cụ thể không? Nếu không, chạy `python tools/new_episode.py --dry-run` 3 lần (seed khác nhau) và đưa 3 phương án để chọn.
3. Chạy `python tools/new_episode.py` với lựa chọn đã chốt.
4. Dùng skill **episode-script** (kèm **prompt-writer**, **seo-metadata**) điền script.json, rồi chạy `python tools/export_prompts.py <ep_id>`.
5. Dừng lại. Hướng dẫn người dùng: mở `episodes/<ep_id>/prompts.md`, tạo ảnh và lưu vào `images/sNN.png`. Nhắc đính kèm ref-sheet nhân vật.
6. Khi người dùng báo đã có ảnh: xem từng ảnh theo skill **qc-review** (phần Ảnh). Đề xuất sửa nếu cần.
7. Người dùng tạo clip từ ảnh đã duyệt, lưu vào `clips/sNN.mp4`.
8. Dùng skill **assemble-video**: chạy bản `--preview` trước, sau khi người dùng ưng ý thì dựng bản cuối.
9. Dùng skill **qc-review** (phần Video cuối). Đổi status thành `ready`, đưa tiêu đề, mô tả, hashtag để người dùng copy khi đăng.
