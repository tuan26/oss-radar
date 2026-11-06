# Tasks: OSS Radar v1

**Input**: Design documents from `/specs/001-oss-radar-v1/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: chạy song song được (file khác nhau, không phụ thuộc)
- **[Story]**: US1…US7 theo spec.md

## Phase 1: Setup

- [x] T001 Tạo `requirements.txt`, `requirements-dev.txt`, `.gitignore` (data/, .venv)
- [x] T002 [P] Tạo `app/__init__.py`, `app/config.py` (DATA_DIR, HOST, PORT, APP_PASSWORD, APP_URL)
- [x] T003 [P] Chép nguyên văn `reference/knowledge.py`, `reference/curated.py` vào `app/`; chép `reference/sample_data.json` → `app/sample_data.json`

## Phase 2: Foundational

- [x] T004 `app/store.py`: ghi nguyên tử (tmp + os.replace), settings mặc định + merge + che bí mật, results, runs (≤50), ai_cache, history snapshot
- [x] T005 [P] `tests/test_store.py`: ghi nguyên tử, mặc định, che bí mật, giữ key khi không gửi, xóa key
- [x] T006 `app/main.py` khung FastAPI: Basic Auth middleware, GZip, static `/`, `/api/data`, `/api/settings` GET/POST, `/api/sample`; logging filter che bí mật

## Phase 3: US2 — Phân loại license (P1) 🎯

- [x] T007 [P] [US2] `tests/test_license.py`: 10 repo trong `tests/fixtures/licenses.json` (nhãn thật + NOASSERTION), "(đọc từ file)", open-core −4 điểm, không bắt "non-commercial" chung chung, không license → none
- [x] T008 [US2] `app/classify.py` từ reference: import tương đối, chữ ký sớm nhất (R1), GPL-2.0, sao tăng tuần vào điểm sức hút (R8), `is_new`, sửa `auto_strengths`

## Phase 4: US1 — Quét & dashboard không cần AI (P1) 🎯 MVP

- [x] T009 [US1] `app/scanner.py` từ reference: Event dừng (R2), session dùng chung + HEAD probe + pipeline tìm kiếm/chi tiết (R3), thêm tên file license, lỗi 401 tiếng Việt
- [x] T010 [US1] `app/jobs.py` ScanManager: một lần quét/thời điểm, tiến độ 3 giai đoạn, dừng, lịch sử sao, ghi run record, chỉ ghi kết quả khi xong
- [x] T011 [US1] API `/api/scan`, `/api/scan/stop`, `/api/status` trong `app/main.py`
- [x] T012 [P] [US1] `tests/test_pipeline.py`: quét giả lập (mock GitHub search/raw), dừng giữa chừng giữ dữ liệu cũ, không chạy 2 lần cùng lúc
- [x] T013 [US1] `app/static/index.html`: dựa trên mockup — thanh trên (tên, giờ quét, Quét ngay + tiến độ + Dừng, tabs), trạng thái rỗng + nạp mẫu, hồ sơ 11 mục, sáng/tối, lưu ý pháp lý

## Phase 5: US3 — Lọc & theo ngành (P2)

- [x] T014 [US3] Bộ lọc trong `index.html`: tìm theo tính năng, sort sao tăng tuần, chip "mới tuần này", tab Theo ngành nhảy hồ sơ; kiểm 400px

## Phase 6: US4 — AI đa nhà cung cấp (P2)

- [x] T015 [P] [US4] `tests/test_ai.py`: parse JSON (fence, text thừa, hỏng), thông điệp lỗi 401/404/429, payload OpenAI/Anthropic (mock), cache key
- [x] T016 [US4] `app/ai.py` từ reference: `AIError.status`, `enrich()` song song + giới hạn + cache + dừng khi 3 lỗi xác thực đầu (R6)
- [x] T017 [US4] Nối bước AI vào `jobs.py`; ước tính số lần gọi; API `/api/ai/test`, `/api/ai/clear-cache`
- [x] T018 [P] [US4] Test pipeline: lần quét 2 không gọi AI; 3 lỗi 401 đầu → dừng AI, kết quả vẫn lưu
- [x] T019 [US4] Tab Cài đặt — nhóm AI trong `index.html` (preset, URL, model, key ẩn, last4, xóa key, max repo, luồng, kiểm tra, xóa cache, ước tính)

## Phase 7: US5 — Lịch tuần (P2)

- [x] T020 [P] [US5] `tests/test_schedule.py`: next_run "Thứ Hai 07:00" Asia/Ho_Chi_Minh, đổi lịch áp dụng ngay, `missed_run` (≤6h chạy bù, >6h bỏ, đã chạy thì bỏ)
- [x] T021 [US5] Scheduler trong `jobs.py` (CronTrigger, misfire 6h, coalesce, chạy bù khi khởi động); áp dụng khi POST settings
- [x] T022 [US5] Cài đặt — nhóm Lịch + GitHub trong `index.html`; hiển thị lần chạy tới/gần nhất

## Phase 8: US6 — Telegram (P3)

- [x] T023 [P] [US6] `tests/test_notify.py`: nội dung tóm tắt (nhóm license, ≤5 repo mới/tăng sao đạt ngưỡng, APP_URL), lỗi không lộ token
- [x] T024 [US6] `app/notify.py` + gọi sau quét/lỗi trong `jobs.py` + `/api/notify/test` + nhóm Thông báo trong `index.html`

## Phase 9: US7 — Bảo mật & triển khai (P3)

- [x] T025 [P] [US7] `tests/test_api.py`: Basic Auth bật/tắt, không phản hồi API nào chứa bí mật, settings 400 khi múi giờ sai
- [x] T026 [P] [US7] `Dockerfile`, `docker-compose.yml` (8080, ./data, extra_hosts host-gateway), `run.sh`, `run.bat`
- [x] T027 [US7] `README.md` tiếng Việt: cài đặt, key từng hãng, GitHub token, Telegram bot, lịch, Ollama trong Docker, cảnh báo HOST/mật khẩu, sao lưu data/

## Phase 10: Polish

- [x] T028 Chạy app thật: quét giả lập end-to-end qua HTTP, chụp màn hình 400px + desktop (sáng/tối), đo thời gian tải dashboard 500 repo
- [x] T029 Rà quickstart.md, đánh dấu tasks hoàn thành

## Dependencies

- Setup → Foundational → US2 → US1 (MVP) → US3, US4, US5, US6, US7 (độc lập với nhau trừ việc cùng sửa `index.html`/`jobs.py` nên làm tuần tự)
- Test [P] viết trước phần cài đặt tương ứng.

## Implementation Strategy

MVP = Phase 1–4 (quét + license + dashboard không AI). Sau đó thêm lần lượt AI, lịch, Telegram, đóng gói.

## Kết quả implement (2026-11-06)

- `pytest`: 91 test xanh (license 10 repo × 2 kiểu nhãn, AI parse/giao thức/cache/dừng khi lỗi xác thực,
  lịch + chạy bù, store nguyên tử, ẩn bí mật, Basic Auth, quét giả lập end-to-end, dừng ≤ 10s, Telegram).
- Chạy thật với máy chủ GitHub giả lập 474 repo / 19 ngành / 88 truy vấn: 442 repo, 194s ở chế độ có
  token; dashboard tải ~1,0–1,3s; không cuộn ngang ở 400px; không lỗi JS; sáng/tối OK.
- Chưa kiểm được trong sandbox: quét GitHub thật (api.github.com bị chặn), `docker build`
  (không có Docker daemon), gọi AI/Telegram thật.
