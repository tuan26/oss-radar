<!--
Sync Impact Report
- Version change: (template) → 1.0.0
- Principles defined: I. Pháp lý license là trên hết; II. Chạy được khi không có AI;
  III. Trung lập nhà cung cấp AI; IV. Bí mật nằm yên trên máy người dùng;
  V. Tự host đơn giản; VI. Tiếng Việt cho người không chuyên; VII. Kiểm thử bắt buộc
- Added sections: Ràng buộc kỹ thuật; Quy trình phát triển
- Removed sections: none
- Templates: plan/spec/tasks templates read this file at runtime — no edits needed
- Deferred TODOs: none
-->
# OSS Radar Constitution

## Core Principles

### I. Pháp lý license là trên hết (NON-NEGOTIABLE)
- Phân loại license MUST dựa trên nội dung file LICENSE, không chỉ nhãn SPDX của GitHub.
- Khi nghi ngờ, MUST xếp vào nhóm thận trọng hơn (`unknown` / `restricted`), không bao giờ
  "nâng" một repo lên nhóm an toàn hơn khi không có bằng chứng.
- Mỗi repo MUST có link trực tiếp tới file license, và giao diện MUST luôn hiển thị lưu ý
  pháp lý (NFR-6).
- Bộ 10 repo kiểm thử trong REQUIREMENTS §5.2 MUST luôn pass.
Lý do: sai license = khách hàng của người dùng gặp rủi ro pháp lý; đó là giá trị cốt lõi của app.

### II. Chạy được khi không có AI
- Mọi luồng chính (quét, phân loại, chấm điểm, dashboard, lịch, thông báo) MUST hoạt động khi
  chế độ AI là "Không dùng AI" và không có GitHub token.
- AI chỉ là lớp làm giàu (tóm tắt tiếng Việt); lỗi AI MUST NOT làm hỏng lần quét.
- Nội dung do AI sinh MUST ghi rõ nguồn ("AI: <model>").

### III. Trung lập nhà cung cấp AI
- Gọi AI MUST bằng HTTP thuần (`requests`), không dùng SDK của hãng nào.
- Hỗ trợ đúng hai giao thức: OpenAI-compatible Chat Completions và Anthropic Messages.
- Kết quả AI MUST được cache theo `repo + hash(README + mô tả)` để không gọi lại khi không đổi.

### IV. Bí mật nằm yên trên máy người dùng
- API key, GitHub token, Telegram token chỉ lưu trong `data/`; MUST NOT xuất hiện trong log,
  phản hồi API hay HTML. API chỉ trả 4 ký tự cuối.
- Mặc định bind `127.0.0.1`; `APP_PASSWORD` bật HTTP Basic Auth cho toàn bộ app.

### V. Tự host đơn giản, bền bỉ
- Một tiến trình Python (FastAPI + APScheduler), lưu file JSON trong `data/`, frontend là một
  file HTML + JS thuần không cần build.
- Ghi dữ liệu MUST theo kiểu file tạm rồi `os.replace` (nguyên tử).
- Lỗi ở một repo (mạng, AI) MUST NOT làm hỏng cả lần quét; dừng quét MUST giữ dữ liệu cũ.
- YAGNI: không thêm DB server, hàng đợi, hay framework frontend.

### VI. Tiếng Việt cho người không chuyên
- Toàn bộ giao diện, thông báo lỗi, README bằng tiếng Việt dễ hiểu, kèm gợi ý cách sửa.
- Giao diện MUST dùng được ở chiều rộng 400px và có chế độ sáng/tối.

### VII. Kiểm thử bắt buộc cho logic lõi
- Test tự động (pytest) MUST có cho: phân loại license, parse JSON AI, tính lịch chạy tới,
  store ghi nguyên tử, ẩn bí mật trong API.
- Test MUST chạy offline (không gọi GitHub/AI thật); dùng fixture license mẫu và mock HTTP.

## Ràng buộc kỹ thuật

- Python 3.11+, FastAPI, Uvicorn, APScheduler 3.x, `requests`. Không dependency nặng khác
  nếu không cần thiết.
- Tái sử dụng code trong `reference/` (scanner, classify, knowledge, curated, ai) thay vì viết lại;
  chỉ sửa khi có lỗi hoặc cần tích hợp.
- Bộ tri thức ngành (`knowledge.py`) và tóm tắt tay (`curated.py`) nằm ở file riêng, dễ sửa tay.
- Đóng gói: Dockerfile + docker-compose (cổng 8080, volume `./data`), `run.sh`, `run.bat`.

## Quy trình phát triển

- Theo Spec Kit: constitution → specify → plan → tasks → implement.
- Mỗi thay đổi lõi (license, AI parse, lịch) đi kèm test; `pytest` MUST xanh trước khi commit.
- Tiêu chí nghiệm thu REQUIREMENTS §8 là định nghĩa "xong" của v1.

## Governance

Constitution này đứng trên mọi quy ước khác của dự án. Sửa đổi phải ghi trong Sync Impact Report,
tăng version theo semver (MAJOR: bỏ/định nghĩa lại nguyên tắc; MINOR: thêm nguyên tắc/mục;
PATCH: diễn đạt). Mọi plan phải qua "Constitution Check"; vi phạm phải được biện minh trong
mục Complexity Tracking của plan.

**Version**: 1.0.0 | **Ratified**: 2026-11-06 | **Last Amended**: 2026-11-06
