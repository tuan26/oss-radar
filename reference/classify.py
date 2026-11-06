# -*- coding: utf-8 -*-
"""Phân loại license, chọn mô hình triển khai an toàn, chấm điểm, gán playbook bán hàng.
Đọc raw.json (+ snapshot tuần trước nếu có) -> data.json
"""
import json, math, re, os, datetime as dt
from knowledge import KB, DEFAULT, CATEGORY_LABEL

NOW = dt.datetime.now(dt.timezone.utc)

PERMISSIVE = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD", "Unlicense",
              "Zlib", "PostgreSQL", "MIT-0", "BSL-1.0", "CC0-1.0"}
WEAK_COPYLEFT = {"MPL-2.0", "LGPL-2.1", "LGPL-3.0", "EPL-2.0", "LGPL-2.1-only", "LGPL-3.0-only"}
GPL = {"GPL-2.0", "GPL-3.0", "GPL-2.0-only", "GPL-3.0-only", "GPL-2.0-or-later", "GPL-3.0-or-later"}
AGPL = {"AGPL-3.0", "AGPL-3.0-only", "AGPL-3.0-or-later"}
RESTRICTED_SPDX = {"BUSL-1.1", "SSPL-1.0", "Elastic-2.0", "CC-BY-NC-4.0", "CC-BY-NC-SA-4.0", "PolyForm-Noncommercial-1.0.0"}

# Dấu hiệu trong nội dung license
COMPETE_PATTERNS = [
    (r"sustainable use license", "Sustainable Use License (fair-code)"),
    (r"elastic license", "Elastic License"),
    (r"business source license", "Business Source License (BSL)"),
    (r"server side public license", "SSPL"),
    (r"commons clause", "Commons Clause"),
    (r"functional source license|\bfsl-1", "Functional Source License"),
    (r"polyform", "PolyForm"),
    (r"you may not use the software for commercial|non-commercial use only|for non-commercial purposes only", "Cấm thương mại"),
    (r"may not provide the software to third parties as a hosted or managed service", "Cấm cung cấp dạng dịch vụ"),
]
TENANT_PATTERNS = [
    (r"multi-?tenant", "Cấm vận hành multi-tenant nếu không có phép"),
    (r"(remove|modify)[^.]{0,60}(logo|copyright information)", "Không được gỡ logo/bản quyền"),
    (r"(alter|remove|obscure|replace)[^.]{0,100}branding", "Không được gỡ/đổi thương hiệu gốc"),
]
ENTERPRISE_DIRS = re.compile(r"^(ee|enterprise|packages/ee|apps/ee|src/ee|premium|ee_?src)(/|$)", re.I)
VI_LOCALE = re.compile(r"(^|/)(vi|vi[-_]vn)(\.json|\.ya?ml|\.po|\.ts|\.js|\.php|/)", re.I)
NOT_APP = re.compile(r"\b(awesome|curated list|list of|tutorials?|boilerplate|starter kit|sdk|client library|component library|ui kit|examples?|learn(ing)? to build|handbook|dataset|papers|roadmap|public data|interview)\b", re.I)


TEXT_SIGNATURES = [  # nhận diện license chuẩn khi GitHub báo NOASSERTION
    (r"gnu affero general public license", "AGPL-3.0"),
    (r"gnu lesser general public license", "LGPL-3.0"),
    (r"gnu general public license", "GPL-3.0"),
    (r"open software license", "OSL-3.0"),
    (r"mozilla public license", "MPL-2.0"),
    (r"eclipse public license", "EPL-2.0"),
    (r"apache license", "Apache-2.0"),
    (r"permission is hereby granted, free of charge", "MIT"),
    (r"redistribution and use in source and binary forms", "BSD-3-Clause"),
    (r"educational community license", "Apache-2.0"),
]
NETWORK_COPYLEFT = AGPL | {"OSL-3.0"}
WEAK_COPYLEFT |= {"EPL-1.0", "CDDL-1.0"}
PERMISSIVE |= {"ECL-2.0", "CC-BY-4.0", "Artistic-2.0"}


def effective_spdx(spdx, text):
    if spdx not in ("NOASSERTION", "OTHER", "NONE") or not text:
        return spdx, False
    for pat, sp in TEXT_SIGNATURES:
        if re.search(pat, text):
            return sp, True
    return spdx, False


def classify_license(r):
    raw_spdx = r["spdx"]
    text = (r.get("license_text") or "").lower()
    enterprise = sorted({p.rsplit("/", 1)[0] for p in r.get("paths_sample", []) if ENTERPRISE_DIRS.match(p)})
    if not enterprise and re.search(r"(\bee/|enterprise (edition|directory|folder|features)|/ee\b|commercial license.{0,80}(director|folder))", text):
        enterprise = ["thư mục enterprise (xem license)"]
    spdx, inferred = effective_spdx(raw_spdx, text)
    tag = spdx + (" (đọc từ file)" if inferred else "")

    compete = [label for pat, label in COMPETE_PATTERNS if re.search(pat, text)]
    tenant = [label for pat, label in TENANT_PATTERNS if re.search(pat, text)]
    mixed = bool(enterprise)

    def res(group, label, model, detail, safe, flags):
        if mixed and group in ("permissive", "gpl", "agpl"):
            detail += " Repo có phần enterprise dùng license thương mại riêng: chỉ dùng phần lõi."
        return dict(group=group, label=label, model=model, model_detail=detail, safe=safe, flags=flags, enterprise=enterprise)

    if raw_spdx == "NONE" and not text:
        return res("none", "Không có license", "Loại", "Không có license = mặc định giữ mọi quyền, không được dùng lại. Bỏ qua.", 0, ["Không có license"])
    if raw_spdx in RESTRICTED_SPDX or compete:
        flags = list(dict.fromkeys(compete or [raw_spdx]))
        return res("restricted", "Hạn chế: " + ", ".join(flags), "Loại",
                   "License hạn chế dùng để bán dịch vụ. Không host bán lại. Chỉ dùng nội bộ, hoặc liên hệ tác giả mua license thương mại.", 0, flags)
    if tenant:
        return res("single-tenant", tag + " + điều khoản phụ", "Triển khai riêng từng khách",
                   "Điều khoản phụ: " + "; ".join(tenant) + ". Mỗi khách một instance riêng (server riêng hoặc server của khách), không gom nhiều khách chung một hệ thống, giữ nguyên logo. Đọc kỹ license trước khi ký hợp đồng.", 12, tenant)
    if spdx in NETWORK_COPYLEFT:
        return res("agpl", tag, "SaaS được, công khai phần sửa",
                   "Được host bán dịch vụ, nhưng sửa đổi trong code gốc phải công khai cho người dùng. Viết tích hợp VN thành service riêng gọi qua API để giữ phần riêng của bạn.", 20, [])
    if spdx in GPL:
        return res("gpl", tag, "SaaS được",
                   "Host làm dịch vụ không bắt buộc công khai code. Nếu cài lên server của khách (phân phối) thì phải giao kèm mã nguồn.", 24, [])
    if spdx in WEAK_COPYLEFT:
        return res("permissive", tag, "SaaS thoải mái",
                   "Copyleft yếu: chỉ phải công khai nếu sửa chính các file gốc. Thoải mái host multi-tenant.", 28, [])
    if spdx in PERMISSIVE:
        return res("permissive", tag, "SaaS thoải mái",
                   "License dễ dãi: được host multi-tenant, sửa đổi giữ riêng. Chỉ cần giữ thông báo bản quyền.", 30, [])
    return res("unknown", "Không xác định (" + raw_spdx + ")", "Cần đọc tay",
               "License tùy biến, công cụ không tự phân loại được. Đọc file license trước khi dùng.", 5, ["License tùy biến"])


def days_since(iso):
    if not iso:
        return 9999
    return (NOW - dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))).days


CAT_WORDS = {
    "crm": r"crm|sales|lead|pipeline|customer relationship",
    "helpdesk": r"helpdesk|help desk|ticket|customer support|live chat|support desk|omnichannel|inbox",
    "booking": r"booking|appointment|schedul|calendar|reservation",
    "ecommerce": r"e-?commerce|shop|store|cart|commerce|marketplace",
    "pos-inventory": r"inventory|point of sale|\bpos\b|warehouse|stock",
    "erp-accounting": r"\berp\b|accounting|invoice|bookkeeping|billing|finance",
    "hr": r"\bhr\b|hrms|human resource|payroll|attendance|employee",
    "lms": r"\blms\b|learning management|course|e-?learning|student|school",
    "marketing-automation": r"marketing|newsletter|email campaign|mailing",
    "workflow-automation": r"workflow|automation|no-?code|low-?code|integration",
    "ai-chatbot": r"chatbot|knowledge base|\brag\b|assistant|customer service|chat",
    "analytics-bi": r"analytics|dashboard|business intelligence|\bbi\b|report",
    "forms-survey": r"form|survey|questionnaire",
    "project-management": r"project management|kanban|task|issue track",
    "document-signing": r"sign|signature|docusign",
    "website-cms": r"\bcms\b|content management|website builder|headless",
    "healthcare": r"health|clinic|patient|medical|\behr\b|emr|hospital",
    "restaurant": r"restaurant|food|menu|ordering",
    "property": r"hotel|property|rental|hospitality|real estate",
}
SME_WORDS = re.compile(r"business|customer|team|compan|small|sme|shop|store|clinic|school|hotel|restaurant|crm|erp|invoice|booking|appointment|helpdesk|ticket|support|inventory|self-?host|alternative to|open[- ]source alternative", re.I)
DEV_WORDS = re.compile(r"\b(cli|sdk|library|framework for developers|developer tool|devtool|codebase|coding agent|claude code|vector database|database|llm inference|terminal|kubernetes|compiler|crawler|scraper|benchmark|research|paper|model training|fine-?tun|repository|prompt|mcp server|memory for|context|api gateway|observability|monitoring|framework|toolkit|orchestration|agent engineering)\b", re.I)


def pick_category(r):
    blob = (r["full_name"] + " " + (r["description"] or "") + " " + " ".join(r.get("topics", []))).lower()
    def key(c):
        hits = len(re.findall(CAT_WORDS.get(c, "$^"), blob))
        return (hits, KB.get(c, DEFAULT)["demand"])
    return sorted(r["categories"], key=key, reverse=True)[0]


def sme_fit(r):
    blob = (r["description"] or "") + " " + " ".join(r.get("topics", []))
    pos = min(8, 3 * len(set(m.lower() for m in SME_WORDS.findall(blob))))
    neg = min(12, 6 * len(set(m.lower() for m in DEV_WORDS.findall(blob))))
    return pos, neg


def score(r, lic, cat, prev_stars):
    kb = KB.get(cat, DEFAULT)
    paths = r.get("paths_sample", [])
    low = [p.lower() for p in paths]
    has_compose = any(re.search(r"(^|/)(docker-)?compose[^/]*\.ya?ml$", p) for p in low)
    has_docker = has_compose or any(p.endswith("dockerfile") for p in low)
    has_helm = any(p.endswith("chart.yaml") for p in low)
    has_vi = bool(r.get("readme_vi"))

    # 1. License (0-30)
    s_lic = lic["safe"]
    if lic["enterprise"]:
        s_lic = max(0, s_lic - 4)

    # 2. Hoạt động (0-15)
    push = days_since(r["pushed_at"])
    s_act = 15 if push <= 14 else 12 if push <= 30 else 8 if push <= 90 else 4 if push <= 180 else 0
    rel = None

    # 3. Sức hút (0-15): quy mô sao + tốc độ
    age = max(30, days_since(r["created_at"]))
    per_day = r["stars"] / age
    s_trac = min(10, (math.log10(max(100, r["stars"])) - 2) * 3.4)  # 1k->3.4, 10k->6.8, 100k->10
    s_trac += min(5, per_day)
    weekly_delta = None
    if prev_stars is not None:
        weekly_delta = r["stars"] - prev_stars

    # 4. Dễ tự host (0-15)
    s_host = (7 if has_compose else 4 if has_docker else 0) + (2 if has_helm else 0)
    lang = (r.get("language") or "").lower()
    s_host += 6 if lang in {"typescript", "javascript", "python", "php", "go"} else 4 if lang in {"ruby", "java", "c#", "kotlin", "rust", "elixir", "dart", "vue"} else 2
    s_host = min(15, s_host)

    # 5. Phù hợp VN (0-25)
    pos, neg = sme_fit(r)
    s_vn = kb["demand"] * 2 + (6 - kb["competition"]) + pos - neg  # ngành (tối đa 15) + mô tả hướng doanh nghiệp (8) - công cụ dev
    if pos == 0:
        s_vn -= 5
    if has_vi:
        s_vn += 2
    s_vn = max(0, min(25, s_vn))

    total = s_lic + s_act + s_trac + s_host + s_vn
    if lic["group"] in ("restricted", "none"):
        total = min(total, 25)  # bị loại, đẩy xuống cuối
    return dict(total=round(total), license=round(s_lic), activity=s_act, traction=round(s_trac, 1),
                selfhost=s_host, vnfit=s_vn), dict(compose=has_compose, docker=has_docker, helm=has_helm, vi=has_vi,
                                                    push_days=push, release_days=rel, stars_per_day=round(per_day, 2),
                                                    weekly_delta=weekly_delta)


def improvements(r, lic, cat, tech):
    kb = KB.get(cat, DEFAULT)
    out = []
    if not tech["vi"]:
        out.append("Việt hóa giao diện (README không nhắc tiếng Việt — kiểm tra thư mục ngôn ngữ)")
    else:
        out.append("README có nhắc tiếng Việt — kiểm tra mức độ dịch, rà thuật ngữ theo ngành")
    out += kb["integrations"]
    out.append("Thanh toán gói dịch vụ bằng VietQR / chuyển khoản, xuất hóa đơn điện tử cho khách")
    if not tech["docker"]:
        out.append("Tự viết Docker/compose để triển khai nhanh cho từng khách")
    if lic["group"] == "agpl":
        out.append("Tách phần tích hợp VN thành service riêng gọi qua API (giữ bản quyền phần của bạn)")
    if lic["enterprise"]:
        out.append(f"Không dùng code trong thư mục {', '.join(lic['enterprise'])} (bản thương mại riêng)")
    return out


def risks(r, lic, cat, tech):
    kb = KB.get(cat, DEFAULT)
    out = []
    if lic["group"] in ("restricted", "none"):
        out.append("License không cho phép bán dịch vụ — loại")
    if lic["group"] == "single-tenant":
        out.append("Điều khoản cấm multi-tenant: chi phí server cao hơn vì mỗi khách một instance")
    if lic["group"] == "unknown":
        out.append("License tùy biến chưa phân loại — phải đọc tay")
    if lic["enterprise"]:
        out.append("Mô hình open-core: một số tính năng nằm trong bản trả phí")
    if kb["data_risk"] in ("cao", "rất cao"):
        out.append(f"Rủi ro dữ liệu {kb['data_risk']}: cần hợp đồng xử lý dữ liệu, mã hóa, lưu tại VN (Luật 91/2025/QH15)")
    if tech["push_days"] > 180:
        out.append(f"Ít cập nhật ({tech['push_days']} ngày chưa có commit)")
    if kb["competition"] >= 5:
        out.append(f"Cạnh tranh nội địa mạnh ({kb['competitors']}) — chỉ đánh ngách")
    return out


def playbook(cat):
    kb = KB.get(cat, DEFAULT)
    n = kb["niches"][0]
    return [
        f"Tuần 1–2: phỏng vấn 10 khách thuộc nhóm '{kb['customers'][0]}' — hỏi đang dùng gì, mất thời gian ở đâu, sẵn sàng trả bao nhiêu.",
        f"Tuần 3–6: dựng demo cho ngách '{n}', chỉ làm 1–2 tích hợp khách nhắc nhiều nhất.",
        f"Tuần 7–12: chốt 3–5 khách trả tiền qua kênh: {kb['channels'][0].split(':')[0]}. Không ai trả → đổi ngách trước khi đổi sản phẩm.",
    ]


def auto_strengths(r):
    t, out = r["tech"], []
    if r["stars"] >= 20000:
        out.append(f"Cộng đồng rất lớn ({r['stars']:,} sao) — dễ tìm tài liệu, plugin, người hỗ trợ".replace(",", "."))
    elif r["stars"] >= 5000:
        out.append(f"Cộng đồng khá lớn ({r['stars']:,} sao)".replace(",", "."))
    if t["push_days"] <= 14:
        out.append("Đang được phát triển tích cực (có commit trong 2 tuần qua)")
    if t["compose"]:
        out.append("Có sẵn Docker Compose — dựng bản demo cho khách trong vài giờ")
    if r["license_group"] == "permissive":
        out.append("License dễ dãi — host nhiều khách trên một hệ thống, giữ riêng phần sửa")
    if t.get("weekly_delta"):
        if t["weekly_delta"] >= 300:
            out.append(f"Tăng {t['weekly_delta']} sao trong tuần qua — đang là xu hướng")
    elif t["stars_per_day"] >= 20:
        out.append(f"Tăng sao rất nhanh (~{round(t['stars_per_day'])} sao/ngày) — đang là xu hướng")
    if t["vi"]:
        out.append("README có nhắc tiếng Việt")
    return out[:4]


def classify_all(raw_repos, prev_stars=None):
    """raw_repos: danh sách từ Scanner.run(); prev_stars: {full_name_lower: stars} của lần quét trước."""
    from curated import CURATED
    prev = prev_stars or {}
    out = []
    for r in raw_repos:
        desc = r["description"] or ""
        if NOT_APP.search(r["full_name"]) or NOT_APP.search(desc[:160]):
            if not any(p.lower().endswith(("docker-compose.yml", "compose.yaml", "docker-compose.yaml")) for p in r.get("paths_sample", [])):
                continue
        lic = classify_license(r)
        cat = pick_category(r)
        sc, tech = score(r, lic, cat, prev.get(r["full_name"].lower()))
        rec = dict(
            name=r["full_name"], url=r["url"], description=desc, homepage=r["homepage"],
            stars=r["stars"], forks=r["forks"], language=r["language"], topics=r["topics"][:8],
            created=r["created_at"][:10], pushed=r["pushed_at"][:10], pushed_at=r["pushed_at"],
            rising="rising" in r["tags"],
            category=cat, category_label=CATEGORY_LABEL.get(cat, cat),
            license=lic["label"], license_group=lic["group"], license_flags=lic["flags"],
            license_url=r["url"] + "/blob/HEAD/" + (r.get("license_path") or "LICENSE"),
            deploy_model=lic["model"], deploy_detail=lic["model_detail"], enterprise_dirs=lic["enterprise"],
            score=sc, tech=tech,
            improvements=improvements(r, lic, cat, tech), risks=risks(r, lic, cat, tech),
        )
        c = CURATED.get(r["full_name"].lower())
        if c:
            rec.update(features=c["f"], strengths=c["s"], feat_src="curated", niche_hint="")
        else:
            fr = r.get("features_raw") or []
            rec.update(features=fr[:10], strengths=[], feat_src="readme" if fr else "none", niche_hint="")
        rec["auto_strengths"] = auto_strengths(rec)
        out.append(rec)
    out.sort(key=lambda x: x["score"]["total"], reverse=True)
    return out


def kb_for(repos):
    return {r["category"]: dict(KB.get(r["category"], DEFAULT), playbook=playbook(r["category"])) for r in repos}


SUMMARY_GROUPS = ["permissive", "gpl", "agpl", "single-tenant", "unknown", "restricted", "none"]
