---
name: dream
description: Điều phối quy trình làm một tập Dreamnostalgic (ý tưởng → phân cảnh → prompt ảnh → chốt ảnh → prompt video → clip → video → đăng). Dùng khi người dùng gọi /dream, muốn tạo tập mới, hoặc làm tiếp một tập đang dở.
---

# /dream

Mỗi lần được gọi: **xác định tập → xem giai đoạn → làm đúng MỘT bước → dừng và nói người dùng việc tiếp theo.** AI ghi nhớ qua file, không qua cuộc trò chuyện.

## 1. Xác định tập
- `/dream epNNN` → tập đó.
- `/dream` không đối số → đọc `library/episode-log.md`, liệt kê các tập chưa `published` kèm giai đoạn (`python tools/episode_state.py phase <ep>`), hỏi: làm tiếp tập nào hay tạo tập mới.
- Tạo tập mới: chạy `python tools/new_episode.py --dry-run --json --seed <số>` 3 lần (seed khác nhau) để đưa 3 ý tưởng; người dùng chọn số, gõ "random", hoặc gõ ý riêng. Tạo bằng `python tools/new_episode.py --series <id> --object <id> --verb <id> --seed <seed>` (ý riêng: thêm `--idea "<ý tưởng>"`). Sau đó làm tiếp bước 2 ngay.

## 2. Xem giai đoạn
`python tools/episode_state.py phase <ep>` → `{phase, by, message}`. Làm theo bảng:

| phase | Làm |
|---|---|
| `idea` | Chạy `plan <ep>`; viết phân cảnh theo `library/guides/storyboard.md`; ghi JSON ra file tạm (vd. `episodes/<ep>/.ai-storyboard.json`); `apply <ep> storyboard <file>`; in **bảng phân cảnh** (dưới) rồi hỏi "ok hay sửa gì?" |
| `storyboard` | Người dùng trả "ok" → `approve <ep>` rồi làm luôn bước `image_prompts`. Người dùng góp ý → sửa JSON, `apply` lại, in lại bảng |
| `image_prompts` | Viết theo `library/guides/image-prompts.md` → `apply <ep> image_prompts <file>` → `python tools/export_prompts.py <ep>` → nhắc mở Studio hoặc `prompts.md`, tạo ảnh, thả vào và **Chốt** (hoặc `lock <ep> all`) |
| `images` | Nói cảnh nào chưa chốt (từ `message`). Không tự chốt hộ trừ khi người dùng yêu cầu |
| `video_prompts` | **Mở xem từng ảnh đã chốt** (`show <ep>` → `locked_image`), viết theo `library/guides/video-prompts.md` (chỉ cảnh thiếu hoặc `motion_stale`) → `apply <ep> video_prompts <file>` → `export_prompts.py` → nhắc tạo clip dài ≥ `scene_seconds + 0.5` giây |
| `clips` | Nói cảnh nào thiếu clip |
| `final` | Nếu chưa có `final.mp4`: đề nghị `python tools/assemble.py <ep> --preview --metronome` để kiểm tra nhịp, rồi bản cuối `python tools/assemble.py <ep>`. Nếu đã có: đưa tiêu đề/mô tả/hashtag, nhắc chọn nhạc trong app và **kéo tới `start_offset`** của hồ sơ nhạc, rồi dán link vào Studio |
| `published` | Báo hoàn tất |

## Bảng phân cảnh (in cho người dùng duyệt)
```
01 · wide   · 2.83s · Ông Moon trên xe nâng, đánh bóng mặt trăng khổng lồ
02 · hands  · 2.83s · bàn tay xoay máy đánh bóng, bụi trăng lấp lánh
...
Tổng: 6 cảnh × 2.83s = 16.9s · 4 phách/cảnh · hard cut
```
Lấy số giây từ `plan <ep>` (`scene_seconds`, `total_seconds`).

## Quy tắc
- Mỗi lần chỉ làm một bước rồi dừng. Không bỏ qua bước; ảnh và clip là bắt buộc.
- Lỗi từ `apply` (in "Lỗi: ...") → sửa JSON theo nội dung lỗi và `apply` lại một lần; vẫn lỗi thì báo người dùng.
- `Lưu ý: ... giữ ... bạn đã sửa tay` → báo người dùng; chỉ dùng `--overwrite-edited` khi họ đồng ý.
- Lỗi "vừa được cập nhật ở nơi khác" → đọc lại tập (`show`) rồi làm lại.
- Xóa file JSON tạm sau khi `apply` thành công.
- Trả lời người dùng bằng tiếng Việt.
