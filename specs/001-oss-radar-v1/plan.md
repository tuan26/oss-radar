# Implementation Plan: OSS Radar v1

**Branch**: `001-oss-radar-v1` | **Date**: 2026-11-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-oss-radar-v1/spec.md`

## Summary

Web app tự host quét GitHub theo 19 ngành, phân loại license từ nội dung file LICENSE, chấm điểm,
gắn playbook bán hàng cho SME Việt Nam và (tùy chọn) tóm tắt tiếng Việt bằng AI của bất kỳ nhà cung
cấp nào. Cách làm: một tiến trình FastAPI phục vụ REST API + một trang HTML thuần; quét chạy trong
thread nền (một lần quét tại một thời điểm, dừng được); APScheduler lo lịch tuần; dữ liệu là file
JSON ghi nguyên tử trong `data/`. Tái sử dụng code `reference/` với các bản sửa lỗi nêu ở
[research.md](./research.md).

## Technical Context

**Language/Version**: Python 3.11+ (test trên 3.13)

**Primary Dependencies**: FastAPI, Uvicorn, APScheduler 3.10.x, requests, tzdata (múi giờ trên Windows/slim)

**Storage**: File JSON trong `data/` (settings, results, runs, ai_cache, history/YYYY-MM-DD.json)

**Testing**: pytest + FastAPI TestClient (httpx); HTTP ngoài được mock, không gọi mạng thật

**Target Platform**: Linux/macOS/Windows, Docker (python:3.12-slim)

**Project Type**: web-service + SPA tĩnh một file

**Performance Goals**: quét ~500 repo < 10 phút (không token) / < 6 phút (có token), chưa tính AI;
`/api/data` + render 500 repo < 2s

**Constraints**: chạy không AI, không token; bí mật không rời `data/`; dừng quét ≤ 10s; bind 127.0.0.1 mặc định

**Scale/Scope**: 1 người dùng, ~500 repo/lần quét, ~1 MB JSON kết quả

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Cách plan đáp ứng | Trạng thái |
|---|---|---|
| I. Pháp lý license | Đọc nội dung LICENSE; sửa lỗi nhận diện GPL/LGPL→AGPL; test 10 repo bằng license thật làm fixture | ✅ |
| II. Chạy không AI | AI là bước 3 tùy chọn; mặc định `none`; lỗi AI cô lập theo repo | ✅ |
| III. Trung lập AI | `requests` thuần, 2 giao thức, cache theo hash nội dung | ✅ |
| IV. Bí mật | Chỉ trong `data/settings.json`; API trả `*_last4`; lọc log; thông điệp lỗi mạng không chứa URL có token | ✅ |
| V. Tự host đơn giản | 1 tiến trình, JSON + `os.replace`, HTML thuần, không DB server | ✅ |
| VI. Tiếng Việt | Toàn bộ UI/lỗi tiếng Việt; CSS mobile-first, kiểm 400px | ✅ |
| VII. Kiểm thử | pytest cho license, parse JSON, lịch, store, ẩn bí mật, cache AI, notify | ✅ |

Re-check sau Phase 1: không phát sinh vi phạm (không thêm DB, không SDK AI, không framework FE).

## Project Structure

### Documentation (this feature)

```text
specs/001-oss-radar-v1/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/api.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
app/
├── __init__.py
├── main.py          # FastAPI: route API, Basic Auth, phục vụ static, khởi động scheduler
├── config.py        # biến môi trường: DATA_DIR, HOST, PORT, APP_PASSWORD, APP_URL
├── store.py         # đọc/ghi nguyên tử settings, results, runs, ai_cache, history
├── scanner.py       # từ reference/scanner.py (+ dừng nhanh, session dùng chung, HEAD probe)
├── classify.py      # từ reference/classify.py (+ sửa chữ ký license, sao tăng tuần vào điểm)
├── knowledge.py     # nguyên văn reference
├── curated.py       # nguyên văn reference
├── ai.py            # từ reference/ai.py (+ AIError.status, enrich song song, dừng khi lỗi xác thực)
├── jobs.py          # ScanManager (thread, tiến độ, dừng), lịch APScheduler, chạy bù
├── notify.py        # Telegram
├── sample_data.json # dữ liệu mẫu để xem thử
└── static/index.html
tests/
├── fixtures/licenses.json   # license thật của 10 repo kiểm thử (lấy qua raw.githubusercontent.com)
├── test_license.py
├── test_ai.py
├── test_schedule.py
├── test_store.py
├── test_api.py
├── test_pipeline.py         # quét giả lập end-to-end (mock GitHub), lịch sử sao, cache AI
└── test_notify.py
Dockerfile, docker-compose.yml, requirements.txt, run.sh, run.bat, README.md
```

**Structure Decision**: Một package Python `app/` đúng cấu trúc gợi ý trong REQUIREMENTS §4;
frontend là file tĩnh trong `app/static/`, không có bước build.

## Complexity Tracking

Không có vi phạm cần biện minh.
