"""The OPC-UA server mirrors the PLC's registers at the addresses the PLC uses.

software/opcua/opcua.py copies GST, HPT, the two sensors and the stop and
manual flags from OpenPLC into OPC-UA variables. OpenPLC maps %MW<n> to
Modbus holding register 1024 + n, so the addresses follow from the variable
declarations in software/OpenPLC/cybICS.st. A wrong address does not fail,
it publishes an unrelated register (usually 0), which is why this compares
the sources instead of the live values. No stack needed.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPENPLC_MW_BASE = 1024


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def plc_registers():
    """Variable name -> holding register for every %MW variable in the PLC program."""
    source = read("software", "OpenPLC", "cybICS.st")
    return {
        name: OPENPLC_MW_BASE + int(word)
        for name, word in re.findall(r"^\s*(\w+)\s+AT\s+%MW(\d+)\s*:", source, re.M)
    }


def test_plc_program_declares_the_plant_registers():
    registers = plc_registers()
    for name in ("gst", "hpt", "stop", "manual", "systemSen", "boSen"):
        assert name in registers, name


def test_opcua_reads_each_variable_from_its_plc_register():
    registers = plc_registers()
    reads = re.findall(
        r"^\s*(\w+)\s*=\s*client\.read_holding_registers\((\d+)\)",
        read("software", "opcua", "opcua.py"),
        re.M,
    )
    assert reads, "no Modbus reads found in opcua.py"
    for name, address in reads:
        assert name in registers, f"{name} is not a %MW variable in cybICS.st"
        assert int(address) == registers[name], (
            f"opcua.py reads {name} from {address}, the PLC keeps it in {registers[name]}"
        )
