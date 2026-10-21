# Hướng dẫn: viết prompt ảnh

## Đọc trước
1. `config.json` → `image_tool` (hoặc `image_tool` trong script.json); trống = `generic`. Theo đúng `library/tool-guides/<image_tool>.md`.
2. `library/prompt-vocab.md`: STYLE BLOCK, ánh sáng, negative.
3. `library/palettes.json` → `prompt_phrase` của palette tập.
4. `library/characters/<id>.md` → **khóa ngoại hình**: dán NGUYÊN VĂN, không diễn đạt lại.

## Khung prompt (tiếng Anh, 60–110 từ, một đoạn văn)
```
[Tỉ lệ dọc 9:16 theo cách tool yêu cầu]. [Khóa ngoại hình nhân vật hoặc người lao động chung]
[hành động thủ công tỉ mỉ] [vật thể trong mơ] [bối cảnh], [giờ trong ngày]. [Đạo cụ].
[Góc máy của cảnh]. [Một chi tiết cảm xúc].
[STYLE BLOCK]. [palette prompt_phrase]. [Điều cần tránh nếu tool không có ô negative.]
```
- Một hành động chính mỗi cảnh; vật thể trong mơ lớn, rõ trong khung dọc.
- Chừa 15% đáy khung trống chi tiết quan trọng.
- Nhãn, biển hiệu: yêu cầu để trống (`blank labels`).
- Giữ nhất quán giữa các cảnh: cùng trang phục, cùng giờ/ánh sáng theo phân cảnh.

## Đầu ra (JSON, `apply ... image_prompts`)
```json
{"shots": [{"n": 1, "image_prompt": "Create a vertical 9:16 photograph...", "negative": "text, watermark, ..."}]}
```
Tool không có ô negative → để `negative` rỗng và đưa phần tránh vào cuối `image_prompt`.
