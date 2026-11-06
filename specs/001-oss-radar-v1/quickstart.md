# Quickstart & Validation: OSS Radar v1

## Chuẩn bị

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

## 1. Test tự động (tiêu chí nghiệm thu #2, #10)

```bash
pytest -q
```

Kỳ vọng: xanh toàn bộ, gồm 10 repo license, parse JSON AI, lịch chạy tới, chạy bù, store nguyên tử,
ẩn bí mật, cache AI (lần 2 = 0 lần gọi), dừng quét, Telegram.

## 2. Chạy app

```bash
./run.sh            # hoặc run.bat trên Windows, hoặc docker compose up -d
```

Mở http://localhost:8080 → trạng thái rỗng có nút **Quét ngay** và **Xem dữ liệu mẫu**.

## 3. Kịch bản thủ công

| # | Thao tác | Kỳ vọng | Tiêu chí |
|---|---|---|---|
| 1 | Không cấu hình gì, bấm Quét ngay | Tiến độ 3 giai đoạn, xong có dashboard | #1 |
| 2 | Cài đặt → AI → preset Gemini/OpenAI/Ollama, nhập key → Kiểm tra kết nối | "Kết nối thành công"; key sai → lỗi tiếng Việt | #3 |
| 3 | Bật AI, quét 2 lần | Repo an toàn có nguồn "AI: <model>"; lần 2 `ai_calls = 0` trong "Lần chạy gần nhất" | #4 |
| 4 | Lịch: Thứ Hai 07:00 → Lưu | Hiện lần chạy tới; đổi sang phút kế tiếp → job tự chạy | #5 |
| 5 | Bấm Dừng khi đang quét | Dừng ≤ 10s, dữ liệu cũ còn | #6 |
| 6 | Nhập Telegram → Gửi thử, rồi quét | Nhận tin; lần 2 có repo mới/tăng sao | #7 |
| 7 | `APP_PASSWORD=x ./run.sh` | Trình duyệt hỏi mật khẩu; `grep` key trong log/API không thấy | #8 |
| 8 | DevTools 400px | Không cuộn ngang | #9 |

## 4. Đo hiệu năng (cần mạng thật tới GitHub)

Quét đủ 19 ngành không token: thời lượng ở "Lần chạy gần nhất" < 10 phút (có token < 6 phút).
