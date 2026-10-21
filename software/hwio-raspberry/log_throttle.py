"""Keep a repeating log message from flooding the board's SD card.

While OpenPLC is unreachable, hwio retries the connection many times a second,
and every attempt logged the same errors: pymodbus's "Connection ... failed"
and hwio's own read and write failures.  On a board whose OpenPLC did not come
up, that was about 270 lines a second, 1.2 million lines in 75 minutes, and
Docker kept all of it.  The retries themselves are deliberate; only their log
lines are thinned out here.

The first occurrence of a message is logged as before.  The same message again
within WINDOW seconds is counted instead, and the next one after the window
says how many were left out.
"""

import logging
import threading
import time

WINDOW = 60.0


class RepeatFilter(logging.Filter):
  def __init__(self, window=WINDOW, clock=time.monotonic):
    super().__init__()
    self.window = window
    self.clock = clock
    self.lock = threading.Lock()
    # message key -> [time it was last let through, how many were dropped since]
    self.seen = {}

  def filter(self, record):
    key = (record.name, record.levelno, record.pathname, record.lineno, record.getMessage())
    now = self.clock()
    with self.lock:
      entry = self.seen.get(key)
      if entry is not None and now - entry[0] < self.window:
        entry[1] += 1
        return False
      dropped = entry[1] if entry is not None else 0
      self.seen[key] = [now, 0]
      if len(self.seen) > 1000:
        # Messages that vary (addresses, values) must not grow this forever.
        cutoff = now - self.window
        self.seen = {k: v for k, v in self.seen.items() if v[0] >= cutoff}
    if dropped:
      record.msg = f"{record.msg} (repeated {dropped} more times in the last {self.window:.0f} s)"
    return True


def install(window=WINDOW):
  """Attach the filter to every handler of the root logger, which is where
  pymodbus's messages end up too."""
  repeat_filter = RepeatFilter(window)
  for handler in logging.getLogger().handlers:
    handler.addFilter(repeat_filter)
  return repeat_filter
