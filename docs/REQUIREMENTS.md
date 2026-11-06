# OSS Radar — Yêu cầu phần mềm (v1.0)

> Tài liệu này dùng để giao cho Claude Code (hoặc lập trình viên) xây dựng app.
> Thư mục `reference/` đi kèm chứa code mẫu đã chạy được cho phần quét, phân loại license, bộ tri thức ngành và lớp AI. **Hãy đọc và tái sử dụng**, không viết lại từ đầu.

---

## 1. Mục tiêu

Xây một web app **tự host** (chạy trên máy cá nhân hoặc VPS). App tìm các repo mã nguồn mở trên GitHub có thể đóng gói thành dịch vụ bán cho doanh nghiệp nhỏ (SME) Việt Nam, rồi trả lời 5 câu hỏi cho từng repo:

1. **Có được phép bán dịch vụ không?** Phân loại license, và chọn mô hình kinh doanh an toàn.
2. **Repo làm được gì?** Tính năng chính và điểm mạnh nổi bật.
3. **Bán cho ai?** Khách hàng phù hợp và ngách nên đánh.
4. **Tiếp cận thế nào?** Kênh, câu mở lời, kế hoạch 12 tuần, giá gợi ý.
5. **Cần sửa gì cho thị trường Việt Nam?** Ví dụ Zalo OA, VietQR, hóa đơn điện tử.

Yêu cầu bắt buộc:
- Dùng được với **bất kỳ nhà cung cấp AI nào**, và app **vẫn chạy khi không có AI**.
- Có nút **Quét ngay** chạy thủ công.
- Có **lịch quét hằng tuần**, chỉnh được trên giao diện.

## 2. Người dùng

Một người dùng chính: chủ doanh nghiệp hoặc dev muốn tìm sản phẩm để kinh doanh. Không cần nhiều tài khoản, nhưng cần bảo vệ bằng mật khẩu khi chạy trên VPS.

## 3. Phạm vi

**Trong phạm vi v1:**
- Quét GitHub, phân loại license, chấm điểm.
- Tóm tắt bằng AI.
- Dashboard xem kết quả.
- Trang Cài đặt.
- Lịch quét, quét thủ công.
- Thông báo Telegram.
- Đóng gói Docker.

**Ngoài phạm vi v1:**
- Nhiều người dùng, phân quyền.
- Thanh toán.
- Tự động triển khai repo cho khách.
- Quét nguồn ngoài GitHub (GitLab, Gitee).
- App mobile.

---

## 4. Kiến trúc đề xuất

| Thành phần | Công nghệ |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Lịch chạy | APScheduler (BackgroundScheduler + CronTrigger, có múi giờ) |
| Lưu trữ | SQLite (khuyến nghị) hoặc file JSON trong thư mục `data/` mount ra ngoài container |
| Frontend | Một trang HTML + JS thuần (không cần build), gọi REST API của backend |
| HTTP | `requests` (hoặc `httpx`), không phụ thuộc SDK của hãng AI nào |
| Đóng gói | Dockerfile + docker-compose.yml; script chạy không Docker cho Windows (`run.bat`) và Mac/Linux (`run.sh`) |

Cấu trúc thư mục gợi ý:
```
oss-radar/
  app/
    main.py          # FastAPI: route API + phục vụ giao diện
    scanner.py       # quét GitHub (dùng lại reference/scanner.py)
    classify.py      # license + điểm + playbook (dùng lại reference/classify.py)
    knowledge.py     # tri thức thị trường VN theo ngành (dùng lại)
    curated.py       # tóm tắt tay cho 72 repo (dùng lại)
    ai.py            # lớp AI đa nhà cung cấp (dùng lại reference/ai.py)
    jobs.py          # chạy quét nền, tiến độ, hủy, lịch
    notify.py        # Telegram
    store.py         # đọc/ghi settings, kết quả, lịch sử, cache AI
    static/index.html
  data/              # mount volume: settings, kết quả, lịch sử, cache
  Dockerfile, docker-compose.yml, run.bat, run.sh, README.md
```

---

## 5. Yêu cầu chức năng

### 5.1 Quét GitHub (FR-SCAN)

- **FR-SCAN-1.** Tìm repo theo 19 ngành. Danh sách topic có sẵn trong `reference/scanner.py → CATEGORIES`. Mỗi topic chạy 2 truy vấn:
  - "top": `stars >= min_stars`, không archived, lấy 20 repo.
  - "mới nổi": tạo trong 18 tháng gần đây, `stars >= 300`, lấy 10 repo.
- **FR-SCAN-2.** Gộp trùng theo `full_name`. Một repo có thể thuộc nhiều ngành; giữ tag `top` hoặc `rising`.
- **FR-SCAN-3.** Đọc chi tiết từng repo qua `raw.githubusercontent.com` (không tốn quota API):
  - file LICENSE (thử lần lượt các tên phổ biến),
  - README,
  - sự tồn tại của file Docker/compose/Helm,
  - thư mục enterprise (`ee/`, `enterprise/`, `packages/ee/`...).
- **FR-SCAN-4.** GitHub token là **tùy chọn**. Không có token thì giãn cách tìm kiếm khoảng 6,5 giây (giới hạn 10 lần/phút); có token thì khoảng 2,2 giây (30 lần/phút). Gặp 403/429 thì chờ theo `X-RateLimit-Reset`. Gặp 401 thì báo "token không hợp lệ".
- **FR-SCAN-5.** Đọc chi tiết song song (khoảng 12 luồng). Báo tiến độ theo 3 giai đoạn: `search`, `detail`, `ai`, mỗi giai đoạn có `done/total` và thông điệp tiếng Việt.
- **FR-SCAN-6.** Cho phép **dừng** khi đang quét. Khi dừng, giữ nguyên kết quả của lần quét trước.
- **FR-SCAN-7.** Trích danh sách tính năng từ README: tìm mục Features/Highlights..., lọc bỏ dòng rác như cài đặt, phiên bản, link tài liệu. Code mẫu: `extract_features()`.
- **FR-SCAN-8.** Loại repo không phải ứng dụng (awesome list, tutorial, SDK, dataset...), trừ khi repo có docker-compose.

### 5.2 Phân loại license (FR-LIC) — quan trọng nhất

App phải đọc **nội dung file LICENSE**, không chỉ tin nhãn GitHub (GitHub hay trả về `NOASSERTION`). Logic mẫu nằm trong `reference/classify.py → classify_license()`.

| Nhóm | Điều kiện nhận diện | Mô hình kinh doanh hiển thị |
|---|---|---|
| `permissive` | MIT, Apache-2.0, BSD, ISC, MPL-2.0, LGPL, EPL... | **SaaS thoải mái**: được host nhiều khách, giữ riêng phần sửa |
| `gpl` | GPL-2.0/3.0 | **SaaS được**. Nếu cài lên server của khách thì phải giao kèm mã nguồn |
| `agpl` | AGPL-3.0, OSL-3.0 | **SaaS được, nhưng phải công khai phần sửa**. Gợi ý tách tích hợp VN thành service riêng |
| `single-tenant` | Có điều khoản cấm multi-tenant, hoặc cấm gỡ logo/thương hiệu (ví dụ Dify, Open WebUI) | **Chỉ triển khai riêng từng khách**, giữ logo |
| `restricted` | BSL, SSPL, Elastic, Sustainable Use (n8n), Commons Clause, FSL, PolyForm, cấm thương mại | **Loại**: không host bán lại |
| `none` | Không có license | **Loại** |
| `unknown` | Không nhận diện được | **Cần đọc tay** |

Yêu cầu thêm:
- **FR-LIC-1.** Khi nhãn GitHub là `NOASSERTION`, nhận diện license chuẩn qua chữ ký văn bản (ví dụ "GNU Affero General Public License", "Permission is hereby granted"...). Nhãn hiển thị thêm "(đọc từ file)".
- **FR-LIC-2.** Phát hiện **open-core**: nếu repo có thư mục enterprise, ghi chú "chỉ dùng phần lõi" và trừ 4 điểm license.
- **FR-LIC-3.** Mỗi repo có link trực tiếp tới file license để người dùng tự đọc.
- **FR-LIC-4.** Không bắt từ "non-commercial" chung chung, vì dễ gây báo nhầm. Chỉ bắt các cụm cấm rõ ràng.

**Bộ kiểm thử bắt buộc** (test tự động với file license mẫu hoặc dữ liệu thật). Kết quả mong đợi:

| Repo | Nhóm mong đợi |
|---|---|
| n8n-io/n8n | restricted |
| nocodb/nocodb | restricted |
| akaunting/akaunting | restricted |
| invoiceninja/invoiceninja | restricted |
| langgenius/dify | single-tenant |
| chatwoot/chatwoot | permissive, kèm enterprise |
| twentyhq/twenty | agpl |
| odoo/odoo | permissive (LGPL) |
| frappe/erpnext | gpl |
| documenso/documenso | agpl, kèm enterprise |

### 5.3 Chấm điểm (FR-SCORE)

Điểm tổng 0–100, gồm 5 phần (công thức mẫu: `score()`):

| Thành phần | Tối đa | Cách tính |
|---|---|---|
| License an toàn | 30 | permissive 30, LGPL/MPL 28, GPL 24, AGPL 20, single-tenant 12, unknown 5, loại 0; trừ 4 nếu open-core |
| Hoạt động | 15 | Theo số ngày từ commit cuối (≤14 ngày: 15, ≤30: 12, ≤90: 8, ≤180: 4) |
| Sức hút | 15 | Log số sao + tốc độ sao/ngày; nếu có lịch sử thì dùng **số sao tăng trong tuần** |
| Dễ tự host | 15 | Có compose/Docker/Helm, ngôn ngữ phổ biến |
| Phù hợp VN | 25 | Nhu cầu và cạnh tranh của ngành (`knowledge.py`) + từ khóa hướng doanh nghiệp − từ khóa công cụ dev |

- Repo nhóm `restricted` hoặc `none` có điểm tối đa 25, và mặc định bị ẩn.

### 5.4 Tri thức thị trường và playbook (FR-KB)

- **FR-KB-1.** Dùng lại `knowledge.py`. Mỗi ngành có:
  - mức nhu cầu và mức cạnh tranh (thang 1–5),
  - rủi ro dữ liệu, khách hàng mục tiêu, ngách nên đánh,
  - kênh tiếp cận, câu mở lời, tích hợp VN cần làm,
  - đối thủ nội địa, giá gợi ý, cách khác biệt.
- **FR-KB-2.** Sinh kế hoạch 12 tuần, danh sách cải tiến cho VN và danh sách rủi ro cho từng repo (code mẫu có sẵn).
- **FR-KB-3.** Bộ tri thức để ở file riêng, dễ sửa tay. Mở rộng thêm (không bắt buộc v1): cho phép sửa trên giao diện.

### 5.5 AI đa nhà cung cấp (FR-AI)

- **FR-AI-1.** Hỗ trợ 2 loại API, gọi bằng HTTP thuần:
  - **Tương thích OpenAI** (`POST {base_url}/chat/completions`). Loại này phủ OpenAI, Google Gemini (endpoint OpenAI-compatible), DeepSeek, Groq, OpenRouter, Mistral, Together, Ollama, LM Studio, vLLM.
  - **Anthropic** (`POST {base_url}/v1/messages`, header `x-api-key`, `anthropic-version`).
- **FR-AI-2.** Có danh sách preset để chọn nhanh (đã có trong `reference/ai.py → PRESETS`) và mục "Khác". Người dùng sửa được base URL và tên model.
- **FR-AI-3.** Chế độ **"Không dùng AI"** là mặc định. Khi đó app vẫn hiển thị:
  - tính năng trích từ README (nhãn "chưa dịch"),
  - tóm tắt tay của 72 repo trong `curated.py`,
  - điểm mạnh tự suy từ dữ liệu.
- **FR-AI-4.** Khi bật AI, với mỗi repo **an toàn license** chưa có tóm tắt tay, gửi mô tả, tính năng trích được và README rút gọn (khoảng 5.000 ký tự, bỏ khối code và ảnh). Nhận về JSON:
  ```json
  {"features":["4–6 ý"],"strengths":["2–3 ý"],"niche_hint":"1 câu","vn_improvements":["1–3 ý"]}
  ```
  Prompt mẫu có sẵn trong `ai.py`. Yêu cầu AI chỉ dựa trên dữ liệu được đưa, không bịa.
- **FR-AI-5.** Giới hạn số repo gọi AI mỗi lần quét (mặc định 60, chỉnh trong Cài đặt), ưu tiên điểm cao. Chạy song song 3 luồng (chỉnh được).
- **FR-AI-6.** **Cache** kết quả theo `tên repo + hash(README + mô tả)`. Lần quét sau chỉ gọi AI cho repo mới hoặc README đã thay đổi. Có nút "Xóa cache AI".
- **FR-AI-7.** Xử lý lỗi:
  - Parse JSON chịu được markdown fence.
  - Lỗi từng repo không làm hỏng cả lần quét.
  - Nếu 3 repo đầu đều lỗi xác thực (401/403) thì dừng bước AI, giữ kết quả quét, và báo lỗi rõ ràng (ví dụ "API key sai", "sai tên model", "hết tiền/giới hạn").
- **FR-AI-8.** Có nút **"Kiểm tra kết nối AI"**: gọi thử một câu ngắn, hiển thị thành công hoặc lỗi kèm gợi ý sửa.
- **FR-AI-9.** Trong hồ sơ repo, ghi rõ nguồn tóm tắt: "Tóm tắt tay", "AI: <tên model>" hoặc "Trích README, chưa dịch".

### 5.6 Chạy thủ công và lịch quét (FR-JOB)

- **FR-JOB-1.** Nút **Quét ngay** ở thanh trên cùng. Mỗi thời điểm chỉ chạy một lần quét; bấm khi đang chạy thì hiện tiến độ thay vì chạy thêm.
- **FR-JOB-2.** Thanh tiến độ cập nhật mỗi khoảng 2 giây (polling `/api/status` hoặc SSE), hiển thị giai đoạn, `done/total`, thời gian đã chạy và nút **Dừng**.
- **FR-JOB-3.** Lịch quét hằng tuần, cấu hình trên giao diện:
  - bật/tắt,
  - ngày trong tuần (T2–CN),
  - giờ:phút,
  - múi giờ (mặc định `Asia/Ho_Chi_Minh`).
  Lưu xong thì áp dụng ngay, không cần khởi động lại.
- **FR-JOB-4.** Giao diện hiển thị **lần chạy tới** và **lần chạy gần nhất** (thời điểm, thành công/lỗi, số repo, số repo được AI tóm tắt, thời lượng).
- **FR-JOB-5.** Lịch sử: sau mỗi lần quét, lưu ảnh chụp `{repo: số sao}` theo ngày. Dùng ảnh chụp gần nhất để tính số sao tăng trong tuần, và đánh dấu repo **mới xuất hiện** so với lần trước.
- **FR-JOB-6.** Nếu máy tắt đúng giờ hẹn, khi bật lại sẽ chạy bù (`misfire_grace_time` khoảng 6 giờ, `coalesce=True`).

### 5.7 Thông báo (FR-NOTI)

- **FR-NOTI-1.** Telegram tùy chọn: nhập bot token và chat ID trong Cài đặt, có nút "Gửi thử".
- **FR-NOTI-2.** Sau mỗi lần quét, gửi tin nhắn tóm tắt gồm:
  - tổng số repo và số repo theo nhóm license,
  - tối đa 5 repo **mới** hoặc **tăng sao mạnh nhất tuần** thuộc nhóm an toàn và đạt ngưỡng điểm (mặc định 75),
  - link mở app (lấy từ biến `APP_URL` nếu có).
- **FR-NOTI-3.** Quét lỗi thì gửi thông báo lỗi.

### 5.8 Giao diện (FR-UI)

Giao diện tiếng Việt, chạy tốt trên điện thoại, có chế độ sáng/tối. Tham khảo bản dashboard mẫu `reference/radar_mockup.html`; giữ bố cục và nội dung hồ sơ repo.

**Thanh trên cùng:**
- tên app,
- thời điểm quét gần nhất,
- nút Quét ngay và tiến độ,
- tab: Theo repo / Theo ngành / Cài đặt.

**Tab Theo repo:**
- Thanh phân bố license.
- Bộ lọc: tìm kiếm (tên, mô tả, **tính năng**), ngành, sắp xếp (điểm, phù hợp VN, số sao, sao tăng trong tuần), ẩn repo bị loại, chỉ SaaS thoải mái, mới nổi, **mới tuần này**, có tóm tắt tiếng Việt.
- Danh sách repo (điểm, tên, ngành, sao, 2 tính năng đầu, nhãn license) và hồ sơ chi tiết bên phải. Hồ sơ gồm, theo thứ tự:
  1. Thông tin nhanh: sao, sao tăng trong tuần, commit cuối, ngôn ngữ, Docker, tiếng Việt
  2. **Mô hình kinh doanh an toàn**, kèm link license
  3. **Tính năng chính** (ghi nguồn tóm tắt)
  4. **Điểm mạnh nổi bật** (của AI hoặc tóm tắt tay, cộng điểm mạnh tự suy)
  5. Điểm và 5 thành phần điểm
  6. Ngách nên đánh, có thêm gợi ý ngách riêng của AI nếu có
  7. Khách hàng phù hợp, kênh tiếp cận, câu mở lời
  8. Kế hoạch 12 tuần
  9. Cải tiến cho VN
  10. Đối thủ, cách khác biệt, giá gợi ý, rủi ro dữ liệu
  11. Rủi ro cần lưu ý

**Tab Theo ngành:** mỗi ngành một thẻ, gồm nhu cầu/cạnh tranh, ngách, khách hàng và 4 repo an toàn tốt nhất. Bấm vào repo thì nhảy sang hồ sơ của repo đó.

**Tab Cài đặt** (nút "Lưu" và thông báo "Đã lưu"):

| Nhóm | Trường |
|---|---|
| AI | Nhà cung cấp (preset), Base URL, Model, API key (ô ẩn ký tự; chỉ hiển thị 4 ký tự cuối khi đã lưu; có nút xóa key), Số repo tối đa gọi AI mỗi lần, Số luồng, nút Kiểm tra kết nối, nút Xóa cache AI |
| Lịch quét | Bật/tắt, Ngày trong tuần, Giờ, Phút, Múi giờ; hiển thị lần chạy tới |
| GitHub | Token (tùy chọn, ẩn ký tự), Số sao tối thiểu (mặc định 800), Chọn ngành cần quét (mặc định tất cả) |
| Thông báo | Telegram bot token, Chat ID, Ngưỡng điểm, nút Gửi thử |

Trạng thái rỗng: lần đầu mở app khi chưa có dữ liệu, hiển thị hướng dẫn và nút Quét ngay. Có thể nạp sẵn file dữ liệu mẫu `reference/sample_data.json` để xem thử.

### 5.9 API (gợi ý)

| Method | Đường dẫn | Mô tả |
|---|---|---|
| GET | `/` | Giao diện |
| GET | `/api/data` | Kết quả quét gần nhất (repo + tri thức ngành) |
| GET / POST | `/api/settings` | Đọc/ghi cài đặt. Không bao giờ trả key đầy đủ. Trường key không gửi lên nghĩa là giữ nguyên |
| POST | `/api/scan` | Bắt đầu quét |
| POST | `/api/scan/stop` | Dừng quét |
| GET | `/api/status` | Tiến độ, lần chạy gần nhất, lần chạy tới |
| POST | `/api/ai/test` | Kiểm tra kết nối AI (dùng cấu hình gửi kèm hoặc cấu hình đã lưu) |
| POST | `/api/ai/clear-cache` | Xóa cache AI |
| POST | `/api/notify/test` | Gửi thử Telegram |

---

## 6. Yêu cầu phi chức năng

- **NFR-1 Bảo mật.**
  - Key AI, token GitHub và token Telegram chỉ lưu ở `data/` trên máy người dùng. Không ghi ra log, không trả về giao diện.
  - Có biến môi trường `APP_PASSWORD`: nếu đặt thì bật HTTP Basic Auth cho toàn bộ app.
  - Mặc định chỉ lắng nghe `127.0.0.1`. Muốn mở cho máy khác phải đặt `HOST=0.0.0.0`, và README phải cảnh báo đặt mật khẩu.
- **NFR-2 Hiệu năng.**
  - Một lần quét đủ 19 ngành (khoảng 500 repo): dưới 10 phút khi không có token, dưới 6 phút khi có token, chưa tính bước AI.
  - Dashboard tải dưới 2 giây với 500 repo.
- **NFR-3 Bền bỉ.**
  - Ghi file kết quả theo kiểu ghi file tạm rồi đổi tên, để tránh hỏng dữ liệu khi tắt ngang.
  - Lỗi mạng ở một repo không làm hỏng cả lần quét.
- **NFR-4 Chi phí AI.** Hiển thị ước tính số lần gọi AI trước khi quét: số repo cần tóm tắt trừ đi số đã có trong cache.
- **NFR-5 Ngôn ngữ.** Toàn bộ giao diện và thông báo lỗi bằng tiếng Việt, dễ hiểu với người không chuyên.
- **NFR-6 Pháp lý.** Giao diện luôn hiển thị lưu ý: "Phân loại license là tự động, đọc license trước khi ký hợp đồng. Giá và ngách là giả định cần kiểm chứng."

## 7. Triển khai

- `docker compose up -d`: app chạy ở `http://localhost:8080`, dữ liệu nằm trong `./data`.
- Không Docker: chạy `run.sh` hoặc `run.bat`. Script tạo virtualenv, cài `requirements.txt`, rồi chạy Uvicorn.
- Dùng Ollama chạy trong Docker: README hướng dẫn base URL `http://host.docker.internal:11434/v1`, và thêm `extra_hosts` trong compose cho Linux.
- README tiếng Việt gồm: cài đặt, lấy API key từng hãng (link trang tạo key), lấy GitHub token (quyền chỉ đọc public), tạo bot Telegram, đổi lịch quét, sao lưu thư mục `data/`.

## 8. Tiêu chí nghiệm thu

1. Lần đầu chạy, khi chưa cấu hình gì, bấm **Quét ngay** thì quét xong và dashboard hiển thị kết quả, **không cần AI và không cần token**.
2. 10 repo trong bảng kiểm thử ở mục 5.2 được phân loại đúng.
3. Chọn preset Gemini hoặc OpenAI hoặc Ollama, nhập key/model, bấm **Kiểm tra kết nối** thì báo thành công. Nhập key sai thì báo lỗi rõ ràng bằng tiếng Việt.
4. Bật AI rồi quét: các repo an toàn chưa có tóm tắt tay sẽ có tính năng và điểm mạnh tiếng Việt, ghi nguồn "AI: <model>". Quét lần hai không gọi lại AI cho repo không đổi (kiểm tra qua log hoặc số lần gọi).
5. Đặt lịch "mỗi thứ Hai 07:00": giao diện hiện đúng lần chạy tới. Đổi sang 1 phút sau giờ hiện tại thì job tự chạy mà không cần khởi động lại app.
6. Bấm **Dừng** khi đang quét: quét dừng trong khoảng 10 giây và dữ liệu cũ còn nguyên.
7. Có Telegram: sau khi quét, nhận được tin nhắn tóm tắt. Từ lần quét thứ hai trở đi, tin nhắn có repo mới hoặc tăng sao.
8. Đặt `APP_PASSWORD`: mở app bị hỏi mật khẩu. API key không xuất hiện trong bất kỳ phản hồi API hay log nào.
9. Giao diện dùng tốt ở chiều rộng 400px.
10. Có test tự động cho: phân loại license, parse JSON trả về từ AI, và tính lịch chạy tới.

## 9. Lộ trình gợi ý

| Bước | Nội dung | Kết quả |
|---|---|---|
| 1 | Dựng khung FastAPI, `store.py`, chuyển code `reference/` vào `app/`, chạy quét bằng lệnh | Có file kết quả |
| 2 | Job nền: quét, tiến độ, dừng, lịch sử sao | API `/api/scan`, `/api/status` |
| 3 | Giao diện dashboard dựa trên `radar_mockup.html`, đọc từ API | Xem được kết quả |
| 4 | Tab Cài đặt + lịch APScheduler | Đổi lịch trên giao diện |
| 5 | Lớp AI + cache + kiểm tra kết nối | Tóm tắt tiếng Việt bằng AI |
| 6 | Telegram, Basic Auth, Docker, README, test | Đạt tiêu chí nghiệm thu |

## 10. Tài liệu tham khảo đi kèm (`reference/`)

| File | Nội dung |
|---|---|
| `scanner.py` | Quét GitHub search + raw, trích tính năng từ README |
| `classify.py` | Phân loại license, chấm điểm, cải tiến, rủi ro, playbook, `classify_all()` |
| `knowledge.py` | Tri thức thị trường VN cho 19 ngành |
| `curated.py` | Tóm tắt tay tính năng và điểm mạnh cho 72 repo |
| `ai.py` | Preset nhà cung cấp, client OpenAI-compatible + Anthropic, prompt, parse JSON, khóa cache |
| `radar_mockup.html` | Dashboard mẫu (dữ liệu nhúng sẵn): tham khảo bố cục và nội dung |
| `sample_data.json` | Kết quả một lần quét thật (474 repo, ngày 06/11/2026) để dev thử giao diện |

Lưu ý khi dùng lại code mẫu:
- `scanner.py` và `ai.py` là bản viết mới, **chưa chạy thử end-to-end**. Cần test lại.
- Phần quét qua raw và logic phân loại đã chạy thật trên 513 repo.
