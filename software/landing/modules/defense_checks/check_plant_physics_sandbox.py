"""
Challenge check: the student predicted what the plant does before touching it (plant_physics_sandbox).

The README describes three situations an attacker might create and asks
what the plant will do in each. The student works them out with the plant
sandbox in the Theory Path (a copy of the plant model that runs in the
browser) or by hand from the model, and answers four questions:

  settle_hpt       Manual mode, outputs frozen with the compressor on, the
                   refill off and the system valve closed, from GST 150 and
                   HPT 60: the HPT at which the plant comes to rest. The
                   compressor moves gas while the GST holds at least 50 bar
                   (hwio and firmware; the PLC's own guard is "> 50", but in
                   manual mode the PLC decides nothing), so GST 150, 148, ...,
                   50 are 51 transfers: HPT 111, GST 48.
  blowout_tick     Manual mode, compressor on, refill on, valve closed, from
                   GST 240 and HPT 90: the tick on which the blow-out valve
                   opens. The HPT rises by exactly 1 a tick and the valve
                   opens above 220, so tick 131. The refill keeps the GST far
                   above 50 (net -0.5 bar a tick on average); only refill
                   draws of 0 in nearly every tick could empty it first, so
                   the answer is practically, not strictly, draw-independent.
  spoof_ticks      Automatic mode, compressor off, HPT 62, GST 200: the PLC
                   sees a forged HPT of 40 in exactly one scan. Its latch
                   then keeps the compressor running on the real readings
                   until the HPT reaches 90: 28 ticks with gas moving. (The
                   README's control run without the attacker drains to
                   58-59 first and runs 31-32 ticks; a forged 60 is that
                   control run. Neither is graded, it depends on chance.)
  freeze_register  The one holding register an attacker writes once to make
                   the outputs stay as they are, whatever the PLC reads:
                   MANUAL, 1130 (%MW106). cybICS.st has an empty manual
                   branch.

tests/test_plant_physics_sandbox_check.py runs each situation with the real
tick of software/hwio-virtual/hardwareAbstraction.py and the PLC rules of
cybICS.st and derives these values, so the README, the model and this module
cannot drift apart. Grading is all or nothing (grade()'s default); the
module never touches the stack.
"""
import re

from modules.defense_checks._answers import grade, number, normalize

SETTLE_HPT = 111
BLOWOUT_TICK = 131
SPOOF_TICKS = 28
MANUAL_REGISTER = 1130   # %MW106 manual

# The register may be named by its address, its variable or its notation
# ("1130", "HR 1130", "%MW106", "manual (1130)", "41131"). Another register
# such as STOP (1128) fails, and so does a list of several.
_REGISTER_WORDS = frozenset({"manual", "mode", "hr", "holding", "register", "the",
                             "1130", "hr1130", "%mw106", "mw106", "41131", "0x46a"})
_REGISTER_IDS = frozenset({"1130", "hr1130", "%mw106", "mw106", "41131", "0x46a"})

LABELS = {
    "settle_hpt": "Situation 1: HPT at which the plant comes to rest (bar)",
    "blowout_tick": "Situation 2: tick on which the blow-out valve opens",
    "spoof_ticks": "Situation 3: ticks the compressor moves gas",
    "freeze_register": "Holding register that freezes the outputs",
}


def freeze_register(value):
    words = re.findall(r"%?[a-z0-9]+", normalize(value))
    return bool(words) and set(words) <= _REGISTER_WORDS and bool(_REGISTER_IDS & set(words))


def verify(answers=None):
    return grade(answers, {
        "settle_hpt": number(SETTLE_HPT),
        "blowout_tick": number(BLOWOUT_TICK),
        "spoof_ticks": number(SPOOF_TICKS),
        "freeze_register": freeze_register,
    }, labels=LABELS,
        success_message="You knew what the plant would do before it did it. That is the "
                        "attacker's preparation, and the defender's consequence analysis.",
        failure_message="At least one prediction does not match the plant yet.")
