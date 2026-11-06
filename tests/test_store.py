# -*- coding: utf-8 -*-
import datetime as dt
import json
import os

import pytest

from app import store


def test_defaults():
    s = store.load_settings()
    assert s["ai"]["provider"] == "none"
    assert s["ai"]["max_repos"] == 60 and s["ai"]["workers"] == 3
    assert s["schedule"]["timezone"] == "Asia/Ho_Chi_Minh"
    assert s["github"]["min_stars"] == 800
    assert s["telegram"]["min_score"] == 75


def test_atomic_write_keeps_old_file_on_failure(data_dir, monkeypatch):
    store.save_results({"repos": [1]})
    real_dump = json.dump

    def boom(*a, **k):
        raise KeyboardInterrupt  # mô phỏng tắt ngang giữa lúc ghi
    monkeypatch.setattr(json, "dump", boom)
    with pytest.raises(KeyboardInterrupt):
        store.save_results({"repos": [2]})
    monkeypatch.setattr(json, "dump", real_dump)
    assert store.load_results() == {"repos": [1]}
    assert not [p for p in os.listdir(data_dir) if p.endswith(".tmp")]


def test_mask_never_contains_secret():
    s = store.load_settings()
    s["ai"]["api_key"] = "sk-SECRET-abcdef1234"
    s["github"]["token"] = "ghp_SECRETTOKEN9876"
    s["telegram"]["bot_token"] = "123:TELEGRAMSECRETzz"
    m = store.mask_settings(s)
    dump = json.dumps(m)
    assert "SECRET" not in dump
    assert m["ai"]["api_key_last4"] == "1234" and m["ai"]["api_key_set"] is True
    assert m["github"]["token_last4"] == "9876"


def test_secret_kept_when_not_sent_and_cleared_on_request():
    s = store.load_settings()
    s = store.apply_update(s, {"ai": {"api_key": "sk-abc-12345678"}})
    s = store.apply_update(s, {"ai": {"model": "gpt-x"}})
    assert s["ai"]["api_key"] == "sk-abc-12345678"
    s = store.apply_update(s, {"ai": {"api_key": ""}})
    assert s["ai"]["api_key"] == "sk-abc-12345678"
    s = store.apply_update(s, {"ai": {"clear_api_key": True}})
    assert s["ai"]["api_key"] == ""


@pytest.mark.parametrize("upd", [
    {"schedule": {"timezone": "Mars/Olympus"}},
    {"schedule": {"hour": 24}},
    {"schedule": {"day_of_week": "xyz"}},
    {"ai": {"workers": 0}},
    {"ai": {"kind": "gemini"}},
])
def test_invalid_settings(upd):
    with pytest.raises(store.SettingsError):
        store.apply_update(store.load_settings(), upd)


def test_previous_snapshot():
    store.save_snapshot(dt.date(2026, 10, 26), {"a/a": 1})
    store.save_snapshot(dt.date(2026, 11, 2), {"a/a": 2})
    store.save_snapshot(dt.date(2026, 11, 9), {"a/a": 3})
    d, snap = store.previous_snapshot(dt.date(2026, 11, 9))
    assert d == dt.date(2026, 11, 2) and snap == {"a/a": 2}
    assert store.previous_snapshot(dt.date(2026, 10, 26)) == (None, None)


def test_runs_capped():
    for i in range(60):
        store.add_run({"i": i})
    runs = store.load_runs()
    assert len(runs) == 50 and runs[-1]["i"] == 59 and store.last_run()["i"] == 59
