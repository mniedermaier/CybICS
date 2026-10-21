"""Unit tests for hwio-raspberry's repeat filter (software/hwio-raspberry/log_throttle.py).

While OpenPLC was down, hwio logged the same connection errors about 270 times
a second and filled the board's SD card. The filter lets the first of a message
through, counts its repeats for a minute, and reports the count with the next
one after that. No stack needed.
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "software" / "hwio-raspberry"))
import log_throttle  # noqa: E402


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def record(msg, lineno=10, args=()):
    return logging.LogRecord("pymodbus", logging.ERROR, "tcp.py", lineno, msg, args, None)


def test_repeats_within_the_window_are_dropped_and_counted():
    clock = Clock()
    f = log_throttle.RepeatFilter(window=60, clock=clock)
    assert f.filter(record("Connection to (openplc, 502) failed"))
    for _ in range(269):
        clock.now += 0.2
        assert not f.filter(record("Connection to (openplc, 502) failed"))
    clock.now += 60
    again = record("Connection to (openplc, 502) failed")
    assert f.filter(again)
    assert again.getMessage().endswith("(repeated 269 more times in the last 60 s)")


def test_different_messages_and_call_sites_pass():
    f = log_throttle.RepeatFilter(window=60, clock=Clock())
    assert f.filter(record("Read from OpenPLC failed"))
    assert f.filter(record("Write to OpenPLC failed"))
    assert f.filter(record("Read from OpenPLC failed", lineno=11))
    assert f.filter(record("value %s", args=(1,)))
    assert f.filter(record("value %s", args=(2,)))


def test_a_message_after_a_quiet_window_carries_no_count():
    clock = Clock()
    f = log_throttle.RepeatFilter(window=60, clock=clock)
    assert f.filter(record("is alive"))
    clock.now += 61
    later = record("is alive")
    assert f.filter(later)
    assert later.getMessage() == "is alive"


def test_the_table_of_seen_messages_is_bounded():
    clock = Clock()
    f = log_throttle.RepeatFilter(window=60, clock=clock)
    for n in range(1500):
        clock.now += 1
        f.filter(record(f"value {n}"))
    assert len(f.seen) <= 1000
