# AutoCaption VEC

AutoCaption VEC tạo phụ đề tự động cho file audio/video bằng Whisper chạy local và có thể dịch phụ đề sang ngôn ngữ khác bằng Argos Translate.

Dự án bao gồm:
- `scripts/AutoCaptionVEC.py` — ứng dụng GUI standalone (Tkinter) để tạo SRT ngay trong Windows/macOS/Linux.
- `scripts/AutoCaptionVEC_Generate.lua` — script cho DaVinci Resolve, gọi `transcribe_local.py` để tạo phụ đề.
- `scripts/transcribe_local.py` — engine xử lý speech-to-text và dịch thuật.

- ✅ Hoạt động offline sau khi tải model và gói dịch lần đầu
- ✅ Hỗ trợ phát hiện ngôn ngữ tự động hoặc chọn tay
- ✅ Xuất 1 file SRT gốc hoặc 2 file SRT (gốc + dịch)
- ✅ Hỗ trợ Tiếng Việt / English / 中文

---

## Yêu cầu

| Thứ | Mô tả |
|-----|-------|
| Python | 3.9 trở lên |
| Dung lượng | ~1.5GB (model `medium`) hoặc ~3GB (model `large-v3`) |
| Internet | Chỉ cần lần đầu tải model Whisper và gói dịch Argos Translate |

---

## Cài đặt

### Bước 1 — Clone hoặc giải nén repo

```bash
git clone <repo-url>
```

hoặc tải file ZIP rồi giải nén.

### Bước 2 — Cài thư viện Python

```bash
pip install -r requirements.txt
```

Nếu muốn dùng tính năng dịch, cài thêm:

```bash
pip install argostranslate
```

> Lưu ý: `requirements.txt` hiện chỉ chứa `faster-whisper` và một số thư viện hỗ trợ. Thư viện `argostranslate` cần cài riêng nếu bạn dùng tùy chọn dịch.

---

## Chạy standalone app

```bash
python scripts/AutoCaptionVEC.py
```

Hoặc dùng `python3` nếu hệ thống của bạn yêu cầu.

### Sử dụng app

1. Chọn file đầu vào audio/video.
2. Chọn thư mục lưu kết quả.
3. Chọn ngôn ngữ nguồn hoặc `Auto-detect`.
4. Chọn model Whisper.
5. Chọn `1 File` (chỉ SRT gốc) hoặc `2 Files` (gốc + dịch).
6. Nếu chọn `2 Files`, chọn ngôn ngữ dịch.
7. Bấm `Generate Subtitles` và chờ hoàn tất.

Kết quả được lưu trong thư mục đầu ra, với tên file dựa trên tên file nguồn.

---

## Chạy trong DaVinci Resolve

1. Copy `scripts/AutoCaptionVEC_Generate.lua` và `scripts/transcribe_local.py` vào cùng thư mục Scripts của Resolve.
2. Mở DaVinci Resolve và mở project cần tạo phụ đề.
3. Vào **Workspace → Scripts → AutoCaptionVEC_Generate**.
4. Chọn file audio/video nguồn.
5. Chọn ngôn ngữ, model, số file xuất, và nếu cần chọn ngôn ngữ dịch.
6. Bấm **OK** và chờ xử lý.

Nếu import SRT vào Media Pool/Timeline không thành công, script sẽ thông báo đường dẫn file SRT để bạn import thủ công.

---

## Kích thước model Whisper

| Model | Dung lượng | Tốc độ (CPU) | Độ chính xác |
|-------|-----------|--------------|--------------|
| tiny | ~75MB | Rất nhanh | Thấp |
| base | ~145MB | Nhanh | Khá |
| small | ~460MB | Khá nhanh | Tốt |
| **medium** ⭐ | ~1.5GB | Trung bình | Tốt |
| large-v3 | ~3GB | Chậm | Cao nhất |

> Khuyến nghị dùng model `medium` cho máy không có GPU rời.

---

## Dịch thuật (File 2)

Khi chọn `2 Files`, ứng dụng sẽ dịch phụ đề sang ngôn ngữ đích bằng `argostranslate`.

- Lần đầu dịch một cặp ngôn ngữ mới, Argos Translate sẽ tải gói ngôn ngữ (cần internet).
- Sau khi tải xong, dịch thuật sẽ hoạt động offline.
- Nếu phần dịch thất bại với một đoạn, script sẽ giữ nguyên bản gốc và tiếp tục.
- Nếu không tìm thấy gói dịch cho cặp ngôn ngữ yêu cầu, script sẽ báo lỗi rõ ràng.

### Ngôn ngữ dịch

- Standalone app: English, Vietnamese, Chinese
- DaVinci Resolve mode: English, Vietnamese, Chinese, Spanish, French, German, Japanese, Korean

---

## Cấu trúc thư mục

```
AutoCaptionVEC/
├── scripts/
│   ├── AutoCaptionVEC.py
│   ├── AutoCaptionVEC_Generate.lua
│   └── transcribe_local.py
├── requirements.txt
└── README.md
```

---

## Cấu hình nâng cao

Mở `scripts/AutoCaptionVEC_Generate.lua`, sửa dòng:

```lua
local PYTHON_EXE = "python"  -- đổi thành "python3" nếu cần (thường trên macOS)
```

---

## Troubleshooting

| Lỗi | Giải pháp |
|-----|-----------|
| `faster-whisper not installed` | Chạy `pip install -r requirements.txt` |
| `argostranslate not installed` | Chạy `pip install argostranslate` |
| Không tìm thấy gói dịch | Kiểm tra internet, Argos cần tải gói lần đầu |
| Script chạy quá chậm | Đổi sang model `small` hoặc `base` |
| Không tạo được file SRT | Kiểm tra quyền ghi và thư mục đầu ra |
| Phụ đề không tự thêm vào timeline | Kéo thủ công file `.srt` từ Media Pool vào timeline |

---

## License

MIT
