# -*- coding: utf-8 -*-
"""Chạy quét nền (một lần quét tại một thời điểm), tiến độ, dừng, lịch quét hằng tuần, chạy bù."""
import datetime as dt
import logging
import threading
import time
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from . import ai, config, notify, store
from .classify import classify_all, kb_for, summarize
from .scanner import GitHubAuthError, Scanner, ScanStopped

log = logging.getLogger("oss-radar")

MISFIRE_GRACE = 6 * 3600
DAY_LABEL = {"mon": "Thứ Hai", "tue": "Thứ Ba", "wed": "Thứ Tư", "thu": "Thứ Năm", "fri": "Thứ Sáu",
             "sat": "Thứ Bảy", "sun": "Chủ Nhật"}


# ---------------- quét ----------------
class ScanManager:
    def __init__(self, scanner_factory=None, notifier=None):
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self.scanner_factory = scanner_factory or self._default_scanner
        self.notifier = notifier or notify.send
        self.state = self._idle()

    @staticmethod
    def _idle():
        return {"running": False, "stopping": False, "phase": None, "done": 0, "total": 0,
                "message": "", "started_at": None, "trigger": None}

    @staticmethod
    def _default_scanner(settings, progress, stop_event):
        gh = settings["github"]
        kw = {}
        if config.github_api():
            kw["api"] = config.github_api()
        if config.github_raw():
            kw["raw"] = config.github_raw()
        return Scanner(github_token=gh["token"], min_stars=gh["min_stars"], categories=gh["categories"] or None,
                       progress=progress, stop_event=stop_event, **kw)

    # --- API công khai ---
    @property
    def running(self):
        return self.state["running"]

    def start(self, trigger="manual"):
        with self._lock:
            if self.state["running"]:
                return False
            self._stop.clear()
            self.state = dict(self._idle(), running=True, phase="search", message="Bắt đầu quét…",
                              started_at=time.time(), trigger=trigger)
            self._thread = threading.Thread(target=self._run, args=(trigger,), name="scan", daemon=True)
            self._thread.start()
            return True

    def stop(self):
        with self._lock:
            if not self.state["running"]:
                return False
            self._stop.set()
            self.state["stopping"] = True
            self.state["message"] = "Đang dừng…"
            return True

    def wait(self, timeout=None):
        t = self._thread
        if t:
            t.join(timeout)
        return not (t and t.is_alive())

    def status(self):
        s = dict(self.state)
        s["elapsed_s"] = round(time.time() - s["started_at"], 1) if s["running"] and s["started_at"] else 0
        return s

    # --- nội bộ ---
    def _progress(self, phase, done, total, message):
        if self._stop.is_set():
            return
        if phase:
            self.state.update(phase=phase, done=done, total=total)
        if message:
            self.state["message"] = message

    def _run(self, trigger):
        started = dt.datetime.now(dt.timezone.utc)
        t0 = time.time()
        rec = {"started_at": started.isoformat(timespec="seconds"), "trigger": trigger, "status": "ok",
               "error": "", "repos": 0, "ai_summarized": 0, "ai_calls": 0, "ai_error": ""}
        settings = store.load_settings()
        result = None
        try:
            scanner = self.scanner_factory(settings, self._progress, self._stop)
            raw = scanner.run()
            if self._stop.is_set():
                raise ScanStopped

            tz = ZoneInfo(settings["schedule"]["timezone"])
            today = dt.datetime.now(tz).date()
            prev_day, prev = store.previous_snapshot(today)
            prev_days = (today - prev_day).days if prev_day else 7
            self._progress("detail", len(raw), len(raw), "Phân loại license, chấm điểm")
            repos = classify_all(raw, prev, prev_days)
            raw_by_name = {r["full_name"].lower(): r for r in raw}

            # Bước AI (tùy chọn) — lỗi AI không làm hỏng lần quét
            cache = store.load_ai_cache()
            client = None
            try:
                client = ai.client_from_settings(settings["ai"])
            except ai.AIError as e:
                rec["ai_error"] = f"Cấu hình AI chưa đủ: {e}"
            n_cache = len(cache)
            stats = ai.enrich(repos, raw_by_name, client, cache, settings["ai"]["max_repos"],
                              settings["ai"]["workers"], self._progress, self._stop,
                              log=lambda m: log.warning(m))
            if len(cache) != n_cache:
                store.save_ai_cache(cache)   # lưu ngay cả khi bị dừng: đã trả tiền cho các lần gọi này
            rec.update(ai_summarized=stats["summarized"], ai_calls=stats["calls"],
                       ai_error=rec["ai_error"] or stats["error"])
            if self._stop.is_set():
                raise ScanStopped

            self.state.update(phase="save", message="Lưu kết quả")
            result = {"scanned_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                      "repos": repos, "summary": summarize(repos), "kb": kb_for(repos),
                      "has_history": prev is not None}
            store.save_results(result)
            store.save_snapshot(today, {r["name"].lower(): r["stars"] for r in repos})
            rec["repos"] = len(repos)
        except ScanStopped:
            rec.update(status="stopped", error="Đã dừng theo yêu cầu. Kết quả cũ được giữ nguyên.")
        except GitHubAuthError as e:
            rec.update(status="error", error=str(e))
        except Exception as e:
            log.exception("Quét lỗi")
            rec.update(status="error", error=f"Quét lỗi: {e.__class__.__name__}: {str(e)[:300]}")
        finally:
            rec["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            rec["duration_s"] = round(time.time() - t0, 1)
            store.add_run(rec)
            with self._lock:
                self.state = self._idle()
        self._notify(settings, rec, result)

    def _notify(self, settings, rec, result):
        tg = settings["telegram"]
        if not (tg["bot_token"] and tg["chat_id"]) or rec["status"] == "stopped":
            return
        try:
            if rec["status"] == "ok":
                text = notify.scan_message(result, rec, config.app_url(), tg["min_score"])
            else:
                text = notify.error_message(rec["error"], config.app_url())
            self.notifier(tg["bot_token"], tg["chat_id"], text)
        except Exception as e:
            log.warning("Gửi Telegram lỗi: %s", e)


# ---------------- lịch ----------------
def make_trigger(sched):
    return CronTrigger(day_of_week=sched["day_of_week"], hour=sched["hour"], minute=sched["minute"],
                       timezone=ZoneInfo(sched["timezone"]))


def next_run(sched, now=None):
    """Thời điểm chạy tới (datetime có múi giờ) hoặc None nếu lịch tắt."""
    if not sched.get("enabled"):
        return None
    tz = ZoneInfo(sched["timezone"])
    now = (now or dt.datetime.now(tz)).astimezone(tz)
    return make_trigger(sched).get_next_fire_time(None, now)


def previous_fire(sched, now):
    trig = make_trigger(sched)
    t = trig.get_next_fire_time(None, now - dt.timedelta(days=8))
    last = None
    while t and t <= now:
        last = t
        t = trig.get_next_fire_time(t, t + dt.timedelta(seconds=1))
    return last


def missed_run(sched, last_started, now=None, grace=MISFIRE_GRACE):
    """Nếu lần hẹn gần nhất đã qua (≤ grace giây) mà chưa có lần quét nào bắt đầu sau đó → trả thời điểm hẹn."""
    if not sched.get("enabled"):
        return None
    now = now or dt.datetime.now(dt.timezone.utc)
    prev = previous_fire(sched, now)
    if not prev or (now - prev).total_seconds() > grace:
        return None
    if last_started and last_started >= prev:
        return None
    return prev


class Scheduler:
    JOB_ID = "weekly-scan"

    def __init__(self, scans: ScanManager):
        self.scans = scans
        self.sched = BackgroundScheduler(timezone=dt.timezone.utc)

    def start(self):
        self.sched.start()
        self.apply(store.load_settings()["schedule"])
        self.catch_up()

    def shutdown(self):
        if self.sched.running:
            self.sched.shutdown(wait=False)

    def _fire(self):
        if not self.scans.start("schedule"):
            log.info("Bỏ qua lần quét theo lịch vì đang có lần quét khác")

    def apply(self, sched):
        """Áp dụng lịch mới ngay, không cần khởi động lại."""
        if self.sched.get_job(self.JOB_ID):
            self.sched.remove_job(self.JOB_ID)
        if sched.get("enabled"):
            self.sched.add_job(self._fire, make_trigger(sched), id=self.JOB_ID, replace_existing=True,
                               misfire_grace_time=MISFIRE_GRACE, coalesce=True, max_instances=1)

    def next_run(self):
        job = self.sched.get_job(self.JOB_ID)
        t = job.next_run_time if job else None
        return t.isoformat() if t else None

    def catch_up(self):
        sched = store.load_settings()["schedule"]
        runs = [r for r in store.load_runs() if r.get("started_at")]
        last = max((dt.datetime.fromisoformat(r["started_at"]) for r in runs), default=None)
        missed = missed_run(sched, last)
        if missed:
            log.info("Chạy bù lần quét lỡ lúc %s", missed.isoformat())
            self.scans.start("catchup")
        return missed


def describe(sched):
    if not sched.get("enabled"):
        return "Lịch đang tắt"
    return f"{DAY_LABEL[sched['day_of_week']]} {sched['hour']:02d}:{sched['minute']:02d} ({sched['timezone']})"
