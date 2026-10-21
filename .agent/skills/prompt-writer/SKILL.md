---
name: prompt-writer
description: Viết prompt ảnh, prompt chuyển động và negative cho một cảnh Dreamnostalgic theo đúng công cụ AI người dùng đang chọn (Gemini/Nano Banana, Midjourney, Flux, Veo, Kling, Hailuo, Runway...). Dùng khi viết hoặc sửa prompt, hoặc khi người dùng đổi công cụ.
---

# Viết prompt cho một cảnh

## Đầu vào cần đọc
1. `config.json` → `image_tool`, `video_tool` (hoặc giá trị trong script.json của tập). Trống → `generic`.
2. `library/tool-guides/<image_tool>.md` và `library/tool-guides/<video_tool>.md`: tuân theo định dạng trong đó.
3. `library/prompt-vocab.md`: STYLE BLOCK, ánh sáng, góc máy, negative.
4. `library/palettes.json` → `prompt_phrase` của palette tập.
5. `library/characters/<id>.md` → **khóa ngoại hình**, dán nguyên văn, không diễn đạt lại.
6. `library/materials.json` → chuỗi `en` của worker / verb / object / setting / time / angle.

## Prompt ảnh (khung chung, điều chỉnh theo tool guide)
```
[Tỉ lệ dọc 9:16 theo cách tool yêu cầu]. [Khóa ngoại hình nhân vật hoặc worker.en]
[verb.en] [object.en] [setting.en], [time.en]. [Chi tiết đạo cụ từ props].
[angle.en]. [1 chi tiết cảm xúc: biểu cảm, Golden, hơi nước, tia lấp lánh].
[STYLE BLOCK]. [palette.prompt_phrase]. [Điều cần tránh nếu tool không có ô negative.]
```
- 60–110 từ. Một hành động chính duy nhất mỗi cảnh.
- Vật thể trong mơ phải **rõ, lớn, dễ đọc** trong khung dọc.
- Nhãn, biển hiệu: yêu cầu để trống (`blank labels`). Chữ do AI tạo thường bị lỗi.

## Prompt chuyển động
- 1–3 câu: [chuyển động camera] + [chuyển động chủ thể, nhỏ, chậm] + [chuyển động môi trường] + `calm, dreamy pace, no fast movement`.
- Chỉ một hành động mỗi clip. Không yêu cầu người nói hay nhép miệng.
- Cảnh `reveal`: ưu tiên camera kéo ra (`slow pull-back`) hoặc đứng yên để thành quả "thở".

## Negative
Lấy từ `prompt-vocab.md`, thêm lỗi riêng của cảnh (vd. cảnh cận tay: `extra fingers, fused fingers`). Tool không có ô negative → để trống trường `negative` và đưa vào cuối prompt ảnh.

## Khi người dùng đổi công cụ
Viết lại `image_prompt`/`motion_prompt` của mọi shot trong tập đang làm theo guide mới, giữ nguyên `scene_vi`, rồi chạy lại `python tools/export_prompts.py <ep_id>`.
