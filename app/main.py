# -*- coding: utf-8 -*-
"""OSS Radar — FastAPI: REST API + phục vụ giao diện."""
import base64
import binascii
import json
import logging
import secrets
from contextlib import asynccontextmanager

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response

from . import ai, config, jobs, notify, store
from .classify import kb_for, summarize
from .knowledge import CATEGORY_LABEL
from .scanner import CATEGORIES

log = logging.getLogger("oss-radar")


class RedactSecrets(logging.Filter):
    """Lớp phòng thủ cuối: thay mọi bí mật đã lưu bằng *** nếu lỡ lọt vào log."""

    def filter(self, record):
        try:
            secrets_ = store.secrets_of(store.load_settings())
        except Exception:
            return True
        if secrets_:
            msg = record.getMessage()
            red = msg
            for s in secrets_:
                red = red.replace(s, "***")
            if red != msg:
                record.msg, record.args = red, ()
        return True


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    f = RedactSecrets()
    for name in ("", "oss-radar", "uvicorn", "uvicorn.error", "uvicorn.access", "apscheduler"):
        lg = logging.getLogger(name)
        if not any(isinstance(x, RedactSecrets) for x in lg.filters):
            lg.addFilter(f)
        for h in lg.handlers:
            if not any(isinstance(x, RedactSecrets) for x in h.filters):
                h.addFilter(f)


def create_app(start_scheduler=True, scans=None):
    scans = scans or jobs.ScanManager()
    scheduler = jobs.Scheduler(scans)

    @asynccontextmanager
    async def lifespan(app):
        setup_logging()
        if config.HOST not in ("127.0.0.1", "localhost", "::1") and not config.app_password():
            log.warning("CẢNH BÁO: app đang mở ra ngoài (HOST=%s) mà CHƯA đặt APP_PASSWORD. "
                        "Ai biết địa chỉ cũng xem và sửa được cài đặt.", config.HOST)
        if start_scheduler:
            scheduler.start()
        yield
        scheduler.shutdown()

    app = FastAPI(title="OSS Radar", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.scans, app.state.scheduler = scans, scheduler
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    @app.middleware("http")
    async def basic_auth(request: Request, call_next):
        pw = config.app_password()
        if pw:
            ok = False
            h = request.headers.get("authorization", "")
            if h.lower().startswith("basic "):
                try:
                    _, _, given = base64.b64decode(h[6:]).decode("utf-8").partition(":")
                    ok = secrets.compare_digest(given.encode(), pw.encode())
                except (binascii.Error, UnicodeDecodeError):
                    ok = False
            if not ok:
                return Response("Cần đăng nhập", status_code=401,
                                headers={"WWW-Authenticate": 'Basic realm="OSS Radar", charset="UTF-8"'})
        return await call_next(request)

    def settings_view(s):
        out = store.mask_settings(s)
        out["presets"] = {k: dict(v) for k, v in ai.PRESETS.items()}
        out["categories"] = {k: CATEGORY_LABEL.get(k, k) for k in CATEGORIES}
        out["next_run"] = scheduler.next_run() if start_scheduler else (
            (t := jobs.next_run(s["schedule"])) and t.isoformat())
        out["schedule_text"] = jobs.describe(s["schedule"])
        return out

    @app.get("/")
    def index():
        return FileResponse(config.BASE_DIR / "static" / "index.html",
                            headers={"Cache-Control": "no-cache"})

    @app.get("/api/data")
    def data():
        res = store.load_results()
        if not res:
            return {"scanned_at": None, "repos": [], "summary": {}, "kb": {}, "has_history": False}
        return res

    @app.get("/api/settings")
    def get_settings():
        return settings_view(store.load_settings())

    @app.post("/api/settings")
    def post_settings(body: dict = Body(default={})):
        try:
            s = store.apply_update(store.load_settings(), body, presets=ai.PRESETS, categories=CATEGORIES)
        except store.SettingsError as e:
            raise HTTPException(400, str(e))
        store.save_settings(s)
        if start_scheduler:
            scheduler.apply(s["schedule"])
        return settings_view(s)

    @app.post("/api/scan")
    def scan():
        started = scans.start("manual")
        return {"started": started, "status": status()}

    @app.post("/api/scan/stop")
    def scan_stop():
        return {"stopping": scans.stop()}

    @app.get("/api/status")
    def status():
        s = store.load_settings()
        res = store.load_results() or {}
        st = scans.status()
        st["last_run"] = store.last_run()
        st["next_run"] = scheduler.next_run() if start_scheduler else None
        st["scanned_at"] = res.get("scanned_at")
        enabled = s["ai"]["provider"] != "none"
        st["ai_estimate"] = ai.estimate(res.get("repos"), store.load_ai_cache(), s["ai"]["max_repos"], enabled)
        st["ai_estimate"]["max_repos"] = s["ai"]["max_repos"]
        st["has_data"] = bool(res.get("repos"))
        return st

    @app.post("/api/ai/test")
    def ai_test(body: dict = Body(default={})):
        saved = store.load_settings()["ai"]
        cfg = dict(saved)
        for k in ("provider", "kind", "base_url", "model"):
            if body.get(k) is not None:
                cfg[k] = str(body[k]).strip()
        if isinstance(body.get("api_key"), str) and body["api_key"].strip():
            cfg["api_key"] = body["api_key"].strip()
        if cfg.get("provider", "none") == "none":
            return {"ok": False, "error": "Đang ở chế độ 'Không dùng AI'. Chọn một nhà cung cấp trước."}
        try:
            client = ai.client_from_settings(cfg)
            reply = client.test()
        except ai.AIError as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True, "reply": reply, "model": cfg["model"]}

    @app.post("/api/ai/clear-cache")
    def ai_clear():
        return {"cleared": store.clear_ai_cache()}

    @app.post("/api/notify/test")
    def notify_test(body: dict = Body(default={})):
        tg = store.load_settings()["telegram"]
        token = (body.get("bot_token") or "").strip() or tg["bot_token"]
        chat = (body.get("chat_id") or "").strip() or tg["chat_id"]
        try:
            notify.send(token, chat, "✅ OSS Radar: gửi thử thành công. Bạn sẽ nhận tóm tắt sau mỗi lần quét.")
        except notify.NotifyError as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True}

    @app.post("/api/sample")
    def load_sample(force: int = 0):
        if store.load_results() and not force:
            raise HTTPException(409, "Đã có dữ liệu quét thật; không ghi đè bằng dữ liệu mẫu.")
        data = json.loads((config.BASE_DIR / "sample_data.json").read_text(encoding="utf-8"))
        for r in data["repos"]:
            r.setdefault("is_new", False)
            r.setdefault("niche_hint", "")
            r.setdefault("ai_model", "")
        data["summary"] = summarize(data["repos"])
        data["kb"] = data.get("kb") or kb_for(data["repos"])
        data["has_history"] = False
        data["sample"] = True
        store.save_results(data)
        return {"loaded": len(data["repos"])}

    @app.exception_handler(Exception)
    async def unhandled(request, exc):
        log.exception("Lỗi không mong đợi")
        return JSONResponse({"detail": "Lỗi máy chủ. Xem log để biết chi tiết."}, status_code=500)

    return app


app = create_app()


def run():
    import uvicorn
    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT)


if __name__ == "__main__":
    run()
