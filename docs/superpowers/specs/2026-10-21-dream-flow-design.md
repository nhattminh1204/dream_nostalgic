# Thiết kế: quy trình `/dream` (ý tưởng → phân cảnh → ảnh → video), khớp nhịp nhạc

Ngày: 2026-10-21 · Trạng thái: chờ người dùng duyệt

## 1. Mục tiêu

Một quy trình làm Shorts Dreamnostalgic trong đó:
- Người dùng khởi động bằng một lệnh hoặc nút, chốt ý tưởng (chọn trong gợi ý, gõ ý riêng, hoặc "random").
- AI đề xuất phân cảnh, người dùng duyệt, AI viết prompt ảnh.
- Người dùng tạo và **chốt** ảnh ở bất kỳ web nào; AI **xem ảnh đã chốt** rồi mới viết prompt video.
- Video ghép bằng **hard cut**, mọi lần cắt rơi đúng phách của đoạn intro không lời của bài lofi người dùng chọn.
- AI "nhớ" tiến độ qua file, không qua cuộc trò chuyện.
- Điều khiển chính từ Studio (nút bấm gọi Gemini API); Antigravity dùng song song.

## 2. Các quyết định đã chốt

| # | Vấn đề | Quyết định |
|---|---|---|
| 1 | Ai điều khiển | Kết hợp: nền tảng chạy được qua Antigravity; Studio gọi AI trực tiếp |
| 2 | Nhịp ảnh → video | Theo giai đoạn: chốt **đủ bộ** ảnh rồi AI mới viết prompt video cho mọi cảnh |
| 3 | Nhạc | Xuất video **không nhạc**; chọn nhạc trong app khi đăng (đặt điểm bắt đầu 0:00) |
| 4 | Chuyển cảnh | **Chỉ hard cut**, không có tùy chọn khác |
| 5 | Chốt ý tưởng | AI đưa 3 ý tưởng (không trùng tập cũ); chọn, gõ "random", hoặc gõ ý riêng |
| 6 | Độ dài | Theo **hồ sơ nhạc** của đoạn intro; cắt theo lưới phách |
| 7 | Chốt ảnh | Nút **Chốt / Bỏ chốt** từng cảnh và **Chốt cả bộ** trong Studio |
| 8 | Phân cảnh | Người dùng **duyệt bảng phân cảnh** trước khi AI viết prompt ảnh |
| 9 | Kiến trúc | Một lệnh điều phối `/dream`; giai đoạn **suy ra** từ dữ liệu, không lưu riêng |
| 10 | Nối Studio ↔ AI | Studio gọi **Gemini API** (API key riêng); đường lùi: nút copy lệnh cho Antigravity |
| 11 | Cấu trúc cảnh | **Không có hook/reveal**; mọi cảnh ngang hàng, liền mạch về không khí |
| 12 | Độ dài cảnh | **Bằng nhau, khoảng 3–4 giây** (số phách chẵn gần 3,5 giây nhất) |
| 13 | Độ dài video | **Khoảng 15–20 giây, 5–6 cảnh**, kết thúc đúng cuối ô nhịp |
| 14 | Bắt buộc | **Mỗi cảnh phải có ảnh đã chốt và clip**; không có đường tắt bỏ qua ảnh hay clip |

Đã thử và loại: điều khiển Antigravity bằng lệnh `antigravity-ide chat`. Lệnh này chỉ bật cửa sổ dùng gần nhất, không gửi câu lệnh tới agent.

## 3. Các giai đoạn của một tập

Giai đoạn **không lưu** mà được suy ra từ `script.json` và file thật mỗi khi cần.

| # | Giai đoạn | Điều kiện để được tính là đang ở giai đoạn này | Bước tiếp |
|---|---|---|---|
| 1 | `idea` | Chưa có `shots` | Viết phân cảnh |
| 2 | `storyboard` | Có `shots`, `storyboard_approved` = false | Duyệt hoặc sửa phân cảnh |
| 3 | `image_prompts` | Đã duyệt, có cảnh thiếu `image_prompt` | Viết prompt ảnh |
| 4 | `images` | Đủ prompt ảnh, có cảnh `locked_image` = null | Tạo, thả và chốt ảnh |
| 5 | `video_prompts` | Đã chốt đủ ảnh, có cảnh thiếu `motion_prompt` hoặc `motion_stale` | Viết prompt video (dựa trên ảnh đã chốt) |
| 6 | `clips` | Đủ prompt video, có cảnh thiếu clip | Tạo và thả clip |
| 7 | `final` | Đủ clip, chưa có `final.mp4` | Dựng (hoặc tải video dựng ở nơi khác lên) |
| 8 | `published` | Có `final.mp4` và `status` = published | Hoàn tất |

Quy trình tuyến tính, **không có đường tắt**: mỗi cảnh bắt buộc có ảnh đã chốt **và** clip.
- Giai đoạn 7 chỉ đạt khi mọi cảnh có `locked_image` và clip.
- Dựng video: trong Studio, **hoặc** ghép ở nơi khác (CapCut…) rồi tải `final.mp4` lên. Nút tải lên chỉ mở khi đã đạt giai đoạn 7.
- Thiếu ảnh chốt hoặc thiếu clip ở bất kỳ cảnh nào → giai đoạn lùi về bước còn thiếu sớm nhất (kể cả khi đã có `final.mp4`; Studio báo video cần dựng lại).

Khi quay lại sửa:
- Thả ảnh mới vào cảnh đã chốt → cảnh **tự bỏ chốt**.
- Bỏ chốt hoặc đổi ảnh sau khi đã có prompt video → cảnh đó và hai cảnh kề bên có `motion_stale` = true; AI chỉ viết lại các cảnh này.
- Sửa phân cảnh **sau khi đã duyệt** → `storyboard_approved` vẫn true; chỉ các cảnh bị sửa bị xóa `image_prompt`, `locked_image`, `motion_prompt` và quay về giai đoạn 3; các cảnh khác giữ nguyên.

## 4. Dữ liệu

### 4.1 `episodes/epNNN/script.json`

Cấp tập (thêm mới):
```json
"version": 7,                       // tăng mỗi lần ghi, dùng để chặn ghi đè
"storyboard_approved": false,
"music_profile": "faded-intro",
"beats_per_scene": 4,               // KHÓA lúc tạo phân cảnh, giống nhau cho mọi cảnh
"concept": { ..., "custom_idea": "ông Moon sửa đồng hồ mặt trời" }  // ý người dùng tự gõ; AI ưu tiên khi có
```
`beats_per_scene` và số cảnh **khóa lại** từ lúc tạo phân cảnh. Đổi BPM sau đó chỉ đổi số giây mỗi cảnh; nếu số giây mới vượt độ dài clip đã có, Studio cảnh báo các cảnh bị ảnh hưởng.
Mỗi cảnh:
```json
{
  "n": 1,
  "angle": "wide",
  "scene_vi": "Ông Moon trên xe nâng, đánh bóng mặt trăng khổng lồ",
  "characters": ["ong-moon"],
  "image_prompt": "...", "negative": "...",
  "locked_image": "images/s01.png",   // null = chưa chốt
  "motion_prompt": "...",
  "motion_stale": false,
  "edited": ["image_prompt"]          // trường người dùng đã sửa tay; AI không ghi đè khi chưa được hỏi
}
```
Bỏ khỏi bản cũ: `role`, `dur`. Độ dài giây được **tính**, không lưu.

### 4.2 `library/music-profiles.json`
```json
{
  "faded-intro": {
    "name": "Faded – Rapid Town Baby (intro không lời)",
    "bpm": 80.0,
    "start_offset": 0.0,
    "intro_seconds": 30.0,
    "note": "Khi đăng: chọn bài trong app, kéo điểm bắt đầu tới start_offset"
  }
}
```
`start_offset` (giây) = vị trí **phách mạnh đầu tiên** của bài, đã cộng phần bù độ lệch của app (đo ở tập đầu). Video luôn bắt đầu đúng phách mạnh; người dùng kéo nhạc trong app tới vị trí này.

Chỉ chứa thông số đo được, **không** chứa file nhạc. Giá trị mặc định khi chưa đo: 80 BPM, `start_offset` 0, intro 30 giây.

### 4.3 `config.json` (thêm)
```json
"music_profile": "faded-intro",
"scene_seconds_target": 3.5,
"video_seconds_target": [15, 20],
"ai_model": ""
```
### 4.4 `%APPDATA%\Dreamnostalgic\secrets.json` (mới, ngoài thư mục dự án)
```json
{ "gemini_api_key": "..." }
```
Đặt ngoài dự án để agent không đọc được và không bị lộ khi chia sẻ/sao lưu thư mục dự án. Không bao giờ được Studio phục vụ qua web; chỉ hiện dạng che (`AIza…xyz`).

## 5. Lưới phách và độ dài

- Thời lượng 1 phách: `b = 60 / bpm`.
- `beats_per_scene`: số chẵn trong {4, 6, 8} cho `beats_per_scene × b` gần `scene_seconds_target` nhất, và không vượt quá độ dài clip tối đa của app video đang chọn trừ 0,5 giây.
- Số cảnh: số nguyên lớn nhất sao cho tổng độ dài ≤ cận trên của `video_seconds_target` và ≤ `intro_seconds − start_offset`, đồng thời tổng số phách là bội của 4 (kết thúc đúng cuối ô nhịp). Tối thiểu 5 cảnh. Nếu không có số cảnh nào vừa ≥ 5 vừa kết thúc đúng ô nhịp (vd. 6 phách/cảnh chỉ cho số cảnh chẵn), ưu tiên **≥ 5 cảnh** và chấp nhận kết thúc giữa ô nhịp; Studio ghi chú điều này.
- Thời điểm cắt thứ k (tính trong video): `t_k = k × beats_per_scene × b`, làm tròn **từng điểm cắt** về khung hình gần nhất (30 fps). Không cộng dồn sai số làm tròn.
- Video bắt đầu tại 0 (tương ứng `start_offset` trong bài nhạc) và kết thúc tại điểm cắt cuối. Mọi cảnh dài bằng nhau tuyệt đối.
- Dựng: mỗi clip bỏ 0,5 giây đầu, lấy đúng độ dài cảnh. Clip thiếu **≤ 10%** → tự làm chậm cho vừa. Thiếu nhiều hơn → báo cảnh cụ thể, đề nghị tạo lại clip.

Ví dụ 80 BPM: `b` = 0,75s → 4 phách = 3,0s; 6 cảnh = 18s.

## 6. Thành phần

### 6.1 `tools/episode_state.py` (mới, bộ não dùng chung)
- `phase(episode)`: suy ra giai đoạn theo mục 3.
- `beat_grid(profile, beats_per_scene, n)`: trả các điểm cắt theo mục 5.
- `plan_storyboard_shape(config, profile, video_tool)`: trả `beats_per_scene` và số cảnh.
- `lock(ep, n)` / `unlock(ep, n)` / `lock_all(ep)`; đánh dấu `motion_stale`.
- `validate(ep, ai_output, kind)`: kiểm tra số cảnh, nhân vật tồn tại, trường bắt buộc; tự sửa lỗi nhỏ; trả lỗi lớn.
- `save(ep, data, expected_version)`: ghi có kiểm tra phiên bản; lưu bản cũ vào `episodes/epNNN/.history/<timestamp>.json`.
- `migrate(script)`: chuyển `script.json` cũ (`dur`, `role`) sang cấu trúc mới.
- Có giao diện dòng lệnh để agent Antigravity gọi (vd. `python tools/episode_state.py phase ep001`).

### 6.2 `library/guides/` (mới, hướng dẫn sáng tạo dùng chung)
- `storyboard.md`: cảnh ngang hàng, không hook/reveal; liền mạch không khí (cùng thế giới, palette, giờ trong ngày hoặc chuyển dần); góc máy luân phiên; cảnh đầu rõ ràng, dễ hiểu.
- `image-prompts.md`: nội dung lấy từ `prompt-writer` hiện tại (công thức cảnh, STYLE BLOCK, khóa ngoại hình, palette).
- `video-prompts.md`: viết dựa trên ảnh đã chốt; một hành động chậm mỗi cảnh; hướng chuyển động liên tục qua hard cut (tránh hai cảnh liền nhau ngược hướng camera); ghi độ dài clip cần tạo.
- `seo.md`: nội dung lấy từ skill `seo-metadata`.

SKILL.md trong `.agent/skills/` chỉ trỏ tới các guide này và thêm bước thao tác (lệnh cần chạy).

### 6.3 `tools/ai.py` (mới)
- Gọi Gemini API bằng thư viện chuẩn Python; key đặt trong header.
- 5 tác vụ: `storyboard` (trả kèm tiêu đề, mô tả, hashtag), `revise_storyboard(feedback)`, `image_prompts(shots?)`, `video_prompts(shots?)` (luôn kèm ảnh đã chốt), `seo` (viết lại riêng tiêu đề/mô tả/hashtag).
- `storyboard` ưu tiên `concept.custom_idea` khi có; ý mới chưa có trong kho chất liệu được trả kèm dưới dạng đề xuất bổ sung kho (người dùng duyệt mới ghi).
- Gửi kèm: guide liên quan, hồ sơ nhân vật dùng trong tập, palette, tool guide của app đang chọn, hình dạng phân cảnh (số cảnh, độ dài).
- `video_prompts` gửi ảnh đã chốt, thu nhỏ còn khoảng 768px JPEG.
- Yêu cầu kết quả JSON đúng khuôn; qua `validate` trước khi ghi; sai thì gửi lại một lần kèm mô tả lỗi.
- Lỗi 429/mạng: thử lại có giãn cách; vẫn lỗi → thông báo tiếng Việt và gợi ý nút copy lệnh.
- `list_models()`: lấy danh sách model hỗ trợ sinh nội dung và nhận ảnh, cho Cài đặt.

### 6.4 Skill `/dream` (Antigravity)
- Thay workflow `/new-episode` (giữ tên cũ làm lối tắt).
- Mỗi lần gọi: đọc tập → `phase` → làm **một** bước → dừng chờ.
- `/dream` không đối số: hỏi làm tiếp tập dở hay tạo tập mới. `/dream ep003`: tiếp tục ep003.

### 6.5 Studio
- Mỗi giai đoạn có nút AI tương ứng: **Viết phân cảnh**, **Sửa phân cảnh** (ô góp ý), **Duyệt phân cảnh**, **Viết prompt ảnh**, **Viết prompt video** (chỉ mở khi đã chốt đủ ảnh); tab Video & đăng có **Viết lại tiêu đề và mô tả**. Mỗi nút AI kèm nút phụ **Copy lệnh cho Antigravity**.
- Tạo tập: ngoài 3 gợi ý và “random”, có ô **gõ ý tưởng riêng** (lưu vào `concept.custom_idea`).
- Đổi BPM khi tập đã có clip: cảnh báo các cảnh có clip ngắn hơn độ dài mới.
- Trước khi AI ghi lên cảnh có `edited`: hỏi "Viết lại tất cả / chỉ cảnh chưa sửa tay"; có thể chọn từng cảnh.
- Tab Cảnh: nút Chốt/Bỏ chốt, Chốt cả bộ, nhãn "Prompt video cần cập nhật", sửa prompt tại chỗ (dấu ✎), khôi phục bản cũ từ `.history`.
- Thanh nhịp: các cảnh trên lưới phách.
- Dựng: cắt theo lưới phách; tùy chọn **tiếng gõ nhịp** cho bản xem thử (tự sinh trên máy). Bản cuối không nhạc.
- Cài đặt: hồ sơ nhạc (BPM có số lẻ, độ lệch phách đầu, độ dài intro), nút nghe tiếng gõ nhịp, độ dài cảnh và video mục tiêu, API key, chọn model.
- Nút AI bị khóa khi đang chạy; ghi bị từ chối khi `version` đã đổi → tải lại và báo.

## 7. Hướng dẫn người dùng về nhạc
1. Tra BPM chính xác của bài trên các trang dữ liệu nhạc; nếu tự đo, đếm số phách cả đoạn intro rồi chia cho thời gian (không dùng gõ 10 lần).
2. Ghi `start_offset` = giây của phách mạnh đầu tiên trong bài (thường 0 hoặc dưới 1 giây).
3. Kiểm tra bằng tai: bật tiếng gõ nhịp trong Studio cùng lúc với bài trên điện thoại (bắt đầu từ `start_offset`); sau 20 giây vẫn trùng là đúng.
4. Khi đăng: chọn bài trong thư viện âm thanh của app, **kéo điểm bắt đầu tới `start_offset`** (Studio hiện con số này ở tab Video & đăng).
5. Tập đầu tiên: đăng chế độ riêng tư, xem điểm cắt sớm hay muộn so với phách, cộng/trừ vào `start_offset` để bù độ lệch của app.

## 8. Xử lý lỗi (tóm tắt)
| Tình huống | Xử lý |
|---|---|
| Chưa có hồ sơ nhạc | Dùng mặc định, Studio nhắc |
| AI trả sai khuôn hoặc sai luật | Tự sửa lỗi nhỏ; gửi lại 1 lần; vẫn sai → không ghi, báo lỗi |
| Hết hạn mức / mất mạng | Thử lại; báo tiếng Việt; gợi ý copy lệnh cho Antigravity |
| Hai nơi cùng ghi | Kiểm tra `version`; từ chối ghi đè, tải lại |
| Clip ngắn | ≤ 10% tự làm chậm; hơn nữa báo cảnh cần tạo lại |
| File bị xóa/đổi ngoài Studio | Giai đoạn suy ra lại từ file thật |
| Tải `final.mp4` khi chưa đủ ảnh chốt và clip | Từ chối, báo cảnh còn thiếu |
| Thay ảnh cảnh đã chốt | Tự bỏ chốt, đánh dấu cảnh cần cập nhật |

## 9. Kiểm thử
1. `episode_state`: đủ 8 giai đoạn; lưới phách ở 72/80/90/79.5 BPM có điểm cắt lệch ≤ ½ khung hình; chọn `beats_per_scene` và số cảnh đúng; khóa/bỏ khóa/stale; chặn ghi đè theo `version`; migrate dữ liệu cũ.
2. `ai.py` với phản hồi giả lập: kết quả đúng, sai khuôn, 429, mất mạng; không gọi API thật.
3. Dựng: đo điểm cắt trong `final.mp4` (clip thử màu khác nhau) so với lưới phách; tiếng gõ nhịp trùng điểm cắt trong 1 khung hình; làm chậm clip thiếu ≤ 10%.
4. Studio: chụp màn hình các giai đoạn ở màn rộng và hẹp.
5. Chạy thật một tập khi có API key.

## 10. Thứ tự xây
| Đợt | Nội dung | Sau đợt này |
|---|---|---|
| 1 | `episode_state.py`, `library/guides/`, `music-profiles.json`, skill `/dream`, dựng theo lưới phách, tiếng gõ nhịp, migrate; server Studio trả thêm số giây tính sẵn để Studio cũ không hỏng | Quy trình mới chạy qua Antigravity |
| 2 | Studio: chốt ảnh, thanh nhịp, sửa prompt tay, lịch sử, hồ sơ nhạc trong Cài đặt | Thao tác đầy đủ trong Studio |
| 3 | `ai.py`, nút AI, API key, chọn model, đường lùi copy lệnh | Bấm nút là AI làm |

## 11. Rủi ro còn lại
- **Điểm bắt đầu nhạc trong app** có thể lệch vài phần mười giây; xử lý bằng đo và bù `start_offset` ở tập đầu, không loại bỏ hoàn toàn được.
- **Bài nhạc có thể không có** trong thư viện của YouTube Shorts; khi đó dùng bài lofi tương tự cùng BPM trên YouTube, giữ bài gốc trên Instagram.
- **Gemini API miễn phí**: hạn mức có thể thay đổi; dữ liệu gửi qua bản miễn phí có thể được Google dùng để cải thiện sản phẩm.

## 12. Ngoài phạm vi
- Chuyển cảnh khác hard cut.
- Ghép nhạc có bản quyền vào video.
- Tự động tạo ảnh/clip qua API của app tạo ảnh/video.
- Tự động đăng lên YouTube.
