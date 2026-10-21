# Hướng dẫn: viết prompt video

Chỉ viết khi **mọi cảnh đã chốt ảnh**. Luôn **xem ảnh đã chốt** (`locked_image` trong script.json) trước khi viết: mô tả chuyển động khớp với đúng những gì có trong ảnh.

## Mỗi cảnh
- Tiếng Anh, 1–3 câu: [chuyển động camera] + [một hành động nhỏ, chậm của chủ thể] + [chuyển động môi trường] + `calm, dreamy pace, no fast movement, no dialogue`.
- Không mô tả lại toàn bộ ảnh; chỉ mô tả cái gì chuyển động.
- Theo cách viết của `library/tool-guides/<video_tool>.md`.

## Liền mạch qua hard cut
- Xem cả chuỗi cảnh: tránh hai cảnh liền nhau có hướng camera ngược nhau (vd. push-in rồi pull-back).
- Ưu tiên `slow push-in`, `locked-off static`, `gentle parallax`; mỗi tập dùng tối đa 2 kiểu camera.
- Chuyển động bắt đầu ngay từ đầu clip (clip bị cắt 0,5 giây đầu và chỉ dùng khoảng 3 giây).

## Độ dài clip cần tạo
`plan` → `scene_seconds + 0.5` giây; chọn chế độ ngắn nhất của app ≥ con số này.

## Đầu ra (JSON, `apply ... video_prompts`)
```json
{"shots": [{"n": 1, "motion_prompt": "Slow gentle push-in. The man moves the buffer in small circles; faint sparkles drift off the moon. Calm, dreamy pace, no fast movement, no dialogue."}]}
```
Nếu chỉ có vài cảnh `motion_stale`: chỉ trả các cảnh đó (và giữ liền mạch với cảnh kề bên).
