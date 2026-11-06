# -*- coding: utf-8 -*-
"""Thông báo Telegram sau mỗi lần quét."""
import html

import requests

from .classify import SAFE_GROUPS, SUMMARY_GROUPS

TG_API = "https://api.telegram.org"
GROUP_LABEL = {"permissive": "SaaS thoải mái", "gpl": "GPL", "agpl": "AGPL", "single-tenant": "Riêng từng khách",
               "unknown": "Cần đọc tay", "restricted": "Loại (hạn chế)", "none": "Loại (không license)"}


class NotifyError(Exception):
    pass


def send(bot_token, chat_id, text, api=TG_API):
    if not bot_token or not chat_id:
        raise NotifyError("Chưa nhập bot token hoặc chat ID")
    try:
        r = requests.post(f"{api}/bot{bot_token}/sendMessage", timeout=20,
                          json={"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                                "disable_web_page_preview": True})
    except requests.RequestException as e:
        # Không đưa thông điệp gốc ra ngoài vì URL có chứa token
        raise NotifyError(f"Không kết nối được tới Telegram ({e.__class__.__name__})")
    if r.status_code == 200:
        return True
    try:
        desc = r.json().get("description", "")
    except Exception:
        desc = ""
    hint = {401: "Bot token sai", 400: "Chat ID sai, hoặc bạn chưa bấm Start với bot",
            403: "Bot bị chặn hoặc chưa được thêm vào nhóm", 404: "Bot token sai"}.get(r.status_code, "")
    raise NotifyError(f"Telegram báo lỗi {r.status_code}{' — ' + hint if hint else ''}"
                      f"{': ' + desc[:150] if desc else ''}")


def highlights(repos, min_score=75, n=5):
    """Tối đa n repo an toàn, đạt ngưỡng điểm, là repo mới hoặc tăng sao mạnh nhất tuần."""
    pool = [r for r in repos if r["license_group"] in SAFE_GROUPS and r["score"]["total"] >= min_score
            and (r.get("is_new") or (r["tech"].get("weekly_delta") or 0) > 0)]
    new =sorted([r for r in pool if r.get("is_new")], key=lambda r: r["score"]["total"], reverse=True)
    grow = sorted([r for r in pool if not r.get("is_new")], key=lambda r: r["tech"].get("weekly_delta") or 0, reverse=True)
    picked, i, j = [], 0, 0
    while len(picked) < n and (i < len(new) or j < len(grow)):   # xen kẽ để có cả hai loại
        if i < len(new):
            picked.append(new[i]); i += 1
        if len(picked) < n and j < len(grow):
            picked.append(grow[j]); j += 1
    return picked


def scan_message(result, run, app_url="", min_score=75):
    repos = result.get("repos", [])
    summ = result.get("summary") or {}
    e = html.escape
    lines = [f"<b>OSS Radar</b> — quét xong {len(repos)} repo"
             + (f" trong {round(run.get('duration_s', 0) / 60, 1)} phút" if run else "")]
    lines.append(" · ".join(f"{GROUP_LABEL[g]}: {summ.get(g, 0)}" for g in SUMMARY_GROUPS if summ.get(g)))
    if run and run.get("ai_summarized"):
        lines.append(f"AI tóm tắt: {run['ai_summarized']} repo")
    hl = highlights(repos, min_score)
    if hl:
        lines.append("")
        lines.append(f"<b>Đáng chú ý (điểm ≥ {min_score})</b>")
        for r in hl:
            tag = "🆕 mới" if r.get("is_new") else f"+{r['tech']['weekly_delta']} sao/tuần"
            lines.append(f"• <a href=\"{e(r['url'])}\">{e(r['name'])}</a> — {r['score']['total']} điểm, "
                         f"{e(r['category_label'])}, {tag}")
    elif result.get("has_history"):
        lines.append(f"Không có repo mới hoặc tăng sao đạt ngưỡng {min_score} điểm.")
    if app_url:
        lines.append("")
        lines.append(f"Mở app: {e(app_url)}")
    return "\n".join(lines)


def error_message(err, app_url=""):
    msg = f"<b>OSS Radar</b> — quét lỗi: {html.escape(str(err))[:500]}"
    return msg + (f"\nMở app: {html.escape(app_url)}" if app_url else "")
