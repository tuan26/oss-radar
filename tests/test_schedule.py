# -*- coding: utf-8 -*-
import datetime as dt
import time
from zoneinfo import ZoneInfo

from app import jobs, store

VN = ZoneInfo("Asia/Ho_Chi_Minh")
MON7 = {"enabled": True, "day_of_week": "mon", "hour": 7, "minute": 0, "timezone": "Asia/Ho_Chi_Minh"}


def test_next_run_monday_7am():
    now = dt.datetime(2026, 11, 6, 10, 0, tzinfo=VN)    # Thứ Sáu
    t = jobs.next_run(MON7, now)
    assert t == dt.datetime(2026, 11, 9, 7, 0, tzinfo=VN)
    assert t.weekday() == 0


def test_next_run_same_day_before_and_after():
    assert jobs.next_run(MON7, dt.datetime(2026, 11, 9, 6, 59, tzinfo=VN)) == dt.datetime(2026, 11, 9, 7, 0, tzinfo=VN)
    assert jobs.next_run(MON7, dt.datetime(2026, 11, 9, 7, 1, tzinfo=VN)) == dt.datetime(2026, 11, 16, 7, 0, tzinfo=VN)


def test_next_run_other_timezone_and_disabled():
    s = dict(MON7, timezone="Europe/Berlin", day_of_week="sun", hour=23, minute=30)
    t = jobs.next_run(s, dt.datetime(2026, 11, 6, 0, 0, tzinfo=dt.timezone.utc))
    assert t.isoformat() == "2026-11-08T23:30:00+01:00"
    assert jobs.next_run(dict(MON7, enabled=False)) is None


def test_missed_run_catch_up():
    fire = dt.datetime(2026, 11, 9, 7, 0, tzinfo=VN)
    now = fire + dt.timedelta(hours=2)
    assert jobs.missed_run(MON7, None, now) == fire                         # lỡ 2 giờ → chạy bù
    assert jobs.missed_run(MON7, fire + dt.timedelta(minutes=1), now) is None   # đã chạy rồi
    assert jobs.missed_run(MON7, fire - dt.timedelta(days=7), now) == fire      # lần chạy trước là tuần trước
    assert jobs.missed_run(MON7, None, fire + dt.timedelta(hours=7)) is None    # quá 6 giờ → bỏ
    assert jobs.missed_run(dict(MON7, enabled=False), None, now) is None


class _Scans:
    def __init__(self):
        self.started = []

    def start(self, trigger):
        self.started.append(trigger)
        return True


def test_scheduler_applies_immediately_and_fires():
    scans = _Scans()
    sch = jobs.Scheduler(scans)
    sch.sched.start()
    try:
        sch.apply(MON7)
        assert sch.next_run().endswith("+07:00") and "T07:00:00" in sch.next_run()
        # Đổi lịch sang ~2 giây nữa: job tự chạy mà không cần khởi động lại
        soon = dt.datetime.now(VN) + dt.timedelta(seconds=2)
        sch.sched.get_job(sch.JOB_ID).modify(next_run_time=soon)
        deadline = time.time() + 10
        while not scans.started and time.time() < deadline:
            time.sleep(0.1)
        assert scans.started == ["schedule"]
        sch.apply(dict(MON7, enabled=False))
        assert sch.next_run() is None
    finally:
        sch.shutdown()


def test_scheduler_minute_trigger_applies_live():
    """Đặt lịch đúng phút kế tiếp qua apply(): next_run phản ánh ngay lịch mới."""
    scans = _Scans()
    sch = jobs.Scheduler(scans)
    sch.sched.start()
    try:
        nxt = dt.datetime.now(VN) + dt.timedelta(minutes=1)
        s = dict(MON7, day_of_week=["mon", "tue", "wed", "thu", "fri", "sat", "sun"][nxt.weekday()],
                 hour=nxt.hour, minute=nxt.minute)
        sch.apply(s)
        got = dt.datetime.fromisoformat(sch.next_run())
        assert got == nxt.replace(second=0, microsecond=0)
    finally:
        sch.shutdown()


def test_catch_up_on_startup(monkeypatch):
    fire = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)
    local = fire.astimezone(VN)
    s = store.load_settings()
    s["schedule"] = dict(MON7, day_of_week=["mon", "tue", "wed", "thu", "fri", "sat", "sun"][local.weekday()],
                         hour=local.hour, minute=local.minute)
    store.save_settings(s)
    scans = _Scans()
    sch = jobs.Scheduler(scans)
    assert sch.catch_up() is not None and scans.started == ["catchup"]
