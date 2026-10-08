"""Drive the Raspberry Pi's heartbeat LED, D12, at the brightness its board needs.

D12 is lit from 3V3 through R12 (1k) and sinks into GPIO4, so it is on while
the pin is low.  hardwareIO.py writes the PLC's heartbeat coil to that pin.

On v1.0 that is all there is: its green LEDs were dim, and the pin is driven
high and low directly.  v1.1 replaced them with a far more efficient part
(C2297), which driven low outshines everything else on the board.  The STM32
dims its own greens with software PWM, but that does not work here: RPi.GPIO's
PWM is a userspace thread, and on a Pi Zero running the whole stack its timing
jitter made the LED flicker visibly.  GPIO4 has no hardware PWM.

So on v1.1 the pin is not driven low at all to light the LED.  It becomes an
input with the internal pull-down, about 50k, which lets some 20 uA through
R12 and the LED: a steady glow, close to the STM32's dimmed greens, with no
timing involved.  Off is the pin driven high, as before.

The GPIO module is passed in rather than imported, so this runs and is tested
without a Pi.
"""


def dims(revision):
    """Whether a revision name from hw_version.read() needs the dimmed drive.

    None means the straps could not be read at all; that keeps the direct
    drive, which is what this pin always did.  hw_version.read() already maps
    an unrecognised code to the newest known revision.
    """
    return revision is not None and revision != "v1.0"


class HeartbeatLed:
    """The heartbeat output on `pin`; `dim` lights it through the pull-down."""

    def __init__(self, gpio, pin, dim):
        self._gpio = gpio
        self._pin = pin
        self._dim = dim
        self._level = None

    def set(self, level):
        """Write the heartbeat coil: a high level turns the LED off, low lights it."""
        level = bool(level)
        if level == self._level:
            return
        self._level = level
        gpio = self._gpio
        if not self._dim:
            gpio.output(self._pin, level)
        elif level:
            gpio.setup(self._pin, gpio.OUT, initial=gpio.HIGH)
        else:
            gpio.setup(self._pin, gpio.IN, pull_up_down=gpio.PUD_DOWN)
