# -*- coding: utf-8 -*-
"""Quét GitHub: tìm repo theo ngành, đọc LICENSE, README, file Docker qua raw.githubusercontent.com.
Không cần GitHub token (có token thì quét nhanh hơn vì giới hạn tìm kiếm cao hơn).
Dùng lại từ reference/scanner.py, thêm dừng nhanh, pipeline tìm kiếm/chi tiết, kết nối dùng chung."""
import re, time, threading, datetime as dt
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import requests
import requests.adapters

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"

CATEGORIES = {
    "crm": ["topic:crm", "topic:sales-pipeline"],
    "helpdesk": ["topic:helpdesk", "topic:customer-support", "topic:live-chat"],
    "booking": ["topic:scheduling", "topic:appointment-booking", "topic:booking-system"],
    "ecommerce": ["topic:ecommerce-platform", "topic:headless-commerce"],
    "pos-inventory": ["topic:inventory-management", "topic:point-of-sale"],
    "erp-accounting": ["topic:erp", "topic:accounting", "topic:invoicing"],
    "hr": ["topic:hrms", "topic:human-resources"],
    "lms": ["topic:lms", "topic:learning-management-system"],
    "marketing-automation": ["topic:marketing-automation", "topic:email-marketing", "topic:newsletter"],
    "workflow-automation": ["topic:workflow-automation", "topic:no-code"],
    "ai-chatbot": ["topic:chatbot", "topic:rag", "topic:llm-app"],
    "analytics-bi": ["topic:web-analytics", "topic:business-intelligence"],
    "forms-survey": ["topic:form-builder", "topic:survey"],
    "project-management": ["topic:project-management", "topic:kanban"],
    "document-signing": ["topic:document-signing", "topic:e-signature"],
    "website-cms": ["topic:headless-cms", "topic:website-builder"],
    "healthcare": ["topic:ehr", "topic:clinic-management", "topic:healthcare"],
    "restaurant": ["topic:restaurant", "topic:food-ordering"],
    "property": ["topic:property-management", "topic:hotel-management"],
}

LIC_FILES = ["LICENSE", "LICENSE.md", "LICENSE.txt", "LICENSE.MD", "COPYING", "COPYING.md", "LICENCE",
             "license", "license.txt", "license.md", "LICENSE-AGPL", "LICENSE-MIT", "LICENSE-APACHE"]
PROBE = ["docker-compose.yml", "docker-compose.yaml", "compose.yaml", "compose.yml", "Dockerfile",
         "docker/docker-compose.yml", "docker/docker-compose.yaml", "deploy/docker-compose.yml",
         "ee/LICENSE", "enterprise/LICENSE", "ee/LICENSE.md", "packages/ee/LICENSE", "apps/ee/LICENSE",
         "charts/Chart.yaml", "helm/Chart.yaml"]
README_FILES = ["README.md", "readme.md", "README.MD", "Readme.md", "README.rst", "docs/README.md"]


class ScanStopped(Exception):
    """Người dùng bấm Dừng."""


class GitHubAuthError(RuntimeError):
    pass


class Scanner:
    """Quét theo kiểu pipeline: repo nào vừa tìm thấy thì đưa ngay vào hàng đọc chi tiết
    (12 luồng) trong khi các truy vấn tìm kiếm tiếp tục chạy theo giới hạn tốc độ."""

    def __init__(self, github_token="", min_stars=800, categories=None, progress=None, stop_event=None,
                 api=API, raw=RAW, search_gap=None, workers=12):
        self.api, self.rawbase = api.rstrip("/"), raw.rstrip("/")
        self.s = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=max(16, workers + 4))
        self.s.mount("https://", adapter)
        self.s.mount("http://", adapter)
        self.s.headers.update({"User-Agent": "oss-radar"})
        self.api_headers = {"Accept": "application/vnd.github+json"}
        if github_token:
            self.api_headers["Authorization"] = f"Bearer {github_token}"
        # Tìm kiếm: 30 lần/phút khi có token, 10 lần/phút khi không có
        self.search_gap = search_gap if search_gap is not None else (2.2 if github_token else 6.5)
        self.min_stars = min_stars
        self.categories = {k: v for k, v in CATEGORIES.items() if not categories or k in categories}
        self.progress = progress or (lambda *a, **k: None)
        self.stop = stop_event or threading.Event()
        self.workers = workers
        self._last_search = 0.0

    def _check_stop(self):
        if self.stop.is_set():
            raise ScanStopped

    # ---------- tìm kiếm ----------
    def _pace(self):
        """Giữ khoảng cách tối thiểu search_gap giữa hai lần gọi tìm kiếm (thời gian request được tính vào)."""
        wait = self._last_search + self.search_gap - time.monotonic()
        if wait > 0:
            self.stop.wait(wait)
        self._check_stop()
        self._last_search = time.monotonic()

    def _search(self, q, per_page):
        for attempt in range(5):
            self._pace()
            try:
                r = self.s.get(f"{self.api}/search/repositories", headers=self.api_headers, timeout=30,
                               params={"q": q, "sort": "stars", "order": "desc", "per_page": per_page})
            except requests.RequestException:
                self.stop.wait(3 * (attempt + 1))
                continue
            if r.status_code == 200:
                return r.json().get("items", [])
            if r.status_code == 401:
                raise GitHubAuthError("GitHub token không hợp lệ. Xóa hoặc sửa token trong Cài đặt.")
            if r.status_code in (403, 429):
                try:
                    reset = int(r.headers.get("X-RateLimit-Reset", ""))
                except ValueError:
                    reset = int(time.time() + 60)
                self.progress(None, None, None, "GitHub giới hạn tốc độ, đang chờ…")
                self.stop.wait(max(5, min(70, reset - time.time() + 2)))
                continue
            self.stop.wait(3 * (attempt + 1))
        return []

    def search_jobs(self):
        since = (dt.date.today() - dt.timedelta(days=548)).isoformat()
        jobs = []
        for cat, queries in self.categories.items():
            for q in queries:
                jobs.append((cat, f"{q} stars:>={self.min_stars} archived:false", "top", 20))
                jobs.append((cat, f"{q} stars:>=300 created:>={since} archived:false", "rising", 10))
        return jobs

    # ---------- chi tiết ----------
    def _raw(self, full, branch, path, head=False):
        if self.stop.is_set():
            return None
        url = f"{self.rawbase}/{full}/{branch}/{path}"
        try:
            if head:
                r = self.s.head(url, timeout=15, allow_redirects=True)
                return "" if r.status_code == 200 else None
            r = self.s.get(url, timeout=15)
            if r.status_code == 200:
                return r.text[:40000]
        except Exception:
            pass
        return None

    def _detail(self, it):
        full, branch = it["full_name"], it.get("default_branch") or "main"
        lic_text, lic_path = "", ""
        for p in LIC_FILES:
            t = self._raw(full, branch, p)
            if t:
                lic_text, lic_path = t, p
                break
        paths = [p for p in PROBE if self._raw(full, branch, p, head=True) is not None]
        readme = ""
        for p in README_FILES:
            t = self._raw(full, branch, p)
            if t and len(t) > 200:
                readme = t
                break
        return {
            "full_name": full, "url": it["html_url"], "description": it.get("description") or "",
            "homepage": it.get("homepage") or "", "stars": it["stargazers_count"], "forks": it.get("forks_count", 0),
            "open_issues": it.get("open_issues_count", 0), "language": it.get("language"), "topics": it.get("topics") or [],
            "created_at": it["created_at"], "pushed_at": it["pushed_at"],
            "spdx": (it.get("license") or {}).get("spdx_id") or "NONE",
            "license_name": (it.get("license") or {}).get("name") or "",
            "license_path": lic_path, "license_text": lic_text, "branch": branch,
            "paths_sample": paths,
            "readme_vi": bool(re.search(r"ti[eế]ng vi[eệ]t|vietnam|vi[-_]VN|🇻🇳", readme, re.I)),
            "readme": readme,
            "features_raw": extract_features(readme),
        }

    def _safe_detail(self, it):
        try:
            return self._detail(it)
        except Exception:
            return None  # lỗi ở một repo không làm hỏng cả lần quét

    def run(self):
        jobs = self.search_jobs()
        repos, futures = {}, {}
        ex = ThreadPoolExecutor(self.workers)
        try:
            for i, (cat, q, tag, n) in enumerate(jobs, 1):
                self._check_stop()
                self.progress("search", i, len(jobs), f"Tìm repo: {cat}")
                for it in self._search(q, n):
                    key = it["full_name"].lower()
                    rec = repos.setdefault(key, {"item": it, "categories": set(), "tags": set()})
                    rec["categories"].add(cat)
                    rec["tags"].add(tag)
                    if key not in futures:
                        futures[key] = ex.submit(self._safe_detail, it)
            total = len(futures)
            out, done = [], 0
            for key, fut in futures.items():
                while True:
                    self._check_stop()
                    try:
                        res = fut.result(timeout=0.5)
                        break
                    except FutureTimeout:
                        continue
                done += 1
                if res:
                    res["categories"] = sorted(repos[key]["categories"])
                    res["tags"] = sorted(repos[key]["tags"])
                    out.append(res)
                if done % 5 == 0 or done == total:
                    self.progress("detail", done, total, "Đọc license, README, Docker")
            return out
        finally:
            ex.shutdown(wait=False, cancel_futures=True)


# ---------- trích tính năng từ README ----------
HEAD = re.compile(r"^(#{1,4})\s*(.+?)\s*#*\s*$")
FEAT_HEAD = re.compile(r"feature|highlight|what can|why |capabilit|key |overview|what is|what's included|functionality|modules|benefits", re.I)
BULLET = re.compile(r"^\s{0,3}[-*+]\s+(.*)$|^\s{0,3}\d+[.)]\s+(.*)$")
JUNK = re.compile(r"(version|release|^example|docs?/|\.md\b|quickstart|reference|install|configur|troubleshoot|frontend|backend|^users:|^operators:|^developers:|^maintainers:|documentation|getting started|tutorial|architecture$|license|contribut|sponsor|requirement|^introduction$|security vulnerab|go to |open your browser|if you see|^run |^use brew|^build the)", re.I)


def _clean(t):
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"[*_`]{1,3}", "", t)
    t = re.sub(r":[a-z_]+:", "", t)
    t = re.sub(r"[\U0001F000-\U0001FFFF☀-➿️]", "", t)
    return re.sub(r"\s+", " ", t).strip(" -–—:|")


def extract_features(md):
    if not md:
        return []
    sections, cur = [], None
    for ln in md.splitlines():
        m = HEAD.match(ln)
        if m:
            cur = {"title": _clean(m.group(2)), "level": len(m.group(1)), "bullets": []}
            sections.append(cur)
            continue
        if cur is None:
            continue
        b = BULLET.match(ln)
        if b:
            txt = _clean(b.group(1) or b.group(2) or "")
            if 8 <= len(txt) <= 260 and not re.match(r"(https?://|npm |pip |docker |git |cd |yarn )", txt, re.I):
                cur["bullets"].append(txt)
    picked = []
    for i, s in enumerate(sections):
        if FEAT_HEAD.search(s["title"]):
            picked += s["bullets"]
            for t in sections[i + 1:]:
                if t["level"] <= s["level"]:
                    break
                if t["bullets"]:
                    picked += t["bullets"][:3]
                elif len(t["title"]) < 80:
                    picked.append(t["title"])
        if len(picked) >= 25:
            break
    if len(picked) < 3:
        for s in sections:
            if len(s["bullets"]) >= 4 and not re.search(r"install|setup|contribut|license|sponsor|support|requirement|prerequisite|deploy|community|contents", s["title"], re.I):
                picked = s["bullets"]
                break
    picked = [re.sub(r"^\[[ xX]\]\s*", "", p) for p in picked]
    picked = [p for p in picked if not JUNK.search(p)]
    seen, out = set(), []
    for p in picked:
        k = p.lower()[:60]
        if k not in seen:
            seen.add(k)
            out.append(p)
    return out[:18] if len(out) >= 3 else []
