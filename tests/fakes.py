# -*- coding: utf-8 -*-
"""Máy chủ giả lập GitHub (search API + raw), AI (OpenAI/Anthropic) và Telegram cho test offline."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

FIX = json.loads((Path(__file__).parent / "fixtures" / "licenses.json").read_text(encoding="utf-8"))

README = """# {name}

Open-source {desc}

## Features

- Manage customers, leads and deals in one place
- Kanban board for the sales pipeline
- Email and live chat inbox for the support team
- Invoices and quotes with PDF export
- Role-based permissions for your team

## Installation

- Run docker compose up
"""


def make_repo(full, stars, lic_fixture=None, topics=("crm",), desc="CRM for small business teams", created="2023-01-01T00:00:00Z"):
    fx = FIX[lic_fixture] if lic_fixture else {"spdx": "MIT", "license_text": "Permission is hereby granted, free of charge, to any person", "paths_sample": ["docker-compose.yml"]}
    return {
        "item": {"full_name": full, "html_url": f"https://github.com/{full}", "description": desc, "homepage": "",
                 "stargazers_count": stars, "forks_count": 10, "open_issues_count": 1, "language": "TypeScript",
                 "topics": list(topics), "created_at": created, "pushed_at": "2026-11-01T00:00:00Z",
                 "default_branch": "main", "license": {"spdx_id": fx["spdx"], "name": fx["spdx"]}},
        "files": {"LICENSE": fx["license_text"], "README.md": README.format(name=full, desc=desc),
                  **{p: "x" for p in fx["paths_sample"]}},
    }


class FakeGitHub:
    def __init__(self, repos, delay=0.0):
        self.repos = {r["item"]["full_name"]: r for r in repos}
        self.delay = delay
        self.search_calls = 0
        self.raw_calls = 0
        self.status = 200
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, code, body=b"", ctype="application/json"):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)

            def do_HEAD(self):
                self.do_GET()

            def do_GET(self):
                u = urlparse(self.path)
                if u.path.startswith("/api/search/repositories"):
                    outer.search_calls += 1
                    if outer.status != 200:
                        return self._send(outer.status, b'{"message":"Bad credentials"}')
                    items = [r["item"] for r in outer.repos.values()]
                    n = int(parse_qs(u.query).get("per_page", ["20"])[0])
                    return self._send(200, json.dumps({"items": items[:n]}).encode())
                if u.path.startswith("/raw/"):
                    outer.raw_calls += 1
                    if outer.delay:
                        time.sleep(outer.delay)
                    parts = u.path[len("/raw/"):].split("/")
                    full, path = "/".join(parts[:2]), "/".join(parts[3:])
                    f = outer.repos.get(full, {}).get("files", {}).get(path)
                    if f is None:
                        return self._send(404, b"404")
                    return self._send(200, f.encode(), "text/plain; charset=utf-8")
                self._send(404)

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    @property
    def api(self):
        return self.url + "/api"

    @property
    def raw(self):
        return self.url + "/raw"

    def close(self):
        self.httpd.shutdown()


AI_JSON = {"features": ["Quản lý khách hàng và cơ hội", "Bảng kanban bán hàng", "Hộp thư email và chat",
                        "Báo giá, hóa đơn PDF"],
           "strengths": ["Dễ đóng gói SaaS cho SME", "Giao diện hiện đại"],
           "niche_hint": "CRM cho đội môi giới BĐS",
           "vn_improvements": ["Tích hợp Zalo OA"]}


class FakeAI:
    """Máy chủ AI tương thích OpenAI + Anthropic. mode: ok | auth | fence"""

    def __init__(self, mode="ok", key="sk-test-123456"):
        self.mode, self.key, self.calls = mode, key, 0
        self.last_body = None
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, code, obj):
                body = json.dumps(obj).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                n = int(self.headers.get("Content-Length", 0))
                outer.last_body = json.loads(self.rfile.read(n) or b"{}")
                outer.calls += 1
                key = self.headers.get("x-api-key") or self.headers.get("Authorization", "").replace("Bearer ", "")
                if outer.mode == "auth" or key != outer.key:
                    return self._send(401, {"error": {"message": "Incorrect API key provided"}})
                user = json.dumps(outer.last_body, ensure_ascii=False)
                text = "ok" if "Nói 'ok'" in user else json.dumps(AI_JSON, ensure_ascii=False)
                if outer.mode == "fence":
                    text = "Đây là kết quả:\n```json\n" + text + "\n```"
                if self.path.endswith("/v1/messages"):
                    return self._send(200, {"content": [{"type": "text", "text": text}]})
                if self.path.endswith("/chat/completions"):
                    return self._send(200, {"choices": [{"message": {"content": text}}]})
                self._send(404, {"error": {"message": "not found"}})

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
