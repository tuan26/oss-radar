# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    d = tmp_path / "data"
    monkeypatch.setenv("DATA_DIR", str(d))
    monkeypatch.delenv("APP_PASSWORD", raising=False)
    monkeypatch.delenv("APP_URL", raising=False)
    return d
