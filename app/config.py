# -*- coding: utf-8 -*-
"""Cấu hình đọc từ biến môi trường."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def data_dir() -> Path:
    p = Path(os.environ.get("DATA_DIR") or (Path.cwd() / "data"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def app_password() -> str:
    return os.environ.get("APP_PASSWORD", "")


def app_url() -> str:
    return os.environ.get("APP_URL", "").rstrip("/")


HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8080"))


# Chỉ dùng cho kiểm thử/giả lập: trỏ tới máy chủ GitHub giả
def github_api() -> str:
    return os.environ.get("GITHUB_API_URL", "")


def github_raw() -> str:
    return os.environ.get("GITHUB_RAW_URL", "")
