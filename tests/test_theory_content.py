"""The Theory Path content: config, articles and their sidecar JSON.

Needs no stack. These are the rules in training/theory/AUTHORING.md, checked
for every topic, so that an article that breaks the page layout, links to a
challenge that does not exist or ships a quiz without an answer fails here
rather than in front of a class.
"""
import json
import os
import re
from html.parser import HTMLParser

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANDING = os.path.join(ROOT, "software", "landing")
CONFIG = os.path.join(LANDING, "theory_config.json")
CTF_CONFIG = os.path.join(LANDING, "ctf_config.json")
GLOSSARY = os.path.join(ROOT, "training", "theory", "glossary.json")

WIDGETS = {
    "plant-live", "modbus-frame", "s7-layers", "register-decoder",
    "purdue-explorer", "scan-cycle", "ids-threshold", "firewall-rules",
    "arp-spoof", "keyspace", "alert-log", "opcua-security", "sequence",
    "rate-planner", "uart-frame", "plant-predict", "plant-sandbox",
    "checkpoint",
}
LEVELS = {"beginner", "intermediate", "advanced"}
MODULE_HEADINGS = [
    "The idea", "How it looks on CybICS", "How to approach it",
    "Detect and defend", "Before you start",
]
# A selector in an article's <style> block that starts with one of these
# restyles the whole page, not the article's own figure.
GLOBAL_SELECTOR = re.compile(
    r"^(\*|html|body|\.article|figure|svg|header|main|nav|section|div|p|a|"
    r"h[1-6]|table|ul|ol|li|code|pre|img|text|g|rect|path|line|circle)\b"
)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


CONFIG_DATA = load_json(CONFIG)
TOPICS = [t for s in CONFIG_DATA["sections"].values() for t in s["topics"]]
TOPIC_IDS = [t["id"] for t in TOPICS]


def challenge_ids():
    ctf = load_json(CTF_CONFIG)
    return {ch["id"] for cat in ctf["categories"].values() for ch in cat["challenges"]}


def article(topic):
    with open(os.path.join(LANDING, "..", "..", topic["content"]), encoding="utf-8") as f:
        return f.read()


def sidecar_path(topic):
    return os.path.join(ROOT, topic["content"][:-3] + ".json")


def sidecar(topic):
    return load_json(sidecar_path(topic))


def is_module(topic):
    return topic["content"].startswith("training/theory/modules/")


class TagCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def tags_of(text):
    parser = TagCollector()
    parser.feed(re.sub(r"<style>.*?</style>", "", text, flags=re.S))
    return parser.tags


def test_topic_ids_are_unique():
    duplicates = {i for i in TOPIC_IDS if TOPIC_IDS.count(i) > 1}
    assert not duplicates, f"duplicate topic ids: {duplicates}"


def test_topic_ids_are_url_safe():
    for topic_id in TOPIC_IDS:
        assert re.fullmatch(r"[a-z0-9][a-z0-9_-]*", topic_id, re.I), topic_id


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_topic_has_its_files(topic):
    for key in ("id", "title", "summary", "content"):
        assert topic.get(key), f"{topic['id']}: missing {key}"
    assert topic["content"].endswith(".md")
    assert os.path.isfile(os.path.join(ROOT, topic["content"])), topic["content"]
    assert os.path.isfile(sidecar_path(topic)), f"{topic['id']}: no sidecar JSON"


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_related_challenges_and_prerequisites_exist(topic):
    known = challenge_ids()
    for related in topic.get("related", []):
        assert related["id"] in known, f"{topic['id']}: unknown challenge {related['id']}"
        assert related.get("label"), f"{topic['id']}: related link without a label"
    for prerequisite in topic.get("prerequisites", []):
        assert prerequisite in TOPIC_IDS, f"{topic['id']}: unknown prerequisite {prerequisite}"
        assert prerequisite != topic["id"]


def test_prerequisites_come_earlier_in_the_path():
    position = {topic_id: i for i, topic_id in enumerate(TOPIC_IDS)}
    for topic in TOPICS:
        for prerequisite in topic.get("prerequisites", []):
            assert position[prerequisite] < position[topic["id"]], (
                f"{topic['id']} needs {prerequisite}, which comes later in the path")


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_sidecar_schema(topic):
    data = sidecar(topic)
    assert data.get("level") in LEVELS, f"{topic['id']}: level {data.get('level')!r}"
    assert 2 <= len(data.get("objectives", [])) <= 4, f"{topic['id']}: objectives"
    assert 3 <= len(data.get("takeaways", [])) <= 5, f"{topic['id']}: takeaways"
    quiz = data.get("quiz", [])
    assert 4 <= len(quiz) <= 6, f"{topic['id']}: {len(quiz)} quiz questions"
    for question in quiz + data.get("checkpoints", []):
        where = f"{topic['id']}: {question.get('question', '')[:50]!r}"
        options = question.get("options", [])
        assert question.get("question") and question.get("explanation"), where
        assert 2 <= len(options) <= 6 and len(set(options)) == len(options), where
        kind = question.get("type", "single")
        assert kind in ("single", "multi"), where
        answer = question.get("answer")
        if kind == "single":
            assert isinstance(answer, int) and 0 <= answer < len(options), where
        else:
            assert isinstance(answer, list) and answer, where
            assert all(isinstance(a, int) and 0 <= a < len(options) for a in answer), where
            assert len(set(answer)) == len(answer), where
    for checkpoint in data.get("checkpoints", []):
        assert re.fullmatch(r"[a-z0-9-]+", checkpoint.get("id", "")), topic["id"]


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_article_structure(topic):
    text = article(topic)
    assert text.lstrip().startswith("# "), f"{topic['id']}: must start with '# Title'"
    headings = re.findall(r"^## (.+?)\s*$", text, re.M)
    assert len(headings) >= 3, f"{topic['id']}: needs at least three ## sections"
    if is_module(topic):
        assert headings[:len(MODULE_HEADINGS)] == MODULE_HEADINGS, (
            f"{topic['id']}: module sections are {headings}")


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_article_figures_are_accessible(topic):
    tags = tags_of(article(topic))
    svgs = [attrs for tag, attrs in tags if tag == "svg"]
    for attrs in svgs:
        assert attrs.get("role") == "img", f"{topic['id']}: <svg> without role=img"
        assert attrs.get("aria-label"), f"{topic['id']}: <svg> without aria-label"
    figures = sum(1 for tag, _ in tags if tag == "figure")
    captions = sum(1 for tag, _ in tags if tag == "figcaption")
    assert figures == captions, f"{topic['id']}: {figures} figures, {captions} captions"


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_article_styles_stay_scoped(topic):
    for block in re.findall(r"<style>(.*?)</style>", article(topic), flags=re.S):
        css = re.sub(r"/\*.*?\*/", "", block, flags=re.S)
        assert "@import" not in css and "url(" not in css, topic["id"]
        # Selectors are what precedes a '{' outside @keyframes bodies.
        css = re.sub(r"@keyframes[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css)
        css = re.sub(r"@media[^{]*\{", "", css)
        for selector_list in re.findall(r"([^{}]+)\{", css):
            for selector in selector_list.split(","):
                selector = selector.strip()
                if selector:
                    assert not GLOBAL_SELECTOR.match(selector), (
                        f"{topic['id']}: unscoped selector {selector!r}")


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_article_widgets_and_links_resolve(topic):
    text = article(topic)
    data = sidecar(topic)
    checkpoint_ids = {c["id"] for c in data.get("checkpoints", [])}
    for tag, attrs in tags_of(text):
        widget = attrs.get("data-widget")
        if widget is None:
            continue
        assert widget in WIDGETS, f"{topic['id']}: unknown widget {widget}"
        if widget == "checkpoint":
            assert attrs.get("data-id") in checkpoint_ids, (
                f"{topic['id']}: checkpoint {attrs.get('data-id')} not in sidecar")
        if widget == "sequence":
            assert attrs.get("data-id") in data.get("exercises", {}), (
                f"{topic['id']}: exercise {attrs.get('data-id')} not in sidecar")
    for target in re.findall(r"\]\(/theory/([^)#\s]+)", text):
        assert target in TOPIC_IDS, f"{topic['id']}: link to unknown topic {target}"
    for target in re.findall(r"\]\(/ctf/challenge/([^)#/\s]+)\)", text):
        assert target in challenge_ids(), f"{topic['id']}: link to unknown challenge {target}"


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_sequence_exercises_are_well_formed(topic):
    for name, ex in sidecar(topic).get("exercises", {}).items():
        where = f"{topic['id']}/{name}"
        assert ex.get("type") == "sequence", where
        assert ex.get("title") and ex.get("intro"), where
        steps = ex.get("steps", [])
        assert 3 <= len(steps) <= 8, f"{where}: {len(steps)} steps"
        texts = [st["text"] for st in steps]
        assert len(set(texts)) == len(texts), f"{where}: duplicate step"
        labels = ex.get("labels", [])
        assert len(set(labels)) == len(labels), f"{where}: duplicate label"
        for st in steps:
            assert st.get("explain"), f"{where}: step without explanation"
            # The position must come from understanding, not from the wording.
            assert not re.match(r"(first|then|finally|next|lastly)\b", st["text"], re.I), f"{where}: {st['text']}"
            if labels or ex.get("order") is False:
                assert st.get("label") in labels, f"{where}: label {st.get('label')!r} not offered"


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_instructor_notes_are_well_formed(topic):
    """Instructor notes are cut out before rendering by a non-greedy match, so
    one that contains another <details> would leak its second half."""
    for note in re.findall(r'<details class="instructor"[^>]*>(.*?)</details>', article(topic), re.S):
        assert "<details" not in note, f"{topic['id']}: nested <details> in an instructor note"


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_article_gives_no_flag_away(topic):
    for text in (article(topic), json.dumps(sidecar(topic))):
        assert not re.search(r"CybICS\([^)]+\)", text), f"{topic['id']}: contains a flag"


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_article_has_no_scripts(topic):
    text = article(topic)
    assert "<script" not in text.lower(), topic["id"]
    assert not re.search(r"\son[a-z]+\s*=", text), f"{topic['id']}: event handler attribute"


def test_glossary_is_well_formed():
    glossary = load_json(GLOSSARY)
    assert len(glossary) >= 30
    seen = set()
    for entry in glossary:
        assert entry.get("term") and entry.get("definition"), entry
        for name in [entry["term"], *entry.get("aliases", [])]:
            assert name.lower() not in seen, f"glossary term twice: {name}"
            seen.add(name.lower())
        for target in re.findall(r"/theory/([A-Za-z0-9_-]+)", entry.get("link", "")):
            assert target in TOPIC_IDS, f"glossary link to unknown topic {target}"


def test_the_right_answer_is_not_given_away_by_its_length():
    """A student who always picks the longest (or shortest) option must not pass.

    The page shuffles the options, so their position no longer gives the
    answer away; their length still would. Distractors should be plausible
    misconceptions, about as long as the right answer.
    """
    longest = shortest = total = 0
    for topic in TOPICS:
        data = sidecar(topic)
        for question in data.get("quiz", []) + data.get("checkpoints", []):
            options = question["options"]
            if question.get("type", "single") != "single" or len(options) < 3:
                continue
            lengths = [len(o) for o in options]
            mine = lengths[question["answer"]]
            total += 1
            longest += mine == max(lengths) and lengths.count(mine) == 1
            shortest += mine == min(lengths) and lengths.count(mine) == 1
    # By chance either would be about 30 per cent.
    assert longest / total <= 0.4, f"the right answer is the longest in {longest} of {total} questions"
    assert shortest / total <= 0.4, f"the right answer is the shortest in {shortest} of {total} questions"


def test_core_path_is_self_contained():
    """The short core path must not send a beginner to a lesson outside it."""
    core = {t["id"] for t in TOPICS if t.get("core")}
    assert 6 <= len(core) <= 12
    for topic in TOPICS:
        if topic["id"] in core:
            missing = set(topic.get("prerequisites", [])) - core
            assert not missing, f"core lesson {topic['id']} needs {missing}"


def test_purdue_explorer_matches_the_ids_host_table():
    """The widget names the same hosts at the same addresses as the IDS."""
    with open(os.path.join(ROOT, "software", "ids", "rules.py"), encoding="utf-8") as f:
        known = dict(re.findall(r'"(172\.18\.0\.\d+)":\s*"([\w-]+)"', f.read()))
    with open(os.path.join(LANDING, "static", "js", "theory-widgets.js"), encoding="utf-8") as f:
        widgets = f.read()
    hosts = re.findall(r"\{ id: '([\w-]+)', name: '[^']*', ip: '(172\.18\.0\.\d+)'", widgets)
    assert len(hosts) >= 8
    for host_id, ip in hosts:
        assert ip in known, f"{host_id} at {ip} is not in KNOWN_SERVICES"
        if host_id != "attack":
            assert known[ip] == host_id, f"{ip} is {known[ip]} in the IDS, {host_id} in the widget"


def test_purdue_explorer_ids_claims_match_the_rules():
    """What the widget says the IDS exempts is what rules.py exempts."""
    with open(os.path.join(ROOT, "software", "ids", "rules.py"), encoding="utf-8") as f:
        rules = f.read()
    writers = set(re.findall(r'"(\w+)"', re.search(r"_MODBUS_WRITERS = frozenset\(\((.*?)\)\)", rules).group(1)))
    with open(os.path.join(LANDING, "static", "js", "theory-widgets.js"), encoding="utf-8") as f:
        widgets = f.read()
    hosts = re.findall(r"\{ id: '([\w-]+)', name: .*?ids: '((?:[^'\\]|\\.)*)' \}", widgets, re.S)
    assert len(hosts) >= 8
    for host_id, claim in hosts:
        assert "allowlist" not in claim.lower(), f"{host_id}: no host is allowlisted wholesale"
        if re.search(r"(?<!not an )expected Modbus writer", claim, re.I):
            assert host_id in writers, f"{host_id} is called an expected Modbus writer, rules.py disagrees"


def test_scan_cycle_widget_decides_like_the_plc_program():
    """plcScan in the widget repeats the automatic-mode rules of cybICS.st.
    Compare the conditions, so a changed threshold in one shows up here."""
    def norm(cond):
        cond = re.sub(r"\b(inputs|state)\.", "", cond)
        cond = cond.replace("===", "=").replace("&&", "AND")
        return re.sub(r"\s+", "", cond)

    with open(os.path.join(ROOT, "software", "OpenPLC", "cybICS.st"), encoding="utf-8") as f:
        st = f.read()
    auto = st.split("IF manual < 1 THEN", 1)[1].split("(* ELSE System running in manual mode *)", 1)[0]
    plc = {norm(c) for c in re.findall(r"\b(?:ELS)?IF\s+(.+?)\s+THEN", auto)}
    plc -= {"compressorState=1", "gstState=1"}   # copying the state to the outputs

    with open(os.path.join(LANDING, "static", "js", "theory-widgets.js"), encoding="utf-8") as f:
        js = f.read()
    body = js.split("function plcScan(", 1)[1].split("\n    }\n", 1)[0]
    widget = {norm(c) for c in re.findall(r"if \((.+?)\) \{", body) if "stop" not in c}
    widget |= {norm(c) for c in re.findall(r"const systemValve = (.+?);", body)}
    assert plc == widget


def test_alert_log_widget_uses_the_ids_rules_and_severities():
    with open(os.path.join(ROOT, "software", "ids", "rules.py"), encoding="utf-8") as f:
        rules = f.read()
    severity = {"SEVERITY_LOW": "low", "SEVERITY_MEDIUM": "medium", "SEVERITY_HIGH": "high", "SEVERITY_CRITICAL": "critical"}
    real = {name: severity[sev] for name, sev in
            re.findall(r'"rule": "(\w+)",\s*"severity": (SEVERITY_\w+)', rules)}
    with open(os.path.join(LANDING, "static", "js", "theory-widgets.js"), encoding="utf-8") as f:
        js = f.read()
    log = js.split("const ALERT_LOG = [", 1)[1].split("];", 1)[0]
    rows = re.findall(r"\['[\d:]+', '(\w+)', '(\w+)'", log)
    assert len(rows) >= 10
    for sev, rule in rows:
        assert rule in real, f"{rule} is not an IDS rule"
        assert real[rule] == sev, f"{rule} is {real[rule]} in rules.py, {sev} in the widget"


def test_rate_planner_uses_the_ids_thresholds():
    with open(os.path.join(ROOT, "software", "ids", "rules.py"), encoding="utf-8") as f:
        rules = f.read()
    real = {name: int(value) for name, value in re.findall(r"self\.(\w+) = (\d+)", rules)}
    with open(os.path.join(LANDING, "static", "js", "theory-widgets.js"), encoding="utf-8") as f:
        js = f.read()
    planned = dict(re.findall(r"\{ rule: '(\w+)', n: (\d+), w: \d+ \}", js))
    windows = dict(re.findall(r"\{ rule: '(\w+)', n: \d+, w: (\d+) \}", js))
    assert int(planned["modbus_unauth_write"]) == real["MODBUS_WRITE_THRESHOLD"]
    assert int(windows["modbus_unauth_write"]) == real["MODBUS_WRITE_WINDOW"]
    assert int(planned["modbus_flood"]) == real["MODBUS_FLOOD_THRESHOLD"]
    assert int(windows["modbus_flood"]) == real["MODBUS_FLOOD_WINDOW"]
    # Both rate widgets keep a rule quiet for the IDS cooldown after it fires.
    assert f"const COOLDOWN = {real['ALERT_COOLDOWN']};" in js
    assert f"x - last >= {real['ALERT_COOLDOWN']}" in js


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_deep_dives_are_not_nested(topic):
    """Reading time leaves deep dives out with a non-greedy match; a nested one would confuse it."""
    for dive in re.findall(r'<details class="deep-dive"[^>]*>(.*?)</details>', article(topic), re.S):
        assert "<details" not in dive, f"{topic['id']}: nested <details> in a deep dive"


# ---- Facts in the prose, checked against the code ----

def compose_services():
    """Service -> {"ip": ..., "ports": {...}} from the virtual testbed's compose file."""
    with open(os.path.join(ROOT, ".devcontainer", "virtual", "docker-compose.yml"), encoding="utf-8") as f:
        lines = f.read().splitlines()
    services, current, in_services = {}, None, False
    for line in lines:
        if re.match(r"^services:", line):
            in_services = True
            continue
        if in_services and re.match(r"^\S", line):
            in_services = False
        if not in_services:
            continue
        start = re.match(r"^  ([\w-]+):\s*(#.*)?$", line)
        if start:
            current = services.setdefault(start.group(1), {"ip": None, "ports": set()})
            continue
        if current is None:
            continue
        ip = re.search(r"ipv4_address:\s*([\d.]+)", line)
        if ip:
            current["ip"] = ip.group(1)
        port = re.match(r'^\s+- "?(\d+):(\d+)', line)
        if port:
            current["ports"].add(int(port.group(2)))
    return {name: s for name, s in services.items() if s["ip"]}


def table_rows(text):
    for line in text.splitlines():
        if line.startswith("|") and not re.match(r"^\|[\s|:-]+\|?$", line):
            yield [cell.strip() for cell in line.strip().strip("|").split("|")]


def services_named(row, services):
    text = " ".join(row).lower()
    return [name for name in services if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", text)]


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_address_and_port_tables_match_the_compose_file(topic):
    services = compose_services()
    for row in table_rows(article(topic)):
        named = services_named(row, services)
        if len(named) != 1:
            continue
        service = services[named[0]]
        for ip in re.findall(r"172\.18\.0\.\d+", " ".join(row)):
            assert ip == service["ip"], f"{topic['id']}: {named[0]} is at {service['ip']}, the table says {ip}"
        first = re.fullmatch(r"`?(\d+(?:,\s*\d+)*)`?", row[0])
        if first:
            for port in map(int, re.findall(r"\d+", first.group(1))):
                assert port in service["ports"], f"{topic['id']}: {named[0]} has no port {port} ({sorted(service['ports'])})"


def test_networking_lesson_lists_every_lab_host():
    services = compose_services()
    text = article(next(t for t in TOPICS if t["id"] == "networking"))
    for name, service in services.items():
        assert service["ip"] in text, f"networking.md does not list {name} at {service['ip']}"


# rule name -> the attributes of software/ids/rules.py that set its threshold and window
RATE_RULE_ATTRS = {
    "port_scan": ("PORT_SCAN_THRESHOLD", "PORT_SCAN_WINDOW"),
    "syn_flood": ("SYN_FLOOD_THRESHOLD", "SYN_FLOOD_WINDOW"),
    "modbus_flood": ("MODBUS_FLOOD_THRESHOLD", "MODBUS_FLOOD_WINDOW"),
    "modbus_unauth_write": ("MODBUS_WRITE_THRESHOLD", "MODBUS_WRITE_WINDOW"),
    "http_brute_force": ("HTTP_BRUTE_THRESHOLD", "HTTP_BRUTE_WINDOW"),
}


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_ids_rule_tables_match_rules_py(topic):
    with open(os.path.join(ROOT, "software", "ids", "rules.py"), encoding="utf-8") as f:
        rules = f.read()
    value = {name: int(v) for name, v in re.findall(r"self\.(\w+) = (\d+)", rules)}
    severity = {name: sev.split("_")[1].lower() for name, sev in
                re.findall(r'"rule": "(\w+)",\s*"severity": (SEVERITY_\w+)', rules)}
    for row in table_rows(article(topic)):
        rule = re.fullmatch(r"`(\w+)`", row[0])
        if not rule or rule.group(1) not in severity:
            continue
        name, rest = rule.group(1), " ".join(row[1:])
        if name in RATE_RULE_ATTRS:
            numbers = set(map(int, re.findall(r"\d+", rest)))
            threshold, window = (value[a] for a in RATE_RULE_ATTRS[name])
            assert {threshold, window} <= numbers, f"{topic['id']}: {name} is {threshold} in {window} s, the table says {rest!r}"
        for word in ("low", "medium", "high", "critical"):
            if word in row[1:]:
                assert word == severity[name], f"{topic['id']}: {name} is {severity[name]}, the table says {word}"


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_before_you_start_points_back(topic):
    """What a lesson tells the reader to read first comes earlier on the path."""
    section = re.search(r"^## Before you start\n(.*?)(?=^## |\Z)", article(topic), re.S | re.M)
    if not section:
        return
    here = TOPIC_IDS.index(topic["id"])
    first = section.group(1).split("Later on the path:", 1)[0]
    for target in re.findall(r"\]\(/theory/([^)#\s]+)", first):
        assert TOPIC_IDS.index(target) < here, f"{topic['id']} asks to read {target} first, which comes later"


def test_lessons_match_what_http_brute_force_detects():
    """http_brute_force counts POSTs that mention one of _HTTP_LOGIN_WORDS.
    It once missed FUXA's /api/signin and the lessons said so; now it matches
    both login forms, and the lessons must not claim FUXA guessing is silent."""
    with open(os.path.join(ROOT, "software", "ids", "rules.py"), encoding="utf-8") as f:
        rules = f.read()
    words = re.search(r"_HTTP_LOGIN_WORDS = \(([^)]*)\)", rules).group(1)
    keywords = re.findall(r'b"(\w+)"', words)
    for path in ("/login", "/api/signin"):
        assert any(k in path for k in keywords), f"the rule no longer matches {path}; update the lessons"
    for topic in TOPICS:
        for row in table_rows(article(topic)):
            text = " ".join(row)
            if "http_brute_force" in text and ("1881" in text or "FUXA" in text):
                assert "signin" in text and "does not" not in text, f"{topic['id']}: {text}"
    with open(os.path.join(LANDING, "static", "js", "theory-widgets.js"), encoding="utf-8") as f:
        fuxa = re.search(r"\{ id: 'fuxa',.*?ids: '((?:[^'\\]|\\.)*)' \}", f.read(), re.S).group(1)
    assert "raises http_brute_force" in fuxa, fuxa


MAX_MINUTES = 8


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_lesson_reads_in_eight_minutes(topic):
    """The main text, as the page renders and times it, stays within the
    limit in AUTHORING.md; deep dives are optional and do not count."""
    import sys
    sys.path.insert(0, LANDING)
    from modules.theory_manager import TheoryManager
    rendered = TheoryManager._render_article(None, os.path.join(ROOT, topic["content"]))
    assert rendered["minutes"] <= MAX_MINUTES, f"{topic['id']}: {rendered['minutes']} min of main text"


def test_port_502_allowlists_keep_every_modbus_client():
    """Three services read or write the PLC over Modbus: hwio, FUXA and the
    OPC-UA server (opcua.py reads from openplc:502). Advice that allows port
    502 only from some of them would break the others."""
    with open(os.path.join(ROOT, "software", "opcua", "opcua.py"), encoding="utf-8") as f:
        assert re.search(r'ModbusTcpClient\(host="openplc",\s*port=502\)', f.read())
    for topic in TOPICS:
        def strings(value):
            if isinstance(value, str):
                yield value
            elif isinstance(value, dict):
                for v in value.values():
                    yield from strings(v)
            elif isinstance(value, list):
                for v in value:
                    yield from strings(v)
        for text in [article(topic), *strings(sidecar(topic))]:
            for sentence in re.split(r"(?<=[.!?])\s+|\n", text):
                if "502" not in sentence or not re.search(r"\b(allow|firewall|reach|lets?)\b", sentence, re.I):
                    continue
                if re.search(r"\bonly\b", sentence, re.I) and re.search(r"hwio", sentence, re.I) and re.search(r"fuxa", sentence, re.I):
                    assert re.search(r"opc-?ua|172\.18\.0\.5", sentence, re.I), f"{topic['id']}: {sentence.strip()}"
    with open(os.path.join(LANDING, "static", "js", "theory-widgets.js"), encoding="utf-8") as f:
        flows = re.findall(r"\{ src: '(\w+)', port: 502, what: '[^']*', needed: true \}", f.read())
    assert set(flows) == {"hwio", "fuxa", "opcua"}


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_lesson_links_use_one_name(topic):
    """A link that opens a list item names the lesson by its title, and the
    defence lesson is never linked under an older name."""
    titles = {t["id"]: t["title"] for t in TOPICS}
    text = article(topic)
    for link_text, target in re.findall(r"^\s*- \[([^\]]+)\]\(/theory/([^)#\s]+)\)", text, re.M):
        assert link_text == titles[target], f"{topic['id']}: [{link_text}] for {titles[target]!r}"
    assert not re.search(r"\[(Defen[cs]e and hardening|Defense in depth)\]\(/theory/defense-hardening\)", text), topic["id"]


@pytest.mark.parametrize("topic", TOPICS, ids=TOPIC_IDS)
def test_questions_do_not_repeat_the_select_all_hint(topic):
    """The page adds "Select all that apply." to every multi question itself."""
    data = sidecar(topic)
    for question in data.get("quiz", []) + data.get("checkpoints", []):
        assert "select all" not in question["question"].lower(), f"{topic['id']}: {question['question']}"


def test_glossary_links_lead_to_a_lesson():
    """A term's "Read more" opens the lesson that teaches it, not a challenge."""
    for entry in load_json(GLOSSARY):
        link = entry.get("link")
        if link:
            assert link.startswith("/theory/"), f"{entry['term']}: {link}"
            assert link.split("/theory/", 1)[1].split("#")[0] in TOPIC_IDS, f"{entry['term']}: {link}"


@pytest.mark.parametrize("topic", [t for t in TOPICS if t.get("core")], ids=[t["id"] for t in TOPICS if t.get("core")])
def test_core_lessons_stay_short(topic):
    """The core path is the first thing a beginner reads: seven minutes at most."""
    import sys
    sys.path.insert(0, LANDING)
    from modules.theory_manager import TheoryManager
    rendered = TheoryManager._render_article(None, os.path.join(ROOT, topic["content"]))
    assert rendered["minutes"] <= 7, f"{topic['id']}: {rendered['minutes']} min of main text"


@pytest.mark.parametrize("topic", [t for t in TOPICS if t.get("core")], ids=[t["id"] for t in TOPICS if t.get("core")])
def test_core_lessons_end_with_three_short_takeaways(topic):
    """The recap of a core lesson compresses it: three short sentences."""
    takeaways = sidecar(topic)["takeaways"]
    assert len(takeaways) == 3, topic["id"]
    for line in takeaways:
        assert len(line.split()) <= 22, f"{topic['id']}: {line}"


def test_one_name_for_the_valve_and_the_flood_challenge():
    """Beginners take two spellings for two things. Display strings quoted in
    backticks (the LCD's `Danger! BlowOut`) are left as the device shows them."""
    paths = [os.path.join(ROOT, t["content"]) for t in TOPICS] + [sidecar_path(t) for t in TOPICS]
    paths += [GLOSSARY, os.path.join(LANDING, "static", "js", "theory-widgets.js")]
    for path in paths:
        with open(path, encoding="utf-8") as f:
            text = re.sub(r"`[^`\n]*`", "", f.read())
        assert not re.search(r"\b[Bb]lowout\b(?!\")", text), f"{path}: write blow-out"
        assert not re.search(r"\b[Ff]lood and overwrite\b", text), f"{path}: write Flood & Overwrite"


def test_glossary_links_lead_to_a_lesson_that_uses_the_term():
    by_id = {t["id"]: t for t in TOPICS}
    for entry in load_json(GLOSSARY):
        link = entry.get("link", "")
        if not link.startswith("/theory/"):
            continue
        text = article(by_id[link.split("/theory/", 1)[1].split("#")[0]]).lower()
        names = [entry["term"], *entry.get("aliases", [])]
        assert any(name.lower() in text for name in names), f"{entry['term']}: {link} never mentions it"


def test_ids_threshold_widget_states_the_real_rules():
    with open(os.path.join(ROOT, "software", "ids", "rules.py"), encoding="utf-8") as f:
        real = {name: int(v) for name, v in re.findall(r"self\.(\w+) = (\d+)", f.read())}
    with open(os.path.join(LANDING, "static", "js", "theory-widgets.js"), encoding="utf-8") as f:
        js = f.read()
    assert f"N = {real['MODBUS_WRITE_THRESHOLD']}, W = {real['MODBUS_WRITE_WINDOW']} s (modbus_unauth_write)" in js
    assert f"N = {real['MODBUS_FLOOD_THRESHOLD']}, W = {real['MODBUS_FLOOD_WINDOW']} s (modbus_flood)" in js
    # The flood lesson starts the widget on the flood rule.
    text = article(next(t for t in TOPICS if t["id"] == "flood_overwrite"))
    mount = re.search(r'<div data-widget="ids-threshold"([^>]*)>', text).group(1)
    assert f'data-n="{real["MODBUS_FLOOD_THRESHOLD"]}"' in mount and f'data-w="{real["MODBUS_FLOOD_WINDOW"]}"' in mount
