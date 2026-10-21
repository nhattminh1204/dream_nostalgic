# midjourney (ảnh)

## Định dạng prompt
- Câu mô tả ngắn gọn hơn Gemini (40–80 từ), sau đó là tham số.
- Ví dụ khung: `<mô tả cảnh>, <STYLE BLOCK rút gọn>, <palette phrase> --ar 9:16 --style raw`

## Tham chiếu nhân vật / phong cách
- Nhân vật: tham số tham chiếu nhân vật/đối tượng (`--cref` ở bản cũ, `--oref` ở bản mới hơn) + URL ảnh ref-sheet.
- Phong cách: `--sref <url style anchor>`; lưu lại mã sref ưng ý vào `library/style-anchors/README.md` để dùng mãi.
- Kiểm tra trang tài liệu Midjourney hiện hành vì tên tham số đổi theo phiên bản.

## Tham số gợi ý
- `--ar 9:16 --style raw --stylize 100-250`
- Negative: `--no text, watermark, neon, modern phone`

## Lỗi thường gặp
- Quá "đẹp kiểu Midjourney", bóng bẩy → `--style raw`, giảm stylize, nhấn `35mm film still, candid`.
- Không có API chính thức → bước ảnh làm tay; agent chỉ xuất prompt để copy.
