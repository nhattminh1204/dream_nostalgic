# Hướng dẫn: viết phân cảnh

Dùng chung cho agent Antigravity và (sau này) nút AI trong Studio.

## Hình dạng (bắt buộc)
- Số cảnh và độ dài lấy từ `python tools/episode_state.py plan <ep>`: viết **đúng** `scenes` cảnh.
- Mọi cảnh **dài bằng nhau** (vd. 2,8–3,0 giây). Chỉ **hard cut**.

## Cấu trúc
- **Không có hook, không có reveal.** Mọi cảnh ngang hàng: mỗi cảnh là một khoảnh khắc kỳ diệu trọn vẹn trong cùng một thế giới.
- Liền mạch về không khí: cùng thế giới, cùng bảng màu của series, cùng giờ trong ngày hoặc chuyển dần (chiều → hoàng hôn → đêm).
- Luân phiên góc máy (`wide`, `medium`, `hands`, `low`, `over-shoulder`, `detail`); **không** để hai cảnh liền nhau cùng góc.
- Cảnh 1 phải đọc được trong 1 giây: vật thể kỳ diệu + người đang làm việc, rõ ràng.
- Mỗi cảnh **một** hành động chậm, vừa trong khoảng 3 giây.
- Nhân vật: chỉ dùng id trong danh sách của series (`library/series.json`); tối đa 2 nhân vật mỗi cảnh; Golden xuất hiện 1–2 cảnh.
- Nếu `concept.custom_idea` có nội dung: phát triển ý đó thay vì logline.

## Đầu ra (JSON, ghi vào file tạm rồi `apply ... storyboard`)
```json
{
  "shots": [
    {"angle": "wide", "scene_vi": "Ông Moon đứng trên xe nâng, đánh bóng mặt trăng khổng lồ trên thị trấn", "characters": ["ong-moon"]}
  ],
  "title": "POV: your job is polishing the moon 🌙",
  "description": "The moon gets a little dusty every night. Someone has to polish it.",
  "hashtags": ["#dreamnostalgic", "#shorts", "#nostalgia", "#dreamcore", "#moon", "#cozy"]
}
```
`scene_vi`: tiếng Việt, 1 câu. Tiêu đề/mô tả/hashtag theo `library/guides/seo.md`.
