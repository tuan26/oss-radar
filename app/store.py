# -*- coding: utf-8 -*-
"""Đọc/ghi dữ liệu trong DATA_DIR: settings, kết quả, lịch sử lần chạy, cache AI, ảnh chụp sao.
Mọi lần ghi đều qua file tạm rồi os.replace để không hỏng dữ liệu khi tắt ngang."""
import copy
import datetime as dt
import json
import os
import re
import tempfile
import threading
from pathlib import Path

from . import config

_lock = threading.RLock()

SECRET_FIELDS = [("ai", "api_key"), ("github", "token"), ("telegram", "bot_token")]

DEFAULT_SETTINGS = {
    "ai": {"provider": "none", "kind": "openai", "base_url": "", "model": "", "api_key": "",
           "max_repos": 60, "workers": 3},
    "schedule": {"enabled": False, "day_of_week": "mon", "hour": 7, "minute": 0,
                 "timezone": "Asia/Ho_Chi_Minh"},
    "github": {"token": "", "min_stars": 800, "categories": []},
    "telegram": {"bot_token": "", "chat_id": "", "min_score": 75},
}
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class SettingsError(ValueError):
    pass


def _path(name) -> Path:
    return config.data_dir() / name


def write_json(path: Path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise


def read_json(path: Path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return copy.deepcopy(default)


# ---------- settings ----------
def _merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _merge(out[k], v)
        elif k in out:
            out[k] = v
    return out


def load_settings() -> dict:
    with _lock:
        return _merge(DEFAULT_SETTINGS, read_json(_path("settings.json"), {}))


def save_settings(s: dict) -> None:
    write_json(_path("settings.json"), s)


def secrets_of(s: dict) -> list:
    return [s[g][f] for g, f in SECRET_FIELDS if s.get(g, {}).get(f)]


def mask_settings(s: dict) -> dict:
    out = copy.deepcopy(s)
    for g, f in SECRET_FIELDS:
        val = out[g].pop(f, "") or ""
        out[g][f + "_set"] = bool(val)
        out[g][f + "_last4"] = val[-4:] if len(val) >= 8 else ("****" if val else "")
    return out


def _int(v, lo, hi, label):
    try:
        n = int(v)
    except (TypeError, ValueError):
        raise SettingsError(f"{label} phải là số")
    if not lo <= n <= hi:
        raise SettingsError(f"{label} phải từ {lo} đến {hi}")
    return n


def validate_timezone(tz: str) -> str:
    from zoneinfo import ZoneInfo
    try:
        ZoneInfo(tz)
    except Exception:
        raise SettingsError(f"Múi giờ '{tz}' không hợp lệ (ví dụ đúng: Asia/Ho_Chi_Minh)")
    return tz


def apply_update(current: dict, upd: dict, presets=None, categories=None) -> dict:
    """Gộp cập nhật từ giao diện vào settings hiện tại. Trường bí mật rỗng/không gửi = giữ nguyên."""
    s = copy.deepcopy(current)
    upd = upd or {}
    for g, f in SECRET_FIELDS:
        part = upd.get(g) or {}
        if part.get("clear_" + f):
            s[g][f] = ""
        elif isinstance(part.get(f), str) and part[f].strip():
            s[g][f] = part[f].strip()

    ai = upd.get("ai") or {}
    if "provider" in ai:
        if ai["provider"] != "none" and presets is not None and ai["provider"] not in presets:
            raise SettingsError("Nhà cung cấp AI không hợp lệ")
        s["ai"]["provider"] = ai["provider"]
    if "kind" in ai:
        if ai["kind"] not in ("openai", "anthropic"):
            raise SettingsError("Loại API phải là 'openai' hoặc 'anthropic'")
        s["ai"]["kind"] = ai["kind"]
    for k in ("base_url", "model"):
        if k in ai:
            s["ai"][k] = str(ai[k] or "").strip()
    if "max_repos" in ai:
        s["ai"]["max_repos"] = _int(ai["max_repos"], 0, 500, "Số repo tối đa gọi AI")
    if "workers" in ai:
        s["ai"]["workers"] = _int(ai["workers"], 1, 8, "Số luồng AI")

    sc = upd.get("schedule") or {}
    if "enabled" in sc:
        s["schedule"]["enabled"] = bool(sc["enabled"])
    if "day_of_week" in sc:
        if sc["day_of_week"] not in DAYS:
            raise SettingsError("Ngày trong tuần không hợp lệ")
        s["schedule"]["day_of_week"] = sc["day_of_week"]
    if "hour" in sc:
        s["schedule"]["hour"] = _int(sc["hour"], 0, 23, "Giờ")
    if "minute" in sc:
        s["schedule"]["minute"] = _int(sc["minute"], 0, 59, "Phút")
    if "timezone" in sc:
        s["schedule"]["timezone"] = validate_timezone(str(sc["timezone"]).strip())

    gh = upd.get("github") or {}
    if "min_stars" in gh:
        s["github"]["min_stars"] = _int(gh["min_stars"], 0, 1_000_000, "Số sao tối thiểu")
    if "categories" in gh:
        cats = [c for c in (gh["categories"] or []) if isinstance(c, str)]
        if categories is not None and any(c not in categories for c in cats):
            raise SettingsError("Có ngành không hợp lệ")
        s["github"]["categories"] = cats

    tg = upd.get("telegram") or {}
    if "chat_id" in tg:
        s["telegram"]["chat_id"] = str(tg["chat_id"] or "").strip()
    if "min_score" in tg:
        s["telegram"]["min_score"] = _int(tg["min_score"], 0, 100, "Ngưỡng điểm")
    return s


# ---------- kết quả ----------
def load_results():
    return read_json(_path("results.json"), None)


def save_results(data: dict) -> None:
    write_json(_path("results.json"), data)


# ---------- lịch sử lần chạy ----------
def load_runs() -> list:
    return read_json(_path("runs.json"), [])


def add_run(rec: dict, keep=50) -> None:
    with _lock:
        runs = load_runs()
        runs.append(rec)
        write_json(_path("runs.json"), runs[-keep:])


def last_run():
    runs = load_runs()
    return runs[-1] if runs else None


# ---------- cache AI ----------
def load_ai_cache() -> dict:
    return read_json(_path("ai_cache.json"), {})


def save_ai_cache(cache: dict) -> None:
    write_json(_path("ai_cache.json"), cache)


def clear_ai_cache() -> int:
    with _lock:
        n = len(load_ai_cache())
        save_ai_cache({})
        return n


# ---------- ảnh chụp sao ----------
_SNAP = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")


def _hist_dir() -> Path:
    p = _path("history")
    p.mkdir(exist_ok=True)
    return p


def save_snapshot(day: dt.date, stars: dict) -> None:
    write_json(_hist_dir() / f"{day.isoformat()}.json", stars)


def previous_snapshot(today: dt.date):
    """Ảnh chụp gần nhất có ngày < today. Trả (ngày, {repo: sao}) hoặc (None, None)."""
    days = sorted(dt.date.fromisoformat(m.group(1)) for p in _hist_dir().iterdir()
                  if (m := _SNAP.match(p.name)) and m.group(1) < today.isoformat())
    if not days:
        return None, None
    d = days[-1]
    return d, read_json(_hist_dir() / f"{d.isoformat()}.json", {})
