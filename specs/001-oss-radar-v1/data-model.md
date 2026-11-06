# Data Model: OSS Radar v1

Tất cả nằm trong `DATA_DIR` (mặc định `./data`).

## settings.json — Settings

```json
{
  "ai": {"provider": "none", "kind": "openai", "base_url": "", "model": "", "api_key": "",
         "max_repos": 60, "workers": 3},
  "schedule": {"enabled": false, "day_of_week": "mon", "hour": 7, "minute": 0,
               "timezone": "Asia/Ho_Chi_Minh"},
  "github": {"token": "", "min_stars": 800, "categories": []},
  "telegram": {"bot_token": "", "chat_id": "", "min_score": 75}
}
```

Ràng buộc: `provider ∈ PRESETS ∪ {"none"}`; `kind ∈ {openai, anthropic}`; `max_repos` 0–500;
`workers` 1–8; `day_of_week ∈ mon..sun`; `hour` 0–23; `minute` 0–59; `timezone` là IANA hợp lệ;
`min_stars` ≥ 0; `categories ⊆ CATEGORIES` (rỗng = tất cả); `min_score` 0–100.
Bí mật: `ai.api_key`, `github.token`, `telegram.bot_token` — không bao giờ rời server.

## results.json — ScanResult

```json
{"scanned_at": "ISO-8601 UTC", "repos": [Repo], "summary": {"permissive": 0, "...": 0},
 "kb": {"<category>": CategoryKnowledge + {"playbook": [str]}},
 "has_history": true}
```

### Repo (theo `classify_all()` + bổ sung)

| Trường | Kiểu | Ghi chú |
|---|---|---|
| name, url, description, homepage | str | |
| stars, forks | int | |
| language | str? | |
| topics | [str] | ≤ 8 |
| created, pushed | YYYY-MM-DD | |
| rising | bool | tag "mới nổi" |
| is_new | bool | **mới** — không có trong ảnh chụp trước |
| category, category_label | str | |
| license, license_group, license_flags, license_url | | group ∈ permissive/gpl/agpl/single-tenant/restricted/none/unknown |
| deploy_model, deploy_detail, enterprise_dirs | | |
| score | {total, license, activity, traction, selfhost, vnfit} | |
| tech | {compose, docker, helm, vi, push_days, stars_per_day, weekly_delta} | |
| improvements, risks | [str] | |
| features, strengths | [str] | |
| feat_src | curated / ai / readme / none | |
| ai_model | str | khi feat_src = ai |
| niche_hint | str | gợi ý ngách của AI |
| auto_strengths | [str] | |
| ai_key | str | khóa cache AI, dùng ước tính chi phí |

## runs.json — RunRecord[] (≤ 50 bản ghi mới nhất)

`{"started_at", "finished_at", "status": "ok|error|stopped", "trigger": "manual|schedule|catchup",
"error": str, "repos": int, "ai_summarized": int, "ai_calls": int, "duration_s": float}`

## history/YYYY-MM-DD.json — StarSnapshot

`{"owner/repo" (lowercase): stars}`

## ai_cache.json — AICacheEntry

`{"<repo lowercase>:<sha1-12>": {"features", "strengths", "niche_hint", "vn_improvements", "model", "at"}}`

## Trạng thái quét (bộ nhớ)

`idle → running(search → detail → ai) → idle`; `running → stopping → idle` khi bấm Dừng.
Kết quả chỉ ghi vào `results.json` khi xong toàn bộ; dừng/lỗi giữ nguyên file cũ.
