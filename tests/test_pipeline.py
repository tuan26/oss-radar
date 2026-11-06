# -*- coding: utf-8 -*-
"""Quét end-to-end với GitHub/AI/Telegram giả lập."""
import time

import pytest

from app import jobs, store
from app.scanner import CATEGORIES
from fakes import FakeAI, FakeGitHub, make_repo


@pytest.fixture
def gh(monkeypatch):
    repos = [make_repo("acme/crm", 5000), make_repo("acme/helpdesk", 3000, desc="Helpdesk ticket system for support teams"),
             make_repo("n8n-io/n8n", 150000, "n8n-io/n8n", desc="Workflow automation platform"),
             make_repo("chatwoot/chatwoot", 25000, "chatwoot/chatwoot", desc="Customer support live chat")]
    g = FakeGitHub(repos)
    monkeypatch.setenv("GITHUB_API_URL", g.api)
    monkeypatch.setenv("GITHUB_RAW_URL", g.raw)
    yield g
    g.close()


def _settings(**ai):
    s = store.load_settings()
    s["github"]["categories"] = ["crm", "helpdesk"]
    s["ai"].update(ai)
    store.save_settings(s)


def _fast_factory(settings, progress, stop_event):
    sc = jobs.ScanManager._default_scanner(settings, progress, stop_event)
    sc.search_gap = 0
    return sc


def run_scan(mgr, trigger="manual"):
    assert mgr.start(trigger)
    assert mgr.wait(30)
    return store.last_run()


def test_scan_without_ai_and_token(gh):
    _settings()
    mgr = jobs.ScanManager(scanner_factory=_fast_factory)
    rec = run_scan(mgr)
    assert rec["status"] == "ok", rec
    res = store.load_results()
    names = {r["name"]: r for r in res["repos"]}
    assert set(names) == {"acme/crm", "acme/helpdesk", "n8n-io/n8n", "chatwoot/chatwoot"}
    assert names["n8n-io/n8n"]["license_group"] == "restricted"
    assert names["chatwoot/chatwoot"]["feat_src"] == "curated"
    assert names["acme/crm"]["feat_src"] == "readme" and names["acme/crm"]["features"]
    assert names["acme/crm"]["tech"]["compose"] is True
    assert res["summary"]["restricted"] == 1
    assert "crm" in res["kb"] and res["kb"]["crm"]["playbook"]
    assert gh.search_calls == 2 * (len(CATEGORIES["crm"]) + len(CATEGORIES["helpdesk"]))
    assert rec["repos"] == 4 and rec["ai_calls"] == 0


def test_only_one_scan_at_a_time(gh):
    _settings()
    gh.delay = 0.05
    mgr = jobs.ScanManager(scanner_factory=_fast_factory)
    assert mgr.start() is True
    assert mgr.start() is False
    assert mgr.status()["running"]
    mgr.wait(30)


def test_stop_keeps_old_data(gh):
    _settings()
    store.save_results({"scanned_at": "old", "repos": [{"name": "old/repo"}]})
    gh.delay = 0.3

    def slow_factory(settings, progress, stop_event):
        sc = _fast_factory(settings, progress, stop_event)
        sc.search_gap = 6.5   # như khi không có token
        return sc
    mgr = jobs.ScanManager(scanner_factory=slow_factory)
    mgr.start()
    time.sleep(1)
    t0 = time.time()
    assert mgr.stop()
    assert mgr.wait(15)
    assert time.time() - t0 < 10
    assert store.load_results()["scanned_at"] == "old"
    assert store.last_run()["status"] == "stopped"


def test_github_bad_token(gh):
    _settings()
    gh.status = 401
    mgr = jobs.ScanManager(scanner_factory=_fast_factory)
    rec = run_scan(mgr)
    assert rec["status"] == "error" and "token không hợp lệ" in rec["error"]


def test_ai_second_scan_uses_cache_and_history(gh, monkeypatch):
    ai_srv = FakeAI()
    sent = []
    try:
        _settings(provider="openai", kind="openai", base_url=ai_srv.url + "/v1", model="fake-model",
                  api_key=ai_srv.key)
        s = store.load_settings()
        s["telegram"].update(bot_token="123:abc", chat_id="42", min_score=0)
        store.save_settings(s)
        mgr = jobs.ScanManager(scanner_factory=_fast_factory, notifier=lambda t, c, m: sent.append(m))
        rec1 = run_scan(mgr)
        assert rec1["status"] == "ok"
        # 2 repo an toàn chưa có tóm tắt tay: acme/crm, acme/helpdesk (n8n bị loại, chatwoot có tóm tắt tay)
        assert rec1["ai_calls"] == 2 and ai_srv.calls == 2 and rec1["ai_summarized"] == 2
        r = {x["name"]: x for x in store.load_results()["repos"]}
        assert r["acme/crm"]["feat_src"] == "ai" and r["acme/crm"]["ai_model"] == "fake-model"
        assert r["acme/crm"]["niche_hint"]
        assert r["n8n-io/n8n"]["feat_src"] != "ai"

        # Lần 2 (giả lập là tuần sau): không gọi lại AI; có sao tăng + repo mới
        import datetime as dt
        snap = store._hist_dir()
        for p in snap.iterdir():
            p.rename(snap / "2026-01-01.json")
        gh.repos["acme/crm"]["item"]["stargazers_count"] = 5600
        gh.repos["new/app"] = __import__("fakes").make_repo("new/app", 4000, desc="Booking system for small business clinics", topics=("crm",))
        rec2 = run_scan(mgr)
        assert rec2["status"] == "ok" and rec2["ai_calls"] == 1 and ai_srv.calls == 3   # chỉ repo mới
        res = store.load_results()
        r = {x["name"]: x for x in res["repos"]}
        assert r["acme/crm"]["tech"]["weekly_delta"] == 600 and r["acme/crm"]["feat_src"] == "ai"
        assert r["new/app"]["is_new"] is True and r["acme/crm"]["is_new"] is False
        assert len(sent) == 2 and "new/app" in sent[1]
    finally:
        ai_srv.close()


def test_ai_wrong_key_keeps_scan(gh):
    ai_srv = FakeAI()
    try:
        _settings(provider="openai", kind="openai", base_url=ai_srv.url + "/v1", model="m", api_key="wrong")
        mgr = jobs.ScanManager(scanner_factory=_fast_factory)
        rec = run_scan(mgr)
        assert rec["status"] == "ok" and rec["repos"] == 4
        assert "API key sai" in rec["ai_error"]
    finally:
        ai_srv.close()


def test_error_notification(gh):
    _settings()
    gh.status = 401
    s = store.load_settings()
    s["telegram"].update(bot_token="123:abc", chat_id="42")
    store.save_settings(s)
    sent = []
    mgr = jobs.ScanManager(scanner_factory=_fast_factory, notifier=lambda t, c, m: sent.append(m))
    run_scan(mgr)
    assert len(sent) == 1 and "quét lỗi" in sent[0]
