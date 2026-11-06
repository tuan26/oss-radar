# -*- coding: utf-8 -*-
import json

import pytest

from app import ai
from fakes import AI_JSON, FakeAI


@pytest.mark.parametrize("text", [
    json.dumps(AI_JSON, ensure_ascii=False),
    "```json\n" + json.dumps(AI_JSON, ensure_ascii=False) + "\n```",
    "```\n" + json.dumps(AI_JSON, ensure_ascii=False) + "\n```",
    "Đây là kết quả:\n```json\n" + json.dumps(AI_JSON, ensure_ascii=False) + "\n```\nHy vọng hữu ích.",
    "<think>suy nghĩ {nháp}</think>\n" + json.dumps(AI_JSON, ensure_ascii=False),
    json.dumps(AI_JSON, ensure_ascii=False) + "\nGhi chú: {không phải json}",
])
def test_parse_json_tolerant(text):
    assert ai.parse_json(text) == AI_JSON


@pytest.mark.parametrize("text", ["", "không có json", "{hỏng", "[1, 2]"])
def test_parse_json_invalid(text):
    assert ai.parse_json(text) is None


REPO = {"name": "x/y", "category_label": "CRM", "license": "MIT", "deploy_model": "SaaS thoải mái",
        "description": "CRM"}


@pytest.fixture
def server():
    s = FakeAI()
    yield s
    s.close()


@pytest.mark.parametrize("kind,base", [("openai", "{u}/v1"), ("anthropic", "{u}")])
def test_both_protocols(server, kind, base):
    c = ai.AIClient(kind, base.format(u=server.url), "m1", server.key)
    assert c.test() == "ok"
    out = c.summarize(REPO, {"readme": "# X\n```bash\nrm -rf\n```\n![img](a.png)\nText", "features_raw": ["A feature"]})
    assert out["features"] == AI_JSON["features"]
    assert out["niche_hint"] == AI_JSON["niche_hint"]
    user = server.last_body["messages"][-1]["content"]
    assert "rm -rf" not in user and "a.png" not in user  # bỏ khối code và ảnh


def test_wrong_key_message_vietnamese(server):
    c = ai.AIClient("openai", server.url + "/v1", "m1", "sai")
    with pytest.raises(ai.AIError) as e:
        c.test()
    assert e.value.status == 401 and e.value.is_auth
    assert "API key sai" in str(e.value)


def test_unreachable_message():
    c = ai.AIClient("openai", "http://127.0.0.1:9/v1", "m1", "k", timeout=2)
    with pytest.raises(ai.AIError) as e:
        c.test()
    assert "Không kết nối được" in str(e.value)


def test_missing_config():
    with pytest.raises(ai.AIError):
        ai.AIClient("openai", "", "", "")
    assert ai.client_from_settings({"provider": "none"}) is None


def test_cache_key_changes_with_readme():
    k1 = ai.cache_key({"name": "A/B", "description": "d"}, {"readme": "r1"})
    k2 = ai.cache_key({"name": "A/B", "description": "d"}, {"readme": "r2"})
    assert k1 != k2 and k1.startswith("a/b:")
    assert k1 == ai.cache_key({"name": "A/B", "description": "d"}, {"readme": "r1"})


def _repos(n):
    return [{"name": f"o/r{i}", "license_group": "permissive", "feat_src": "readme", "score": {"total": 90 - i},
             "features": [], "strengths": [], "improvements": ["x"], "category_label": "CRM", "license": "MIT",
             "deploy_model": "SaaS", "description": f"d{i}"} for i in range(n)]


def test_enrich_limit_cache_and_source(server):
    c = ai.AIClient("openai", server.url + "/v1", "m1", server.key)
    repos, cache = _repos(5), {}
    st = ai.enrich(repos, {}, c, cache, max_repos=3, workers=2)
    assert st["calls"] == 3 and st["summarized"] == 3 and server.calls == 3
    assert [r["feat_src"] for r in repos] == ["ai"] * 3 + ["readme"] * 2   # ưu tiên điểm cao
    assert repos[0]["ai_model"] == "m1" and repos[0]["improvements"][0] == "Tích hợp Zalo OA"
    repos2 = _repos(5)
    st2 = ai.enrich(repos2, {}, c, cache, max_repos=3, workers=2)
    assert st2["calls"] == 0 and server.calls == 3 and repos2[0]["feat_src"] == "ai"


def test_enrich_aborts_after_three_auth_errors():
    s = FakeAI(mode="auth")
    try:
        c = ai.AIClient("openai", s.url + "/v1", "m1", "x")
        st = ai.enrich(_repos(20), {}, c, {}, max_repos=20, workers=1)
        assert st["aborted"] and s.calls == 3 and "xác thực" in st["error"]
    finally:
        s.close()


def test_estimate():
    repos = _repos(4)
    repos[0]["ai_key"] = "k0"
    repos[1]["ai_key"] = "k1"
    e = ai.estimate(repos, {"k0": {}}, 3, True)
    assert e == {"enabled": True, "candidates": 3, "cached": 1, "calls": 2}
