# -*- coding: utf-8 -*-
"""Lớp AI dùng được với mọi nhà cung cấp (dùng lại từ reference/ai.py).

- "openai": mọi API tương thích OpenAI Chat Completions — OpenAI, Google Gemini,
  DeepSeek, Groq, OpenRouter, Mistral, Together, Ollama, LM Studio, vLLM...
- "anthropic": Claude (API Messages riêng của Anthropic)
- "none": không dùng AI; app vẫn chạy, chỉ hiển thị tính năng trích từ README
"""
import json, re, hashlib, threading, datetime as dt
from concurrent.futures import ThreadPoolExecutor
import requests

PRESETS = {
    "openai":     {"label": "OpenAI",            "kind": "openai",    "base_url": "https://api.openai.com/v1",                                  "model": "gpt-4o-mini"},
    "gemini":     {"label": "Google Gemini",     "kind": "openai",    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",   "model": "gemini-2.5-flash"},
    "deepseek":   {"label": "DeepSeek",          "kind": "openai",    "base_url": "https://api.deepseek.com/v1",                               "model": "deepseek-chat"},
    "openrouter": {"label": "OpenRouter",        "kind": "openai",    "base_url": "https://openrouter.ai/api/v1",                              "model": "openai/gpt-4o-mini"},
    "groq":       {"label": "Groq",              "kind": "openai",    "base_url": "https://api.groq.com/openai/v1",                            "model": "llama-3.3-70b-versatile"},
    "ollama":     {"label": "Ollama (máy bạn)",  "kind": "openai",    "base_url": "http://localhost:11434/v1",                                 "model": "qwen2.5:7b"},
    "lmstudio":   {"label": "LM Studio (máy bạn)", "kind": "openai",  "base_url": "http://localhost:1234/v1",                                  "model": "local-model"},
    "anthropic":  {"label": "Anthropic Claude",  "kind": "anthropic", "base_url": "https://api.anthropic.com",                                 "model": "claude-sonnet-5-5"},
    "custom":     {"label": "Khác (tương thích OpenAI)", "kind": "openai", "base_url": "",                                                     "model": ""},
}

SYSTEM = ("Bạn là chuyên gia phân tích phần mềm mã nguồn mở cho doanh nghiệp nhỏ Việt Nam. "
          "Chỉ dựa vào thông tin được cung cấp, không bịa tính năng. Trả lời bằng tiếng Việt, ngắn gọn, "
          "và CHỈ trả về một đối tượng JSON hợp lệ, không kèm giải thích.")

PROMPT = """Repo: {name}
Ngành: {category}
License / mô hình kinh doanh an toàn: {license} — {deploy}
Mô tả: {description}
Tính năng trích từ README:
{features}

Trích README (rút gọn):
{readme}

Trả về JSON đúng cấu trúc:
{{
  "features": ["4–6 tính năng chính, mỗi ý dưới 18 từ, tiếng Việt"],
  "strengths": ["2–3 điểm mạnh nổi bật khi đóng gói thành dịch vụ bán cho doanh nghiệp nhỏ Việt Nam"],
  "niche_hint": "1 câu: ngách cụ thể ở Việt Nam nên dùng repo này, hoặc chuỗi rỗng nếu không phù hợp SME",
  "vn_improvements": ["1–3 cải tiến cần làm cho thị trường Việt Nam (vd Zalo OA, VietQR, hóa đơn điện tử)"]
}}"""


class AIError(Exception):
    def __init__(self, msg, status=None):
        super().__init__(msg)
        self.status = status

    @property
    def is_auth(self):
        return self.status in (401, 403)


class AIClient:
    def __init__(self, kind, base_url, model, api_key="", timeout=90):
        self.kind, self.base_url, self.model, self.api_key, self.timeout = kind, (base_url or "").rstrip("/"), model, api_key, timeout
        if kind not in ("openai", "anthropic"):
            raise AIError("Chưa chọn nhà cung cấp AI")
        if not self.base_url or not self.model:
            raise AIError("Thiếu địa chỉ API hoặc tên model")

    def chat(self, system, user, max_tokens=900):
        try:
            if self.kind == "anthropic":
                r = requests.post(f"{self.base_url}/v1/messages", timeout=self.timeout, headers={
                    "x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                    json={"model": self.model, "max_tokens": max_tokens, "system": system,
                          "messages": [{"role": "user", "content": user}]})
                self._check(r)
                return "".join(b.get("text", "") for b in r.json().get("content", []))
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            r = requests.post(f"{self.base_url}/chat/completions", timeout=self.timeout, headers=headers,
                              json={"model": self.model, "max_tokens": max_tokens, "temperature": 0.2,
                                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
            self._check(r)
            return r.json()["choices"][0]["message"]["content"] or ""
        except requests.Timeout:
            raise AIError(f"Hết thời gian chờ phản hồi từ {self.base_url}. Model có thể quá chậm hoặc máy chủ quá tải.")
        except requests.RequestException as e:
            raise AIError(f"Không kết nối được tới {self.base_url} ({e.__class__.__name__}). "
                          "Kiểm tra địa chỉ API, mạng, hoặc Ollama/LM Studio đã chạy chưa.")
        except (KeyError, IndexError, TypeError, ValueError):
            raise AIError("Phản hồi của API không đúng định dạng mong đợi. Kiểm tra lại loại API và địa chỉ.")

    @staticmethod
    def _check(r):
        if r.status_code == 200:
            return
        try:
            msg = r.json()
            msg = msg.get("error", msg)
            msg = msg.get("message", msg) if isinstance(msg, dict) else msg
        except Exception:
            msg = r.text[:200]
        hint = {400: "Yêu cầu không hợp lệ — thường do sai tên model", 401: "API key sai hoặc hết hạn",
                402: "Tài khoản hết tiền", 403: "Key không có quyền dùng model này", 404: "Sai địa chỉ API hoặc tên model",
                429: "Vượt giới hạn gọi API hoặc hết tiền trong tài khoản"}.get(r.status_code, "")
        if r.status_code >= 500:
            hint = "Máy chủ AI đang lỗi, thử lại sau"
        raise AIError(f"Lỗi {r.status_code}{' — ' + hint if hint else ''}: {str(msg)[:200]}", status=r.status_code)

    def test(self):
        out = self.chat("Trả lời đúng một từ.", "Nói 'ok'.", max_tokens=20)
        return out.strip()[:60]

    def summarize(self, repo, raw):
        user = PROMPT.format(
            name=repo["name"], category=repo["category_label"], license=repo["license"], deploy=repo["deploy_model"],
            description=repo["description"][:400],
            features="\n".join("- " + f for f in (raw.get("features_raw") or [])[:15]) or "(không có)",
            readme=_squeeze(raw.get("readme", ""))[:5000] or "(không có)")
        text = self.chat(SYSTEM, user)
        data = parse_json(text)
        if not data:
            raise AIError("AI không trả về JSON hợp lệ")
        clean = lambda xs, n: [str(x).strip() for x in (xs or []) if str(x).strip()][:n]
        return {"features": clean(data.get("features"), 6), "strengths": clean(data.get("strengths"), 3),
                "niche_hint": str(data.get("niche_hint") or "").strip()[:300],
                "vn_improvements": clean(data.get("vn_improvements"), 3)}


def parse_json(text):
    """Đọc JSON từ phản hồi AI: chịu được markdown fence, lời dẫn trước/sau, thẻ <think>."""
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    text = re.sub(r"^\s*```[a-zA-Z]*\s*$|^\s*```\s*$", "", text.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        # thử đối tượng JSON đầu tiên đứng riêng
        try:
            data, _ = json.JSONDecoder().raw_decode(text[text.index("{"):])
        except (ValueError, json.JSONDecodeError):
            return None
    return data if isinstance(data, dict) else None


def _squeeze(md):
    md = re.sub(r"```.*?```", "", md, flags=re.S)       # bỏ khối code
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)|<img[^>]*>", "", md)
    md = re.sub(r"<[^>]+>", "", md)
    return re.sub(r"\n{3,}", "\n\n", md)


def cache_key(repo, raw):
    h = hashlib.sha1(((raw.get("readme") or "")[:6000] + repo["description"]).encode("utf-8", "ignore")).hexdigest()[:12]
    return f"{repo['name'].lower()}:{h}"


def client_from_settings(ai: dict):
    """Tạo AIClient từ settings['ai']; trả None nếu chế độ không dùng AI."""
    if not ai or ai.get("provider", "none") == "none":
        return None
    return AIClient(ai.get("kind", "openai"), ai.get("base_url", ""), ai.get("model", ""), ai.get("api_key", ""))


def apply_summary(rec, summ):
    rec["features"] = summ["features"] or rec["features"]
    rec["strengths"] = summ["strengths"]
    rec["niche_hint"] = summ.get("niche_hint", "")
    rec["feat_src"] = "ai"
    rec["ai_model"] = summ.get("model", "")
    vi = summ.get("vn_improvements") or []
    rec["improvements"] = list(dict.fromkeys(vi + rec["improvements"]))


def candidates(repos, max_repos):
    """Repo an toàn license, chưa có tóm tắt tay, ưu tiên điểm cao."""
    safe = ("permissive", "gpl", "agpl", "single-tenant")
    cs = [r for r in repos if r["license_group"] in safe and r.get("feat_src") != "curated"]
    cs.sort(key=lambda r: r["score"]["total"], reverse=True)
    return cs[:max_repos]


def enrich(repos, raw_by_name, client, cache, max_repos=60, workers=3, progress=None, stop_event=None, log=None):
    """Gắn tóm tắt AI vào repo. Dùng cache trước; chỉ gọi AI cho repo mới hoặc README đổi.
    Trả dict thống kê {summarized, calls, errors, aborted, error}."""
    progress = progress or (lambda *a: None)
    stop_event = stop_event or threading.Event()
    log = log or (lambda m: None)
    stats = {"summarized": 0, "calls": 0, "errors": 0, "aborted": False, "error": ""}

    # Áp dụng cache cho mọi repo (không tốn phí, kể cả khi đã tắt AI)
    for r in repos:
        if r.get("feat_src") == "curated":
            continue
        raw = raw_by_name.get(r["name"].lower(), {})
        r["ai_key"] = cache_key(r, raw)
        if r["ai_key"] in cache:
            apply_summary(r, cache[r["ai_key"]])
    if client is None:
        return stats

    todo = [r for r in candidates(repos, max_repos) if r["ai_key"] not in cache]
    stats["summarized"] = sum(1 for r in candidates(repos, max_repos) if r["ai_key"] in cache)
    if not todo:
        return stats
    lock = threading.Lock()
    first = []           # kết quả của các lần gọi đầu tiên: True = lỗi xác thực
    abort = threading.Event()

    def work(r):
        if abort.is_set() or stop_event.is_set():
            return
        try:
            summ = client.summarize(r, raw_by_name.get(r["name"].lower(), {}))
            summ.update(model=client.model, at=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))
            with lock:
                stats["calls"] += 1
                if len(first) < 3:
                    first.append(False)
                cache[r["ai_key"]] = summ
                apply_summary(r, summ)
                stats["summarized"] += 1
        except AIError as e:
            with lock:
                stats["calls"] += 1
                stats["errors"] += 1
                stats["error"] = stats["error"] or str(e)
                log(f"AI lỗi ở {r['name']}: {e}")
                if len(first) < 3:
                    first.append(e.is_auth)
                    if len(first) == 3 and all(first):
                        abort.set()
                        stats["aborted"] = True
                        stats["error"] = f"Dừng bước AI vì 3 repo đầu đều lỗi xác thực: {e}"
        except Exception as e:  # lỗi bất ngờ ở một repo không làm hỏng lần quét
            with lock:
                stats["errors"] += 1
                log(f"AI lỗi ở {r['name']}: {e.__class__.__name__}")
        finally:
            with lock:
                done[0] += 1
                progress("ai", done[0], len(todo), f"AI tóm tắt ({client.model})")

    done = [0]
    progress("ai", 0, len(todo), f"AI tóm tắt ({client.model})")
    with ThreadPoolExecutor(max(1, workers)) as ex:
        list(ex.map(work, todo))
    return stats


def estimate(repos, cache, max_repos, enabled):
    cs = candidates(repos or [], max_repos)
    cached = sum(1 for r in cs if r.get("ai_key") and r["ai_key"] in cache)
    return {"enabled": enabled, "candidates": len(cs), "cached": cached, "calls": len(cs) - cached if enabled else 0}
