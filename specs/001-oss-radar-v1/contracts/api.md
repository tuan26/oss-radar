# REST API Contract

Mọi route (kể cả `/`) yêu cầu HTTP Basic Auth nếu đặt `APP_PASSWORD` (username tùy ý).
Lỗi trả `{"detail": "<thông điệp tiếng Việt>"}` với mã 4xx/5xx.

| Method | Path | Request | Response 200 |
|---|---|---|---|
| GET | `/` | | HTML |
| GET | `/api/data` | | ScanResult (xem data-model) hoặc `{"repos": [], "scanned_at": null, ...}` |
| GET | `/api/settings` | | Settings đã che + `presets`, `categories` |
| POST | `/api/settings` | Settings một phần (xem dưới) | Settings đã che + `next_run` |
| POST | `/api/scan` | | `{"started": bool, "status": Status}` (`started=false` nếu đang quét) |
| POST | `/api/scan/stop` | | `{"stopping": bool}` |
| GET | `/api/status` | | Status |
| POST | `/api/ai/test` | `{provider?, kind?, base_url?, model?, api_key?}` | `{"ok": true, "reply": str}` hoặc `{"ok": false, "error": str}` |
| POST | `/api/ai/clear-cache` | | `{"cleared": int}` |
| POST | `/api/notify/test` | `{bot_token?, chat_id?}` | `{"ok": bool, "error"?: str}` |
| POST | `/api/sample` | | `{"loaded": int}` — nạp dữ liệu mẫu (chỉ khi chưa có kết quả, hoặc `?force=1`) |

## Settings đã che (GET)

Bí mật thay bằng: `api_key_set: bool, api_key_last4: "abcd"`, tương tự `token_set/token_last4`,
`bot_token_set/bot_token_last4`. Không có trường bí mật đầy đủ.

## POST /api/settings

- Trường bí mật **không gửi hoặc rỗng** → giữ nguyên.
- `clear_api_key`, `clear_token`, `clear_bot_token: true` → xóa.
- Giá trị sai (múi giờ, giờ…) → 400 với thông điệp tiếng Việt, không lưu gì.
- Lịch được áp dụng ngay; phản hồi có `next_run`.

## Status

```json
{"running": true, "stopping": false, "phase": "search|detail|ai|save", "done": 12, "total": 76,
 "message": "Tìm repo: crm", "elapsed_s": 41.2,
 "last_run": RunRecord | null, "next_run": "ISO-8601 có múi giờ" | null,
 "scanned_at": "...", "ai_estimate": {"enabled": bool, "candidates": int, "cached": int, "calls": int}}
```
