# Research: OSS Radar v1

## R1. Nhận diện license chuẩn khi nhãn là NOASSERTION

- **Phát hiện**: chạy `reference/classify.py` trên license thật (lấy qua raw.githubusercontent.com,
  lưu ở `tests/fixtures/licenses.json`) → `odoo/odoo` (LGPL-3.0) và `frappe/erpnext` khi nhãn là
  NOASSERTION bị xếp **agpl**. Lý do: văn bản GPL-3.0 (và LGPL kèm GPL) có điều 13 "Use with the
  GNU Affero General Public License", mà code mẫu duyệt `TEXT_SIGNATURES` theo thứ tự danh sách.
- **Decision**: chọn chữ ký có **vị trí xuất hiện sớm nhất** trong văn bản (tiêu đề license luôn ở đầu).
  Thêm nhận diện GPL-2.0 ("version 2, june 1991"). Thêm `license.txt`, `COPYING.md`, `LICENSE-MIT`
  vào danh sách file thử (erpnext dùng `license.txt`).
- **Rationale**: đơn giản, xác định, không cần NLP; khớp 10/10 repo kiểm thử.
- **Alternatives**: so khớp toàn văn với kho SPDX (nặng, cần dữ liệu ngoài); chỉ đọc 2.000 ký tự
  đầu (hỏng khi license có lời dẫn dài như twenty).
- `twentyhq/twenty` được gắn cờ enterprise ("@license Enterprise" + Enterprise Edition trong
  LICENSE) — đúng thực tế, nhóm vẫn là `agpl` như bảng kiểm thử yêu cầu.

## R2. Dừng quét trong ≤ 10 giây

- **Decision**: dùng `threading.Event`; mọi chỗ chờ (`time.sleep` giãn cách 6,5s, chờ reset rate
  limit tới 70s) đổi thành `stop.wait(n)`; `_raw` kiểm tra cờ dừng trước mỗi request; executor
  `shutdown(cancel_futures=True)`; timeout request đọc 15s. Kết quả chỉ ghi khi cả lần quét hoàn tất.
- **Alternatives**: kill thread (Python không hỗ trợ an toàn); process riêng (phức tạp, trái nguyên tắc V).

## R3. Hiệu năng đọc chi tiết

- **Decision**: một `requests.Session` dùng chung với `HTTPAdapter(pool_maxsize=16)` (keep-alive),
  12 luồng; kiểm tra tồn tại file Docker/enterprise bằng `HEAD`; dừng thử tên license khi tìm thấy.
  ~25 request/repo × 500 repo / 12 luồng ≈ 3–5 phút; phần tìm kiếm 88 truy vấn (44 topic × 2) × 6,5s ≈ 9,5 phút
  không token (≈ 3,2 phút có token). Giãn cách tính từ lúc bắt đầu request trước (thời gian request nằm trong khoảng chờ). Phần tìm kiếm và đọc chi tiết chạy tuần tự nên ở chế độ không
  token tổng thời gian sát ngưỡng 10 phút → **chồng lấp**: đọc chi tiết repo ngay khi truy vấn
  tìm kiếm trả về (pipeline), chỉ phần gộp ngành chờ cuối.
- **Ghi chú môi trường**: sandbox phát triển chặn `api.github.com`; hiệu năng thật cần đo trên máy
  người dùng (quickstart bước 7).

## R4. Lịch tuần và chạy bù

- **Decision**: `BackgroundScheduler(timezone=...)`, job id `weekly`, `CronTrigger(day_of_week,
  hour, minute, timezone)`, `misfire_grace_time=6h`, `coalesce=True`, `replace_existing=True` khi
  lưu cài đặt (áp dụng ngay). Jobstore trong bộ nhớ không nhớ lần lỡ sau khi tắt máy, nên khi khởi
  động app tự kiểm tra: lần hẹn gần nhất trong quá khứ (≤ 6 giờ) mà chưa có lần chạy nào bắt đầu sau
  thời điểm đó → chạy bù một lần. Hàm thuần `next_run()` / `missed_run()` để test.
- **Alternatives**: SQLAlchemyJobStore (thêm dependency + DB chỉ để nhớ 1 job).

## R5. Lưu trữ

- **Decision**: JSON + ghi file tạm cùng thư mục rồi `os.replace` (nguyên tử trên POSIX và Windows),
  khóa `threading.RLock` trong tiến trình. Ảnh chụp sao: `data/history/YYYY-MM-DD.json`.
- **Alternatives**: SQLite (được phép, nhưng ~500 bản ghi đọc nguyên khối, JSON đơn giản hơn).

## R6. AI

- **Decision**: giữ `reference/ai.py`; `AIError` thêm `status`; enrich chạy `ThreadPoolExecutor(n)`
  theo thứ tự điểm; nếu 3 kết quả đầu tiên đều là lỗi xác thực (401/403) → bật cờ hủy, các task còn
  lại bỏ qua. Cache `data/ai_cache.json` theo `cache_key()`; cache được áp dụng cả khi đã tắt AI (không
  tốn phí). `parse_json` chịu fence + text thừa; thêm fallback cắt tới `}` cuối.
- Kiểm tra kết nối dùng cấu hình gửi kèm; nếu không gửi key thì dùng key đã lưu.

## R7. Bí mật

- **Decision**: API chỉ trả `{field}_set` + `{field}_last4`. Lỗi mạng chỉ báo tên lớp exception
  (URL Telegram chứa token). Logging filter thay mọi bí mật đã lưu bằng `***`. Basic Auth:
  `secrets.compare_digest`, bất kỳ username.

## R8. Sao tăng tuần & repo mới

- **Decision**: lấy ảnh chụp gần nhất có ngày < hôm nay; `weekly_delta = stars − prev`;
  `is_new = repo không có trong ảnh chụp đó` (chỉ khi có ảnh chụp). Điểm sức hút: phần tốc độ
  (tối đa 5) dùng `weekly_delta / số ngày giữa hai ảnh chụp` thay cho trung bình sao/ngày từ khi tạo.
  Sửa lỗi `auto_strengths` dùng `.replace(",", ".")` trên cả câu (biến dấu phẩy câu thành dấu chấm).
