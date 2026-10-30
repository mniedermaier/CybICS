"""The Theory Path (/theory) against the running landing page.

test_theory_content.py checks the sources; this checks what a student gets:
every lesson renders, the sanitiser keeps the figures and drops nothing that
teaches, the widgets have their scripts, and the live plant endpoint reads
the PLC. Nothing here records a quiz result, so a student's progress on the
board is left alone.
"""
import json
import os
import re

import pytest
import requests

from conftest import NGINX_PROXY_PORT, READ_TIMEOUT, SERVER_IP

pytestmark = pytest.mark.usefixtures("stack_ready")

BASE = f"http://{SERVER_IP}:{NGINX_PROXY_PORT}"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "software", "landing", "theory_config.json"), encoding="utf-8") as f:
    TOPICS = [t for s in json.load(f)["sections"].values() for t in s["topics"]]


def get(path, **kwargs):
    kwargs.setdefault("timeout", READ_TIMEOUT)
    return requests.get(BASE + path, **kwargs)


def article_of(html):
    match = re.search(r'<article class="article" id="article">(.*?)</article>\s*\n', html, re.S)
    assert match, "no article block"
    return match.group(1)


def test_overview_lists_every_lesson():
    page = get("/theory")
    assert page.status_code == 200
    for topic in TOPICS:
        assert f'href="/theory/{topic["id"]}"' in page.text, topic["id"]
    assert "/static/css/theory.css" in page.text


@pytest.mark.parametrize("topic", TOPICS, ids=[t["id"] for t in TOPICS])
def test_lesson_renders_with_its_parts(topic):
    page = get(f"/theory/{topic['id']}")
    assert page.status_code == 200
    html = page.text
    assert 'id="objectives"' in html and 'id="takeaways"' in html and 'id="quiz"' in html
    for asset in ("/static/js/theory.js", "/static/js/theory-widgets.js"):
        assert asset in html

    article = article_of(html)
    assert "<script" not in article.lower()
    assert not re.search(r"\son[a-z]+\s*=", article)

    # The sanitiser must keep every figure, its accessible name and its
    # viewBox (a lower-cased "viewbox" would break the scaling).
    with open(os.path.join(ROOT, topic["content"]), encoding="utf-8") as f:
        source = f.read()
    # Instructor notes are cut out before rendering, figures and all.
    source = re.sub(r'<details class="instructor".*?</details>', "", source, flags=re.S)
    assert article.count("<svg") == source.count("<svg")
    assert article.count("viewBox=") == source.count("viewBox=")
    assert article.count("aria-label=") >= source.count("<svg")
    assert article.count("data-widget=") == source.count("data-widget=")


def test_quiz_answers_are_not_in_the_page():
    """The answers come back only from the grading endpoint, after an attempt."""
    for topic in TOPICS:
        html = get(f"/theory/{topic['id']}").text
        data = json.loads(re.search(r'<script type="application/json" id="theory-data">(.*?)</script>', html, re.S).group(1))
        assert data["quiz"], topic["id"]
        for question in data["quiz"]:
            assert set(question) <= {"type", "question", "options"}, topic["id"]


def test_instructor_notes_never_reach_the_page():
    for topic in TOPICS:
        with open(os.path.join(ROOT, topic["content"]), encoding="utf-8") as f:
            if 'class="instructor"' not in f.read():
                continue
        html = get(f"/theory/{topic['id']}").text
        assert 'class="instructor"' not in html, topic["id"]
        assert "Instructor notes" not in html, topic["id"]


def test_core_lessons_offer_the_core_path_onwards():
    core = [t for t in TOPICS if t.get("core")]
    html = get(f"/theory/{core[0]['id']}").text
    pager = html.split('id="pager-core"', 1)[1].split("</nav>", 1)[0]
    assert f'href="/theory/{core[1]["id"]}"' in pager


def test_lesson_links_onwards_and_to_its_challenges():
    first, second = TOPICS[0], TOPICS[1]
    html = get(f"/theory/{first['id']}").text
    assert f'href="/theory/{second["id"]}"' in html
    for related in first.get("related", []):
        assert f'href="/ctf/challenge/{related["id"]}"' in html
        # Inside the dashboard the link asks it to open the CTF view; a plain
        # link loaded the challenge into the Theory view, where its Back
        # button switched to a hidden CTF view and seemed to do nothing.
        assert f"postMessage({{ type: 'navigate', url: '/ctf/challenge/{related['id']}' }}" in html


def test_paired_challenges_are_labelled():
    """An attack's briefing names its defence, a defence's briefing the attacks it stops."""
    for topic in TOPICS:
        paired = [r for r in topic.get("related", []) if r.get("role")]
        if not paired:
            continue
        html = get(f"/theory/{topic['id']}").text
        box = html[html.index("Put it into practice"):]
        box = box[:box.index("</section>")]
        for related in paired:
            label = "Defend it:" if related["role"] == "defense" else "Stops:"
            link = re.search(r'<a [^>]*href="/ctf/challenge/%s"[^>]*>(.*?)</a>' % re.escape(related["id"]), box, re.S)
            assert link and label in link.group(1), f"{topic['id']}: {related['id']}"


def test_challenge_back_button_asks_for_the_previous_view():
    """The dashboard sends Back to the lesson a challenge was opened from."""
    html = get("/ctf/challenge/scanning").text
    assert "type:'navigate',url:'/ctf',back:true" in html


def test_unknown_lesson_is_404():
    assert get("/theory/no-such-lesson").status_code == 404


def test_static_assets_are_served():
    for asset in ("/static/css/theory.css", "/static/js/theory.js", "/static/js/theory-widgets.js"):
        assert get(asset).status_code == 200, asset


def test_glossary_page():
    page = get("/theory/glossary")
    assert page.status_code == 200
    assert "Programmable Logic Controller" in page.text


def test_live_plant_reads_the_plc():
    response = get("/theory/api/plant")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["ok"] is True
    values = data["values"]
    for key in ("gst", "hpt", "sysSen", "boSen"):
        assert isinstance(values[key], int) and 0 <= values[key] <= 65535, key
    for key in ("heartbeat", "compressor", "systemValve", "gstSig"):
        assert isinstance(values[key], bool), key


def test_progress_endpoint_rejects_bad_attempts():
    assert get("/theory/api/progress").status_code == 200
    url = BASE + "/theory/api/progress/"
    bad = requests.post(url + TOPICS[0]["id"], json={"answers": []}, timeout=READ_TIMEOUT)
    assert bad.status_code == 400
    with open(os.path.join(ROOT, TOPICS[0]["content"][:-3] + ".json"), encoding="utf-8") as f:
        count = len(json.load(f)["quiz"])
    garbage = requests.post(url + TOPICS[0]["id"], json={"answers": [[{"x": 1}]] * count}, timeout=READ_TIMEOUT)
    assert garbage.status_code == 400
    unknown = requests.post(url + "no-such-lesson", json={"answers": [0]}, timeout=READ_TIMEOUT)
    assert unknown.status_code == 404


def test_theme_setting_says_whether_it_was_chosen():
    data = get("/api/settings/theme").json()
    assert data["theme"] in ("light", "dark")
    assert data["explicit"] is False


def test_theme_setting_can_return_to_the_system_preference():
    """Settings > Appearance stores light or dark, and 'system' forgets the choice."""
    browser = requests.Session()
    url = BASE + "/api/settings/theme"
    assert browser.post(url, json={"theme": "light"}, timeout=READ_TIMEOUT).ok
    assert browser.get(url, timeout=READ_TIMEOUT).json() == {"theme": "light", "explicit": True}
    assert browser.post(url, json={"theme": "system"}, timeout=READ_TIMEOUT).ok
    assert browser.get(url, timeout=READ_TIMEOUT).json()["explicit"] is False
    assert browser.post(url, json={"theme": "<script>"}, timeout=READ_TIMEOUT).status_code == 400
