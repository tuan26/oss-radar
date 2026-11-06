# -*- coding: utf-8 -*-
"""Bộ kiểm thử bắt buộc REQUIREMENTS §5.2 — dùng file LICENSE thật của 10 repo (tests/fixtures)."""
import json
from pathlib import Path

import pytest

from app.classify import classify_license, classify_all, effective_spdx, score

FIX = json.loads((Path(__file__).parent / "fixtures" / "licenses.json").read_text(encoding="utf-8"))

EXPECTED = {
    "n8n-io/n8n": ("restricted", False),
    "nocodb/nocodb": ("restricted", False),
    "akaunting/akaunting": ("restricted", False),
    "invoiceninja/invoiceninja": ("restricted", False),
    "langgenius/dify": ("single-tenant", False),
    "chatwoot/chatwoot": ("permissive", True),
    "twentyhq/twenty": ("agpl", None),        # bảng yêu cầu chỉ ghi agpl; LICENSE có Enterprise Edition
    "odoo/odoo": ("permissive", False),       # LGPL
    "frappe/erpnext": ("gpl", False),
    "documenso/documenso": ("agpl", True),
}


@pytest.mark.parametrize("repo", sorted(EXPECTED))
@pytest.mark.parametrize("label", ["github", "NOASSERTION"])
def test_ten_repos(repo, label):
    r = dict(FIX[repo])
    if label == "NOASSERTION":
        r["spdx"] = "NOASSERTION"
    group, ent = EXPECTED[repo]
    res = classify_license(r)
    assert res["group"] == group, (repo, res)
    if ent is not None:
        assert bool(res["enterprise"]) == ent, (repo, res["enterprise"])


def test_odoo_is_lgpl_read_from_file():
    res = classify_license(FIX["odoo/odoo"])
    assert res["label"] == "LGPL-3.0 (đọc từ file)"


def test_erpnext_text_is_gpl_not_agpl():
    sp, inferred = effective_spdx("NOASSERTION", FIX["frappe/erpnext"]["license_text"].lower())
    assert (sp, inferred) == ("GPL-3.0", True)


def test_noassertion_agpl_label():
    res = classify_license(FIX["twentyhq/twenty"])
    assert res["label"] == "AGPL-3.0 (đọc từ file)"


def test_gpl2_detected():
    text = "GNU GENERAL PUBLIC LICENSE\nVersion 2, June 1991\n..."
    assert effective_spdx("NOASSERTION", text.lower()) == ("GPL-2.0", True)


def test_open_core_minus_4():
    raw = _raw(FIX["chatwoot/chatwoot"])
    lic = classify_license(raw)
    sc, _ = score(raw, lic, "helpdesk", None)
    assert sc["license"] == 30 - 4
    assert "chỉ dùng phần lõi" in lic["model_detail"]


def test_generic_non_commercial_not_restricted():
    text = ("Permission is hereby granted, free of charge, to any person obtaining a copy... "
            "This software can be used for commercial and non-commercial projects.")
    res = classify_license({"spdx": "NOASSERTION", "license_text": text, "paths_sample": []})
    assert res["group"] == "permissive"


def test_explicit_non_commercial_restricted():
    text = "You may not use the software for commercial purposes."
    res = classify_license({"spdx": "NOASSERTION", "license_text": text, "paths_sample": []})
    assert res["group"] == "restricted"


def test_no_license():
    res = classify_license({"spdx": "NONE", "license_text": "", "paths_sample": []})
    assert res["group"] == "none"


def test_unknown_custom():
    res = classify_license({"spdx": "NOASSERTION", "license_text": "Custom terms by ACME.", "paths_sample": []})
    assert res["group"] == "unknown"


def _raw(fix, **kw):
    r = dict(full_name="x/y", url="https://github.com/x/y", description="Open-source CRM for small business",
             homepage="", stars=5000, forks=10, open_issues=1, language="Python", topics=["crm"],
             created_at="2024-01-01T00:00:00Z", pushed_at="2026-11-01T00:00:00Z",
             categories=["crm"], tags=["top"], readme_vi=False, features_raw=["Quản lý lead và cơ hội"])
    r.update(fix)
    r.update(kw)
    return r


def test_restricted_capped_25():
    out = classify_all([_raw(FIX["n8n-io/n8n"], full_name="n8n-io/n8n", stars=150000)])
    assert out[0]["license_group"] == "restricted"
    assert out[0]["score"]["total"] <= 25


def test_license_link_and_curated():
    out = classify_all([_raw(FIX["chatwoot/chatwoot"], full_name="chatwoot/chatwoot",
                             url="https://github.com/chatwoot/chatwoot")])
    r = out[0]
    assert r["license_url"] == "https://github.com/chatwoot/chatwoot/blob/HEAD/LICENSE"
    assert r["feat_src"] == "curated"


def test_weekly_delta_and_new_flag():
    a = _raw(FIX["chatwoot/chatwoot"], full_name="a/a", stars=5000)
    b = _raw(FIX["chatwoot/chatwoot"], full_name="b/b", stars=3000)
    out = {r["name"]: r for r in classify_all([a, b], prev_stars={"a/a": 4000}, prev_days=7)}
    assert out["a/a"]["tech"]["weekly_delta"] == 1000
    assert out["a/a"]["is_new"] is False
    assert out["b/b"]["is_new"] is True
    first = classify_all([a])[0]
    assert first["is_new"] is False and first["tech"]["weekly_delta"] is None


def test_auto_strengths_keeps_commas():
    r = classify_all([_raw(FIX["chatwoot/chatwoot"], full_name="a/a", stars=37402)])[0]
    s = r["auto_strengths"][0]
    assert "37.402" in s and "tài liệu, plugin, người hỗ trợ" in s
