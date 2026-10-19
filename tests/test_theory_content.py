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
            if labels:
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
        for target in re.findall(r"/theory/([a-z0-9_-]+)", entry.get("link", "")):
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
