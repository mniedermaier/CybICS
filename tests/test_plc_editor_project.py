"""The OpenPLC Editor project students start from matches the program OpenPLC runs.

The plc_programming challenge has students open the CybICS project in OpenPLC
Editor (training/plc_programming/software/plc.xml, and the same file on the
Engineering Workstation's desktop from software/engineeringWS/plc-software/),
change it, generate the Structured Text and download it to OpenPLC. Whatever
they generate replaces software/OpenPLC/cybICS.st on the controller.

The project once lagged behind the deployed program: systemSen and boSen were
%IX inputs instead of the %MW108/%MW110 registers the plant model writes, and
the GST refill state shared the heartbeat counter. A student who completed
the challenge left a controller that no longer exposed the blow-out sensor
(holding register 1134, read by the HMI and the physical_process check) and
no longer refilled the gas storage tank. These tests compare the sources so
that cannot drift again. No stack needed.
"""
import os
import re
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NS = {"p": "http://www.plcopen.org/xml/tc6_0201", "x": "http://www.w3.org/1999/xhtml"}
PROJECTS = (
    ("training", "plc_programming", "software", "plc.xml"),
    ("software", "engineeringWS", "plc-software", "plc.xml"),
)


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def st_program():
    """(variables, body, task) of software/OpenPLC/cybICS.st.

    variables maps name -> (address or None, type, initial value or None).
    """
    source = read("software", "OpenPLC", "cybICS.st")
    variables = {}
    for block in re.findall(r"^\s*VAR\n(.*?)^\s*END_VAR", source, re.S | re.M):
        for name, address, typ, init in re.findall(
                r"^\s*(\w+)(?:\s+AT\s+(%\S+))?\s*:\s*(\w+)\s*(?::=\s*([^;\s]+))?\s*;", block, re.M):
            variables[name] = (address or None, typ, init or None)
    body = source.split("END_VAR\n")[-1].split("END_PROGRAM")[0]
    task = re.search(r"TASK\s+\w+\(INTERVAL\s*:=\s*(T#\w+),\s*PRIORITY\s*:=\s*(\d+)\)", source)
    return variables, body, (task.group(1), task.group(2))


def xml_program(parts):
    root = ET.fromstring(read(*parts))
    pou = root.find(".//p:pou[@pouType='program']", NS)
    variables = {}
    for var in pou.findall("./p:interface/p:localVars/p:variable", NS):
        typ = next(iter(var.find("p:type", NS))).tag.split("}")[1]
        init = var.find("p:initialValue/p:simpleValue", NS)
        variables[var.get("name")] = (var.get("address"), typ,
                                      init.get("value") if init is not None else None)
    body = pou.find("./p:body/p:ST/x:p", NS).text
    task = root.find(".//p:task", NS)
    return variables, body, (task.get("interval"), task.get("priority"))


def _code(text):
    """ST without comments and whitespace, for comparing logic."""
    return re.sub(r"\s+", "", re.sub(r"\(\*.*?\*\)", "", text, flags=re.S))


def test_both_project_copies_are_identical():
    assert read(*PROJECTS[0]) == read(*PROJECTS[1])


def test_project_declares_the_deployed_variables():
    deployed, _, _ = st_program()
    project, _, _ = xml_program(PROJECTS[0])
    assert project == deployed


def test_project_logic_and_cycle_match_the_deployed_program():
    _, deployed_body, deployed_task = st_program()
    _, project_body, project_task = xml_program(PROJECTS[0])
    assert _code(project_body) == _code(deployed_body)
    assert project_task == deployed_task
