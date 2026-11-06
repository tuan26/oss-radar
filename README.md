# OSS Radar

Tìm repo mã nguồn mở trên GitHub có thể **đóng gói thành dịch vụ bán cho doanh nghiệp nhỏ (SME)
Việt Nam**, và trả lời 5 câu hỏi cho từng repo:

1. **Có được phép bán dịch vụ không?** — đọc nội dung file LICENSE, xếp vào 7 nhóm, chọn mô hình kinh doanh an toàn.
2. **Repo làm được gì?** — tính năng chính và điểm mạnh nổi bật.
3. **Bán cho ai?** — khách hàng phù hợp, ngách nên đánh.
4. **Tiếp cận thế nào?** — kênh, câu mở lời, kế hoạch 12 tuần, giá gợi ý.
5. **Cần sửa gì cho thị trường Việt Nam?** — Zalo OA, VietQR, hóa đơn điện tử…

App **chạy được khi không có AI và không có GitHub token**. AI (bất kỳ hãng nào) chỉ dùng để tóm
tắt tiếng Việt cho đẹp hơn.

> ⚖️ Phân loại license là tự động, đọc license trước khi ký hợp đồng. Giá và ngách là giả định cần kiểm chứng.

---

## 1. Cài đặt và chạy

### Cách A — Docker (khuyên dùng)

```bash
docker compose up -d
```

Mở <http://localhost:8080>. Dữ liệu nằm trong thư mục `./data`.

### Cách B — Không cần Docker

Cần Python 3.11 trở lên.

- **macOS / Linux**: `./run.sh`
- **Windows**: bấm đúp `run.bat`

Script tự tạo môi trường ảo `.venv`, cài thư viện trong `requirements.txt`, rồi chạy app ở
<http://localhost:8080>. Dừng bằng `Ctrl+C`.

### Lần đầu sử dụng

Bấm **Quét ngay**. Không cần cấu hình gì. Lần quét đủ 19 ngành mất khoảng 10 phút khi không có
GitHub token (khoảng 4 phút khi có token). Muốn xem trước giao diện, bấm **Xem dữ liệu mẫu**.

## 2. Chạy trên VPS — đặt mật khẩu!

Mặc định app **chỉ nghe ở 127.0.0.1** (chỉ máy đang chạy mở được). Để máy khác truy cập:

| Cách chạy | Làm gì |
|---|---|
| Docker | Trong `docker-compose.yml` đổi `"127.0.0.1:8080:8080"` thành `"8080:8080"` |
| run.sh / run.bat | Đặt biến `HOST=0.0.0.0` |

> ⚠️ **Khi mở ra ngoài, BẮT BUỘC đặt mật khẩu.** Nếu không, ai biết địa chỉ cũng xem được và sửa
> được cài đặt (dùng API key của bạn).

Đặt mật khẩu bằng biến `APP_PASSWORD`: trình duyệt sẽ hỏi tên đăng nhập (gõ gì cũng được) và mật khẩu.

```bash
# Docker: tạo file .env cạnh docker-compose.yml
echo "APP_PASSWORD=mat-khau-dai-kho-doan" >> .env
echo "APP_URL=https://radar.ten-mien-cua-ban.vn" >> .env
docker compose up -d
```

```bash
# Không Docker
HOST=0.0.0.0 APP_PASSWORD=mat-khau-dai-kho-doan ./run.sh
```

Nên đặt app sau reverse proxy có HTTPS (Caddy, Nginx) để mật khẩu không đi qua mạng dạng rõ.

| Biến môi trường | Mặc định | Ý nghĩa |
|---|---|---|
| `APP_PASSWORD` | (trống) | Bật đăng nhập cho toàn bộ app |
| `HOST` | `127.0.0.1` | Địa chỉ lắng nghe (`0.0.0.0` = mọi máy) |
| `PORT` | `8080` | Cổng |
| `APP_URL` | (trống) | Link mở app, gắn vào tin nhắn Telegram |
| `DATA_DIR` | `./data` | Thư mục lưu dữ liệu |

## 3. Cấu hình AI (không bắt buộc)

Vào **Cài đặt → AI**, chọn nhà cung cấp, dán API key, bấm **Kiểm tra kết nối**, rồi **Lưu**.

| Nhà cung cấp | Lấy key ở đâu | Ghi chú |
|---|---|---|
| Google Gemini | <https://aistudio.google.com/apikey> | Có gói miễn phí |
| OpenAI | <https://platform.openai.com/api-keys> | |
| DeepSeek | <https://platform.deepseek.com/api_keys> | Rẻ |
| OpenRouter | <https://openrouter.ai/keys> | Một key dùng nhiều model |
| Groq | <https://console.groq.com/keys> | Nhanh, có gói miễn phí |
| Anthropic Claude | <https://console.anthropic.com/settings/keys> | |
| Ollama / LM Studio | Không cần key | Chạy AI ngay trên máy bạn |
| Khác | — | Bất kỳ API nào tương thích OpenAI (Mistral, Together, vLLM…): nhập Base URL + model |

- Mỗi lần quét chỉ gọi AI cho tối đa **60 repo** (chỉnh được), ưu tiên repo điểm cao, chỉ repo an
  toàn license và chưa có tóm tắt tay.
- Kết quả được **lưu cache**: lần quét sau chỉ gọi AI cho repo mới hoặc repo đổi README. Giao diện
  hiện ước tính số lần gọi AI trước khi quét. Nút **Xóa cache AI** để làm lại từ đầu.
- Nếu 3 repo đầu đều báo lỗi xác thực (key sai), app dừng bước AI nhưng vẫn giữ kết quả quét.

### Dùng Ollama khi app chạy trong Docker

Ollama chạy trên máy host, nên trong container phải dùng địa chỉ đặc biệt:

```text
Base URL: http://host.docker.internal:11434/v1
Model:    qwen2.5:7b   (hoặc model bạn đã ollama pull)
```

`docker-compose.yml` đã có sẵn `extra_hosts: host.docker.internal:host-gateway` để địa chỉ này chạy
trên Linux. Trên Linux, có thể cần cho Ollama nghe mọi địa chỉ: `OLLAMA_HOST=0.0.0.0 ollama serve`.

## 4. GitHub token (không bắt buộc, giúp quét nhanh gấp ~3 lần)

1. Mở <https://github.com/settings/personal-access-tokens/new> (Fine-grained token).
2. Đặt tên, chọn hạn dùng. Ở **Repository access** chọn **Public repositories (read-only)**.
   Không cần cấp thêm quyền nào.
3. Bấm **Generate token**, sao chép (`github_pat_…`), dán vào **Cài đặt → GitHub → Token**, rồi **Lưu**.

Không có token: app giãn cách 6,5 giây giữa các lần tìm kiếm (giới hạn 10 lần/phút của GitHub).
Có token: 2,2 giây (30 lần/phút). Token sai → app báo "GitHub token không hợp lệ".

## 5. Thông báo Telegram

1. Mở Telegram, nhắn [@BotFather](https://t.me/BotFather) → `/newbot` → đặt tên → nhận **bot token**.
2. Nhắn bất kỳ tin nào cho bot vừa tạo (bấm **Start**).
3. Lấy **chat ID**: mở `https://api.telegram.org/bot<TOKEN>/getUpdates` trong trình duyệt, tìm
   `"chat":{"id": 123456789`. Muốn gửi vào nhóm: thêm bot vào nhóm, nhắn một tin trong nhóm, chat ID
   của nhóm là số âm (vd `-100…`).
4. Dán vào **Cài đặt → Thông báo**, bấm **Gửi thử**, rồi **Lưu**.

Sau mỗi lần quét bạn nhận: tổng số repo, số repo theo nhóm license, tối đa 5 repo an toàn đạt ngưỡng
điểm (mặc định 75) là **mới xuất hiện** hoặc **tăng sao mạnh nhất tuần**, và link mở app (`APP_URL`).
Quét lỗi cũng được báo.

## 6. Lịch quét hằng tuần

**Cài đặt → Lịch quét**: bật, chọn thứ, giờ, phút, múi giờ (mặc định `Asia/Ho_Chi_Minh`), bấm
**Lưu**. Lịch áp dụng ngay, không cần khởi động lại. Thanh trên cùng hiện **lần chạy tới** và
**lần chạy gần nhất**.

Nếu máy tắt đúng giờ hẹn, khi bật lại trong vòng 6 giờ app sẽ tự chạy bù một lần.

Mỗi lần quét lưu ảnh chụp số sao của từng repo (`data/history/`). Từ lần quét thứ hai, app tính
**số sao tăng trong tuần** và đánh dấu repo **mới tuần này**.

## 7. Dữ liệu và sao lưu

Mọi thứ nằm trong thư mục `data/`:

| File | Nội dung |
|---|---|
| `settings.json` | Cài đặt, **kể cả API key và token** — giữ kín file này |
| `results.json` | Kết quả lần quét gần nhất |
| `runs.json` | 50 lần chạy gần nhất |
| `ai_cache.json` | Tóm tắt AI đã trả tiền — giữ lại để không phải gọi lại |
| `history/` | Ảnh chụp số sao theo ngày |

Sao lưu: chép nguyên thư mục `data/` (vd `tar czf radar-backup.tgz data/`). Khôi phục: chép lại vào
chỗ cũ rồi khởi động app. Mọi file được ghi kiểu "ghi file tạm rồi đổi tên" nên không hỏng khi tắt ngang.

API key và token chỉ nằm trong `data/settings.json` trên máy bạn: không ghi ra log, không bao giờ trả
về giao diện (chỉ hiện 4 ký tự cuối).

## 8. Tùy biến tri thức ngành

- `app/knowledge.py` — nhu cầu, cạnh tranh, khách hàng, ngách, kênh, câu mở lời, đối thủ, giá… của 19 ngành.
- `app/curated.py` — tóm tắt tay tính năng/điểm mạnh cho 72 repo.
- `app/scanner.py → CATEGORIES` — các topic GitHub dùng để tìm repo cho từng ngành.

Sửa file rồi khởi động lại app (Docker: `docker compose up -d --build`).

## 9. Cách phân loại license

| Nhóm | Nhận diện | Mô hình kinh doanh |
|---|---|---|
| SaaS thoải mái | MIT, Apache-2.0, BSD, ISC, MPL-2.0, LGPL, EPL… | Host nhiều khách, giữ riêng phần sửa |
| GPL | GPL-2.0/3.0 | SaaS được; cài lên server khách thì giao kèm mã nguồn |
| AGPL | AGPL-3.0, OSL-3.0 | SaaS được, phải công khai phần sửa |
| Riêng từng khách | Cấm multi-tenant / cấm gỡ logo (vd Dify) | Mỗi khách một instance, giữ logo |
| Loại | BSL, SSPL, Elastic, Sustainable Use, Commons Clause, FSL, PolyForm, cấm thương mại | Không host bán lại |
| Không license | — | Loại |
| Cần đọc tay | License tùy biến | Đọc file license |

Repo có thư mục enterprise (`ee/`, `enterprise/`…) được ghi chú "chỉ dùng phần lõi" và trừ 4 điểm.

## 10. Phát triển

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

Test chạy offline (GitHub, AI, Telegram đều được giả lập), gồm bộ 10 repo license bắt buộc với file
LICENSE thật trong `tests/fixtures/licenses.json`.

Tài liệu thiết kế theo quy trình Spec Kit nằm trong `specs/001-oss-radar-v1/`
(spec → plan → research → data model → API contract → tasks), nguyên tắc dự án ở
`.specify/memory/constitution.md`, yêu cầu gốc ở `docs/REQUIREMENTS.md`.
