# -*- coding: utf-8 -*-
import base64
import json
import logging

import pytest
from fastapi.testclient import TestClient

from app import store
from app.main import create_app
from fakes import FakeAI

SECRETS = {"ai": {"api_key": "sk-TOPSECRET-aaaa1111"}, "github": {"token": "ghp_TOPSECRETbbbb2222"},
           "telegram": {"bot_token": "999:TOPSECRETcccc3333", "chat_id": "1"}}


@pytest.fixture
def client():
    with TestClient(create_app(start_scheduler=False)) as c:
        yield c


def test_settings_roundtrip_hides_secrets(client):
    r = client.post("/api/settings", json=SECRETS)
    assert r.status_code == 200
    assert "TOPSECRET" not in r.text
    g = client.get("/api/settings").json()
    assert g["ai"]["api_key_set"] and g["ai"]["api_key_last4"] == "1111"
    assert g["github"]["token_last4"] == "2222" and g["telegram"]["bot_token_last4"] == "3333"
    assert "gemini" in g["presets"] and "crm" in g["categories"]
    # gửi lại không có key → giữ nguyên
    client.post("/api/settings", json={"ai": {"model": "x"}})
    assert store.load_settings()["ai"]["api_key"] == "sk-TOPSECRET-aaaa1111"
    for path in ["/api/settings", "/api/status", "/api/data"]:
        assert "TOPSECRET" not in client.get(path).text


def test_settings_validation_error_vietnamese(client):
    r = client.post("/api/settings", json={"schedule": {"timezone": "Sai/Mui"}})
    assert r.status_code == 400 and "Múi giờ" in r.json()["detail"]


def test_settings_next_run(client):
    r = client.post("/api/settings", json={"schedule": {"enabled": True, "day_of_week": "mon", "hour": 7, "minute": 0}}).json()
    assert r["next_run"] and "T07:00:00+07:00" in r["next_run"]
    assert r["schedule_text"].startswith("Thứ Hai 07:00")


def test_basic_auth(monkeypatch, client):
    monkeypatch.setenv("APP_PASSWORD", "matkhau")
    assert client.get("/").status_code == 401
    assert client.get("/api/data").status_code == 401
    bad = base64.b64encode(b"admin:sai").decode()
    assert client.get("/api/data", headers={"Authorization": "Basic " + bad}).status_code == 401
    ok = base64.b64encode(b"admin:matkhau").decode()
    assert client.get("/api/data", headers={"Authorization": "Basic " + ok}).status_code == 200
    assert client.get("/", headers={"Authorization": "Basic " + ok}).status_code == 200


def test_empty_data_and_sample(client):
    d = client.get("/api/data").json()
    assert d["repos"] == [] and d["scanned_at"] is None
    r = client.post("/api/sample").json()
    assert r["loaded"] == 474
    d = client.get("/api/data", headers={"Accept-Encoding": "gzip"})
    assert d.headers.get("content-encoding") == "gzip" and len(d.json()["repos"]) == 474
    assert client.post("/api/sample").status_code == 409


def test_ai_test_endpoint(client):
    srv = FakeAI()
    try:
        ok = client.post("/api/ai/test", json={"provider": "custom", "kind": "openai", "base_url": srv.url + "/v1",
                                               "model": "m", "api_key": srv.key}).json()
        assert ok["ok"] is True
        bad = client.post("/api/ai/test", json={"provider": "custom", "kind": "openai", "base_url": srv.url + "/v1",
                                                "model": "m", "api_key": "sai"}).json()
        assert bad["ok"] is False and "API key sai" in bad["error"]
        # dùng key đã lưu khi không gửi key
        client.post("/api/settings", json={"ai": {"provider": "custom", "kind": "openai", "base_url": srv.url + "/v1",
                                                  "model": "m", "api_key": srv.key}})
        assert client.post("/api/ai/test", json={}).json()["ok"] is True
        none = client.post("/api/ai/test", json={"provider": "none"}).json()
        assert none["ok"] is False and "Không dùng AI" in none["error"]
    finally:
        srv.close()


def test_clear_cache(client):
    store.save_ai_cache({"a:1": {}, "b:2": {}})
    assert client.post("/api/ai/clear-cache").json() == {"cleared": 2}
    assert store.load_ai_cache() == {}


def test_status_estimate(client):
    client.post("/api/sample")
    client.post("/api/settings", json={"ai": {"provider": "gemini", "max_repos": 10}})
    st = client.get("/api/status").json()
    assert st["ai_estimate"]["enabled"] and st["ai_estimate"]["candidates"] == 10
    assert st["running"] is False and st["has_data"] is True


def test_log_redaction(client, caplog):
    client.post("/api/settings", json=SECRETS)
    from app.main import RedactSecrets
    rec = logging.LogRecord("x", logging.INFO, __file__, 1, "key=%s", ("sk-TOPSECRET-aaaa1111",), None)
    RedactSecrets().filter(rec)
    assert "TOPSECRET" not in rec.getMessage()


def test_notify_test_endpoint_error(client):
    r = client.post("/api/notify/test", json={}).json()
    assert r["ok"] is False and "Chưa nhập" in r["error"]
