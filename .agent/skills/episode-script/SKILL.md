---
name: episode-script
description: Lên ý tưởng và viết shot list cho một tập Dreamnostalgic mới. Dùng khi người dùng muốn tạo tập mới, lên ý tưởng video, hoặc điền shots cho episodes/epNNN/script.json.
---

# Viết kịch bản tập

## 1. Tạo tập
- Nếu chưa có thư mục tập: chạy `python tools/new_episode.py` (thêm `--series`, `--object`, `--verb` nếu người dùng chỉ định). Dùng `--dry-run` để đưa 2–3 phương án cho người dùng chọn khi họ muốn chọn.
- Nếu người dùng tự đưa ý tưởng ngoài kho chất liệu: vẫn chạy `new_episode.py` với series gần nhất, rồi sửa `concept` trong script.json. Đề xuất thêm mục mới vào `library/materials.json` nếu ý tưởng hay.

## 2. Thiết kế mạch truyện (4–6 cảnh, tổng 25–35s)
Đọc `library/series.json`, `library/characters/<id>.md` và `library/prompt-vocab.md`. Cấu trúc mặc định:

| # | role | Gợi ý góc máy | dur |
|---|---|---|---|
| 1 | `hook` | `low` hoặc `wide`: vật thể kỳ diệu + người làm việc, hiểu ngay trong 1s | 5–6 |
| 2 | `process` | `medium`: bắt đầu công việc | 5–6 |
| 3 | `detail` | `hands` hoặc `detail`: cận cảnh thỏa mãn (ASMR) | 4–5 |
| 4 | `process` | `over-shoulder` / `medium`: tiến triển, có thể có Golden | 5–6 |
| 5 | `reveal` | `wide`: thành quả đẹp nhất (vd. trăng sáng rực trên thị trấn) | 6–8 |

Mạch là một **quy trình có trước → sau** (bẩn → bóng, trắng → hồng, rời rạc → hoàn chỉnh). Cảnh cuối nên nối được về cảnh đầu để video lặp tự nhiên.

## 3. Viết từng shot vào `script.json` → `shots`
```json
{
  "n": 1,
  "role": "hook",
  "angle": "low",
  "dur": 6,
  "characters": ["ong-moon"],
  "scene_vi": "Ông Moon đứng trên xe nâng, đánh bóng mặt trăng khổng lồ, thị trấn lên đèn bên dưới",
  "image_prompt": "...",
  "motion_prompt": "...",
  "negative": "..."
}
```
- `image_prompt`, `motion_prompt`, `negative`: viết theo skill **prompt-writer** (gọi nó cho từng shot).
- Giữ nhất quán: cùng giờ trong ngày, cùng trang phục, cùng đạo cụ chính xuyên suốt tập (trừ khi mạch truyện chuyển giờ có chủ đích).

## 4. Hoàn tất
- Điền `description` (1–2 câu thơ ngắn tiếng Anh) và `hashtags` theo skill **seo-metadata**.
- Chạy `python tools/export_prompts.py <ep_id>` và báo người dùng mở `episodes/<ep_id>/prompts.md`.
- Tóm tắt cho người dùng bằng tiếng Việt: tiêu đề, mạch 5 cảnh (mỗi cảnh 1 dòng), ảnh tham chiếu cần đính kèm.
