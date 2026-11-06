# -*- coding: utf-8 -*-
"""Lớp AI dùng được với mọi nhà cung cấp.

- "openai": mọi API tương thích OpenAI Chat Completions — OpenAI, Google Gemini,
  DeepSeek, Groq, OpenRouter, Mistral, Together, Ollama, LM Studio, vLLM...
- "anthropic": Claude (API Messages riêng của Anthropic)
- "none": không dùng AI; app vẫn chạy, chỉ hiển thị tính năng trích từ README
"""
import json, re, hashlib
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
    pass


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
        except requests.RequestException as e:
            raise AIError(f"Không kết nối được tới {self.base_url}: {e.__class__.__name__}")

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
        hint = {401: "API key sai hoặc hết hạn", 403: "Key không có quyền dùng model này", 404: "Sai địa chỉ API hoặc tên model",
                429: "Vượt giới hạn gọi API hoặc hết tiền trong tài khoản"}.get(r.status_code, "")
        raise AIError(f"Lỗi {r.status_code}{' — ' + hint if hint else ''}: {str(msg)[:200]}")

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
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _squeeze(md):
    md = re.sub(r"```.*?```", "", md, flags=re.S)       # bỏ khối code
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)|<img[^>]*>", "", md)
    md = re.sub(r"<[^>]+>", "", md)
    return re.sub(r"\n{3,}", "\n\n", md)


def cache_key(repo, raw):
    h = hashlib.sha1(((raw.get("readme") or "")[:6000] + repo["description"]).encode("utf-8", "ignore")).hexdigest()[:12]
    return f"{repo['name'].lower()}:{h}"
