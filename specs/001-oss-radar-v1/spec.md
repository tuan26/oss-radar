# Feature Specification: OSS Radar v1 — radar repo mã nguồn mở cho SME Việt Nam

**Feature Branch**: `001-oss-radar-v1`

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "OSS Radar — Yêu cầu phần mềm (v1.0)" (bản đầy đủ: `docs/REQUIREMENTS.md`)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Quét lần đầu và xem kết quả không cần cấu hình (Priority: P1)

Người dùng cài app, mở trình duyệt, thấy hướng dẫn và nút **Quét ngay**. Bấm nút, app tìm repo
trên GitHub theo 19 ngành, đọc license/README, phân loại license, chấm điểm và hiển thị dashboard:
danh sách repo, thanh phân bố license, hồ sơ chi tiết trả lời 5 câu hỏi (được bán không? làm gì?
bán cho ai? tiếp cận thế nào? cần sửa gì cho VN?).

**Why this priority**: Đây là giá trị cốt lõi; không có nó app vô dụng. Phải chạy khi không có AI
và không có GitHub token.

**Independent Test**: Cài mới, không nhập gì, bấm Quét ngay → sau khi xong dashboard có repo,
mỗi repo có nhóm license, mô hình kinh doanh, điểm, playbook.

**Acceptance Scenarios**:

1. **Given** app mới cài, chưa có dữ liệu, **When** mở trang chủ, **Then** thấy trạng thái rỗng
   có hướng dẫn, nút Quét ngay và lựa chọn nạp dữ liệu mẫu.
2. **Given** chưa cấu hình AI/token, **When** bấm Quét ngay, **Then** thanh tiến độ hiện giai đoạn
   (tìm kiếm / đọc chi tiết / AI), `done/total`, thời gian đã chạy; khi xong dashboard hiển thị kết quả.
3. **Given** đang quét, **When** bấm Quét ngay lần nữa, **Then** không khởi chạy lần quét thứ hai mà
   hiện tiến độ hiện tại.
4. **Given** đang quét và đã có kết quả cũ, **When** bấm Dừng, **Then** quét dừng trong ~10 giây và
   dữ liệu cũ còn nguyên.
5. **Given** có kết quả, **When** chọn một repo, **Then** hồ sơ hiển thị đủ 11 mục theo thứ tự
   (thông tin nhanh → mô hình kinh doanh + link license → tính năng (ghi nguồn) → điểm mạnh → điểm
   5 thành phần → ngách → khách hàng/kênh/câu mở lời → kế hoạch 12 tuần → cải tiến VN → đối thủ/giá
   /rủi ro dữ liệu → rủi ro).

---

### User Story 2 - Phân loại license đáng tin cậy (Priority: P1)

Người dùng cần biết chắc repo nào được phép đóng gói bán dịch vụ và theo mô hình nào. App đọc nội
dung file LICENSE (không chỉ nhãn GitHub), xếp vào 7 nhóm: permissive, gpl, agpl, single-tenant,
restricted, none, unknown; phát hiện open-core; repo bị loại mặc định bị ẩn.

**Why this priority**: Sai license là rủi ro pháp lý thật cho người dùng.

**Independent Test**: Chạy bộ test với license mẫu của 10 repo chuẩn → 100% đúng nhóm.

**Acceptance Scenarios**:

1. **Given** license của n8n, nocodb, akaunting, invoiceninja, **Then** nhóm `restricted`.
2. **Given** license của dify, **Then** `single-tenant`.
3. **Given** chatwoot (MIT + thư mục `enterprise/`), **Then** `permissive` kèm ghi chú enterprise và
   bị trừ 4 điểm license.
4. **Given** twenty → `agpl`; odoo → `permissive` (LGPL); erpnext → `gpl`; documenso → `agpl` kèm enterprise.
5. **Given** nhãn GitHub `NOASSERTION` nhưng văn bản là AGPL, **Then** nhãn hiển thị
   "AGPL-3.0 (đọc từ file)".
6. **Given** license chỉ nhắc chung chung "non-commercial", **Then** không bị xếp `restricted`.

---

### User Story 3 - Lọc, sắp xếp và xem theo ngành (Priority: P2)

Người dùng tìm kiếm (tên, mô tả, tính năng), lọc theo ngành, các chip (ẩn repo bị loại, chỉ SaaS
thoải mái, mới nổi, mới tuần này, có tóm tắt tiếng Việt), sắp xếp (điểm, phù hợp VN, số sao, sao
tăng trong tuần). Tab "Theo ngành" hiển thị thẻ mỗi ngành với 4 repo an toàn tốt nhất; bấm vào repo
nhảy sang hồ sơ.

**Independent Test**: Nạp dữ liệu mẫu 474 repo, thao tác bộ lọc trên màn hình 400px và desktop.

**Acceptance Scenarios**:

1. **Given** dữ liệu mẫu, **When** gõ "kanban", **Then** chỉ còn repo có từ đó trong tên/mô tả/tính năng.
2. **Given** tab Theo ngành, **When** bấm một repo, **Then** chuyển sang tab Theo repo với hồ sơ repo đó.
3. **Given** màn hình rộng 400px, **Then** không có thanh cuộn ngang, mọi chức năng dùng được.

---

### User Story 4 - Tóm tắt tiếng Việt bằng AI của bất kỳ nhà cung cấp nào (Priority: P2)

Người dùng chọn preset (OpenAI, Gemini, DeepSeek, OpenRouter, Groq, Ollama, LM Studio, Anthropic,
Khác), sửa base URL/model, nhập key, bấm **Kiểm tra kết nối**. Khi quét, các repo an toàn license
chưa có tóm tắt tay (ưu tiên điểm cao, tối đa N repo) được AI tóm tắt: tính năng, điểm mạnh, gợi ý
ngách, cải tiến VN; ghi nguồn "AI: <model>". Lần quét sau không gọi lại AI cho repo không đổi.

**Independent Test**: Dùng máy chủ AI giả lập; quét 2 lần, đếm số lần gọi AI lần 2 = 0 cho repo không đổi.

**Acceptance Scenarios**:

1. **Given** key đúng, **When** Kiểm tra kết nối, **Then** báo thành công.
2. **Given** key sai, **When** Kiểm tra kết nối, **Then** báo lỗi tiếng Việt kèm gợi ý ("API key sai
   hoặc hết hạn").
3. **Given** AI trả JSON bọc trong markdown fence, **Then** vẫn đọc được.
4. **Given** 3 repo đầu đều lỗi xác thực, **Then** dừng bước AI, giữ kết quả quét, báo lỗi rõ.
5. **Given** chế độ "Không dùng AI" (mặc định), **Then** hồ sơ vẫn có tính năng trích README
   ("chưa dịch"), tóm tắt tay, điểm mạnh tự suy.
6. **Given** trước khi quét, **Then** thấy ước tính số lần gọi AI (= số repo cần tóm tắt − số đã cache).

---

### User Story 5 - Lịch quét hằng tuần và lịch sử sao (Priority: P2)

Người dùng bật lịch, chọn thứ, giờ, phút, múi giờ (mặc định Asia/Ho_Chi_Minh) và lưu; lịch áp dụng
ngay. Giao diện hiện lần chạy tới và lần chạy gần nhất (thời điểm, thành công/lỗi, số repo, số repo
AI tóm tắt, thời lượng). Mỗi lần quét lưu ảnh chụp số sao để tính sao tăng trong tuần và đánh dấu
repo mới xuất hiện. Máy tắt lúc hẹn thì chạy bù khi bật lại (trong vòng ~6 giờ).

**Independent Test**: Đặt "Thứ Hai 07:00" → lần chạy tới đúng; đổi sang 1 phút sau giờ hiện tại →
job tự chạy, không khởi động lại.

**Acceptance Scenarios**:

1. **Given** lịch Thứ Hai 07:00 Asia/Ho_Chi_Minh, **Then** "lần chạy tới" là Thứ Hai gần nhất 07:00.
2. **Given** có ảnh chụp lần trước, **When** quét xong, **Then** mỗi repo có "sao tăng trong tuần" và
   repo chưa có trong ảnh chụp trước được đánh dấu "mới".

---

### User Story 6 - Thông báo Telegram (Priority: P3)

Người dùng nhập bot token + chat ID, bấm Gửi thử. Sau mỗi lần quét nhận tin tóm tắt: tổng repo,
số repo theo nhóm license, tối đa 5 repo an toàn đạt ngưỡng điểm (mặc định 75) là mới hoặc tăng sao
mạnh nhất, link mở app. Quét lỗi thì nhận thông báo lỗi.

**Independent Test**: Mock Telegram API; kiểm tra nội dung tin nhắn sau quét lần 1 và lần 2.

**Acceptance Scenarios**:

1. **Given** token/chat ID đúng, **When** Gửi thử, **Then** nhận tin.
2. **Given** lần quét thứ hai, **Then** tin nhắn liệt kê repo mới hoặc tăng sao.

---

### User Story 7 - Chạy an toàn trên VPS (Priority: P3)

Người dùng triển khai bằng Docker hoặc script; đặt mật khẩu để bảo vệ khi mở ra Internet.

**Acceptance Scenarios**:

1. **Given** biến `APP_PASSWORD`, **When** mở app, **Then** bị hỏi mật khẩu cho mọi trang và API.
2. **Given** đã lưu key, **Then** không phản hồi API/log nào chứa key đầy đủ (chỉ 4 ký tự cuối).
3. **Given** không đặt `HOST`, **Then** app chỉ nghe ở 127.0.0.1.

### Edge Cases

- GitHub trả 403/429 (giới hạn tốc độ): chờ theo thời điểm reset rồi thử lại.
- GitHub token sai (401): dừng quét, báo "GitHub token không hợp lệ".
- Mạng lỗi khi đọc một repo: bỏ qua repo/file đó, quét tiếp.
- Tắt máy ngang khi đang ghi dữ liệu: file kết quả cũ không bị hỏng.
- AI trả về văn bản không phải JSON: repo đó giữ tóm tắt README, quét tiếp.
- Hết quota AI giữa chừng: lỗi từng repo không làm hỏng lần quét.
- Repo không phải ứng dụng (awesome list, SDK, tutorial...) bị loại, trừ khi có docker-compose.
- Repo nằm ở nhiều ngành: chỉ xuất hiện một lần, chọn ngành phù hợp nhất.
- Lưu cài đặt mà không gửi trường key: key cũ giữ nguyên; có nút xóa key riêng.
- Múi giờ nhập sai: báo lỗi, không lưu.

## Requirements *(mandatory)*

### Functional Requirements

Mã yêu cầu ánh xạ trực tiếp tới `docs/REQUIREMENTS.md`.

- **FR-SCAN-1..8**: Quét 19 ngành (2 truy vấn/topic: top ≥ min_stars 20 repo; mới nổi 18 tháng, ≥300
  sao, 10 repo), gộp trùng, đọc LICENSE/README/Docker/thư mục enterprise qua kênh không tốn quota,
  token tùy chọn với giãn cách 6,5s/2,2s, đọc song song ~12 luồng, tiến độ 3 giai đoạn, dừng được,
  trích tính năng từ README, loại repo không phải ứng dụng.
- **FR-LIC-1..4**: Phân loại 7 nhóm từ nội dung license; nhận diện license chuẩn khi nhãn
  NOASSERTION; phát hiện open-core (−4 điểm); link file license; chỉ bắt cụm cấm thương mại rõ ràng.
- **FR-SCORE**: Điểm 0–100 = License (30) + Hoạt động (15) + Sức hút (15, dùng sao tăng tuần nếu có
  lịch sử) + Dễ tự host (15) + Phù hợp VN (25); nhóm bị loại tối đa 25 điểm và ẩn mặc định.
- **FR-KB-1..3**: Tri thức 19 ngành từ file riêng sửa tay được; sinh kế hoạch 12 tuần, cải tiến VN, rủi ro.
- **FR-AI-1..9**: Hai giao thức (OpenAI-compatible, Anthropic), preset + "Khác", mặc định không AI,
  tóm tắt JSON cố định, giới hạn số repo (mặc định 60) và số luồng (mặc định 3), cache theo nội dung,
  nút xóa cache, xử lý lỗi (fence, lỗi lẻ, 3 lỗi xác thực đầu → dừng AI), nút kiểm tra kết nối,
  ghi nguồn tóm tắt.
- **FR-JOB-1..6**: Quét ngay (một lần quét tại một thời điểm), tiến độ cập nhật ~2s với nút Dừng,
  lịch tuần chỉnh trên giao diện áp dụng ngay, hiển thị lần chạy tới/gần nhất, ảnh chụp sao theo
  ngày, chạy bù khi lỡ giờ (≤6 giờ, gộp lần lỡ).
- **FR-NOTI-1..3**: Telegram tùy chọn, gửi thử, tóm tắt sau quét, báo lỗi quét.
- **FR-UI**: Tiếng Việt, sáng/tối, dùng tốt ở 400px; thanh trên (tên app, giờ quét gần nhất, Quét
  ngay + tiến độ, 3 tab); tab Theo repo / Theo ngành / Cài đặt như REQUIREMENTS §5.8; trạng thái rỗng
  có hướng dẫn và nạp dữ liệu mẫu; lưu ý pháp lý luôn hiển thị.
- **NFR-1..6**: Bí mật chỉ trong `data/`, không log/không trả về; Basic Auth qua `APP_PASSWORD`;
  mặc định 127.0.0.1; quét <10 phút không token / <6 phút có token (chưa tính AI); dashboard
  <2s với 500 repo; ghi nguyên tử; ước tính số lần gọi AI; tiếng Việt; lưu ý pháp lý.

### Key Entities

- **Settings**: cấu hình AI (preset, kind, base URL, model, key, max repo, số luồng), lịch (bật,
  thứ, giờ, phút, múi giờ), GitHub (token, min sao, ngành), Telegram (token, chat ID, ngưỡng điểm).
- **ScanResult**: thời điểm quét, danh sách Repo, thống kê theo nhóm license, tri thức ngành.
- **Repo**: tên, link, mô tả, sao, ngành, nhóm license + mô hình kinh doanh + link license, thư mục
  enterprise, điểm 5 thành phần, thông tin kỹ thuật (Docker, tiếng Việt, ngày commit, sao/ngày,
  sao tăng tuần), cờ mới nổi / mới tuần này, tính năng, điểm mạnh, nguồn tóm tắt, gợi ý ngách AI,
  cải tiến, rủi ro.
- **StarSnapshot**: ngày → {repo: số sao}.
- **RunRecord**: lần chạy (bắt đầu, kết thúc, kết quả, lỗi, số repo, số repo AI tóm tắt, nguồn kích hoạt).
- **AICacheEntry**: khóa (repo + hash nội dung) → tóm tắt + model.
- **CategoryKnowledge**: nhu cầu, cạnh tranh, rủi ro dữ liệu, khách hàng, ngách, kênh, câu mở lời,
  tích hợp, đối thủ, giá, khác biệt.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Người dùng mới hoàn tất lần quét đầu và thấy kết quả mà không phải cấu hình gì.
- **SC-002**: 10/10 repo trong bảng kiểm thử license được phân loại đúng.
- **SC-003**: Một lần quét đủ 19 ngành (~500 repo) xong dưới 10 phút không token, dưới 6 phút có
  token (chưa tính AI).
- **SC-004**: Dashboard với 500 repo hiển thị trong dưới 2 giây.
- **SC-005**: Lần quét thứ hai với dữ liệu không đổi phát sinh 0 lần gọi AI.
- **SC-006**: Bấm Dừng → quét dừng trong ≤10 giây, dữ liệu cũ nguyên vẹn.
- **SC-007**: Đổi lịch sang 1 phút sau giờ hiện tại → quét tự chạy, không cần khởi động lại.
- **SC-008**: Không phản hồi API/log nào chứa bí mật đầy đủ.
- **SC-009**: Mọi màn hình dùng được ở chiều rộng 400px.

## Assumptions

- Một người dùng duy nhất; không cần tài khoản, chỉ mật khẩu chung khi chạy trên VPS.
- Lưu trữ bằng file JSON trong `data/` (đủ cho ~500 repo; REQUIREMENTS cho phép thay SQLite).
- "Sao tăng trong tuần" = sao hiện tại − sao ở ảnh chụp gần nhất cách ≥ 1 ngày (thường là lần quét
  tuần trước); nếu chưa có lịch sử thì để trống.
- "Mới tuần này" = repo không có trong ảnh chụp trước; lần quét đầu tiên không đánh dấu repo nào là mới.
- Ngoài phạm vi: nhiều người dùng, thanh toán, tự triển khai repo, nguồn ngoài GitHub, app mobile,
  sửa tri thức ngành trên giao diện.
- Giá, ngách, nhu cầu trong bộ tri thức là giả định cần kiểm chứng.
