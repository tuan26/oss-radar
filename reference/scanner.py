# -*- coding: utf-8 -*-
"""Quét GitHub: tìm repo theo ngành, đọc LICENSE, README, file Docker qua raw.githubusercontent.com.
Không cần GitHub token (có token thì quét nhanh hơn vì giới hạn tìm kiếm cao hơn)."""
import re, time, base64, datetime as dt
from concurrent.futures import ThreadPoolExecutor
import requests

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

LIC_FILES = ["LICENSE", "LICENSE.md", "LICENSE.txt", "LICENSE.MD", "COPYING", "LICENCE", "license", "LICENSE-AGPL"]
PROBE = ["docker-compose.yml", "docker-compose.yaml", "compose.yaml", "compose.yml", "Dockerfile",
         "docker/docker-compose.yml", "docker/docker-compose.yaml", "deploy/docker-compose.yml",
         "ee/LICENSE", "enterprise/LICENSE", "ee/LICENSE.md", "packages/ee/LICENSE", "apps/ee/LICENSE",
         "charts/Chart.yaml", "helm/Chart.yaml"]


class Scanner:
    def __init__(self, github_token="", min_stars=800, categories=None, progress=None, should_stop=None):
        self.s = requests.Session()
        self.s.headers.update({"Accept": "application/vnd.github+json", "User-Agent": "oss-radar"})
        if github_token:
            self.s.headers["Authorization"] = f"Bearer {github_token}"
        # Tìm kiếm: 30 lần/phút khi có token, 10 lần/phút khi không có
        self.search_gap = 2.2 if github_token else 6.5
        self.min_stars = min_stars
        self.categories = {k: v for k, v in CATEGORIES.items() if not categories or k in categories}
        self.progress = progress or (lambda *a, **k: None)
        self.should_stop = should_stop or (lambda: False)

    # ---------- tìm kiếm ----------
    def _search(self, q, per_page):
        for attempt in range(5):
            r = self.s.get(f"{API}/search/repositories", params={"q": q, "sort": "stars", "order": "desc", "per_page": per_page}, timeout=30)
            if r.status_code == 200:
                time.sleep(self.search_gap)
                return r.json().get("items", [])
            if r.status_code in (403, 429):
                reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
                time.sleep(max(5, min(70, reset - time.time() + 2)))
                continue
            if r.status_code == 401:
                raise RuntimeError("GitHub token không hợp lệ. Xóa hoặc sửa token trong Cài đặt.")
            time.sleep(3 * (attempt + 1))
        return []

    def search_all(self):
        since = (dt.date.today() - dt.timedelta(days=548)).isoformat()
        jobs = []
        for cat, queries in self.categories.items():
            for q in queries:
                jobs.append((cat, f"{q} stars:>={self.min_stars} archived:false", "top", 20))
                jobs.append((cat, f"{q} stars:>=300 created:>={since} archived:false", "rising", 10))
        repos = {}
        for i, (cat, q, tag, n) in enumerate(jobs, 1):
            if self.should_stop():
                raise InterruptedError
            self.progress("search", i, len(jobs), f"Tìm repo: {cat}")
            for it in self._search(q, n):
                key = it["full_name"].lower()
                rec = repos.setdefault(key, {"item": it, "categories": set(), "tags": set()})
                rec["categories"].add(cat)
                rec["tags"].add(tag)
        return repos

    # ---------- chi tiết ----------
    def _raw(self, full, branch, path):
        try:
            r = requests.get(f"{RAW}/{full}/{branch}/{path}", timeout=20)
            if r.status_code == 200:
                return r.text[:40000]
        except Exception:
            pass
        return None

    def _detail(self, rec):
        it = rec["item"]
        full, branch = it["full_name"], it.get("default_branch", "main")
        lic_text, lic_path = "", ""
        for p in LIC_FILES:
            t = self._raw(full, branch, p)
            if t:
                lic_text, lic_path = t, p
                break
        paths = [p for p in PROBE if self._raw(full, branch, p) is not None]
        readme = ""
        for p in ["README.md", "readme.md", "README.MD", "Readme.md", "README.rst", "docs/README.md"]:
            t = self._raw(full, branch, p)
            if t and len(t) > 200:
                readme = t
                break
        return {
            "full_name": full, "url": it["html_url"], "description": it.get("description") or "",
            "homepage": it.get("homepage") or "", "stars": it["stargazers_count"], "forks": it["forks_count"],
            "open_issues": it["open_issues_count"], "language": it.get("language"), "topics": it.get("topics", []),
            "created_at": it["created_at"], "pushed_at": it["pushed_at"],
            "spdx": (it.get("license") or {}).get("spdx_id") or "NONE",
            "license_name": (it.get("license") or {}).get("name") or "",
            "license_path": lic_path, "license_text": lic_text, "branch": branch,
            "categories": sorted(rec["categories"]), "tags": sorted(rec["tags"]),
            "paths_sample": paths,
            "readme_vi": bool(re.search(r"ti[eế]ng vi[eệ]t|vietnam|vi[-_]VN|🇻🇳", readme, re.I)),
            "readme": readme,
            "features_raw": extract_features(readme),
        }

    def details(self, repos):
        recs = list(repos.values())
        out = []
        with ThreadPoolExecutor(12) as ex:
            for n, res in enumerate(ex.map(self._detail, recs), 1):
                if self.should_stop():
                    ex.shutdown(cancel_futures=True)
                    raise InterruptedError
                out.append(res)
                if n % 5 == 0 or n == len(recs):
                    self.progress("detail", n, len(recs), "Đọc license, README, Docker")
        return out

    def run(self):
        return self.details(self.search_all())


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
