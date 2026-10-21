---
name: qc-review
description: Checklist duyệt chất lượng ảnh, clip và video cuối của Dreamnostalgic trước khi đăng; cập nhật episode-log. Dùng khi người dùng gửi ảnh hoặc clip để nhận xét, hoặc trước khi đăng.
---

# Duyệt chất lượng

## Ảnh (trước khi tốn lượt tạo video)
- [ ] Đúng 9:16, chủ thể nằm ở 2/3 giữa, đáy khung không có chi tiết quan trọng
- [ ] Nhân vật khớp ref-sheet: mặt, tóc, trang phục, mũ
- [ ] Tay: đủ 5 ngón, cầm dụng cụ hợp lý
- [ ] Không chữ rác, logo, watermark; không vật thể hiện đại
- [ ] Màu đúng palette, có chất phim (không bóng bẩy kiểu CGI)
- [ ] Vật thể trong mơ rõ ràng, đọc được ngay
Ảnh lỗi → đề xuất câu sửa cụ thể (theo tool guide), ví dụ với Nano Banana: `Keep everything the same but fix the left hand holding the buffer.`

## Clip
- [ ] Không biến hình (morph), không giật, không nhép miệng
- [ ] Chuyển động chậm, một hành động, khớp `motion_prompt`
- [ ] 1–2 giây đầu và cuối dùng được (để cắt)

## Video cuối (`final.mp4`)
- [ ] Cảnh 1 gây tò mò trong 1 giây
- [ ] Tổng 25–35s, nhịp đều, cảnh cuối lặp về đầu tự nhiên
- [ ] Màu đồng nhất giữa các cảnh sau khi grade
- [ ] Âm thanh: nhạc có quyền dùng, hoặc im lặng để thêm nhạc trong app
- [ ] Không có chất liệu nào từ thư mục `Video/`

## Sau khi duyệt
- Đổi `status` trong script.json: `draft` → `ready`.
- Khi người dùng báo đã đăng: cập nhật dòng của tập trong `library/episode-log.md` → status `published`, điền link.
