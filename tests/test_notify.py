# -*- coding: utf-8 -*-
import pytest

from app import notify


def _r(name, group="permissive", score=80, new=False, delta=None):
    return {"name": name, "url": f"https://github.com/{name}", "license_group": group, "score": {"total": score},
            "is_new": new, "tech": {"weekly_delta": delta}, "category_label": "CRM"}


def test_highlights_filters_and_limits():
    repos = [_r("a/new1", new=True), _r("a/grow", delta=500), _r("a/low", score=60, new=True),
             _r("a/bad", group="restricted", new=True), _r("a/flat", delta=0),
             _r("a/new2", new=True, score=90), _r("a/g2", delta=50), _r("a/g3", delta=40), _r("a/g4", delta=30)]
    hl = [r["name"] for r in notify.highlights(repos, 75)]
    assert len(hl) == 5
    assert "a/low" not in hl and "a/bad" not in hl and "a/flat" not in hl
    assert hl[:2] == ["a/new2", "a/grow"]


def test_scan_message_content():
    res = {"repos": [_r("a/new1", new=True), _r("b/x", group="agpl")],
           "summary": {"permissive": 1, "agpl": 1}, "has_history": True}
    msg = notify.scan_message(res, {"duration_s": 120, "ai_summarized": 3}, "https://radar.example", 75)
    assert "2 repo" in msg and "SaaS thoải mái: 1" in msg and "AGPL: 1" in msg
    assert "a/new1" in msg and "mới" in msg and "https://radar.example" in msg and "AI tóm tắt: 3" in msg


def test_send_error_does_not_leak_token(monkeypatch):
    with pytest.raises(notify.NotifyError) as e:
        notify.send("123:SECRET", "1", "hi", api="http://127.0.0.1:9")
    assert "SECRET" not in str(e.value)


def test_send_requires_config():
    with pytest.raises(notify.NotifyError):
        notify.send("", "", "hi")
