"""The CTF overview (/ctf): the learning path, difficulty, briefings and pairs.

ctf_config.json orders the challenges the way a student with little IT/OT
background should meet them: seven stages from the plant to its defense, easy
to hard inside each stage. The overview, training/README.md and CybICS-mgmt
(which imports the file and keeps its order as each challenge's position)
all follow that order, so it is pinned here. Points follow the difficulty, so
a score means the same everywhere.

Every challenge names its Theory Path briefing ("theory"); an attack names
the defense challenge that stops it ("defended_by"), and the overview shows
the reverse on the defense.

Most of this needs no stack. The last test renders /ctf on the live landing
page and reads nothing but the page.
"""
import json
import os
import re

import pytest
import requests

from conftest import NGINX_PROXY_PORT, READ_TIMEOUT, SERVER_IP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANDING = os.path.join(ROOT, "software", "landing")

with open(os.path.join(LANDING, "ctf_config.json"), encoding="utf-8") as f:
    CONFIG = json.load(f)
with open(os.path.join(LANDING, "theory_config.json"), encoding="utf-8") as f:
    TOPICS = {t["id"]: t for s in json.load(f)["sections"].values() for t in s["topics"]}

CATEGORIES = CONFIG["categories"]
CHALLENGES = [c for cat in CATEGORIES.values() for c in cat["challenges"]]
BY_ID = {c["id"]: c for c in CHALLENGES}

STAGES = ["plant_basics", "recon", "access_attacks", "process_attacks", "detection", "forensics", "defense"]
POINTS = {"easy": 100, "medium": 200, "hard": 300}


def test_stages_follow_the_learning_path():
    assert list(CATEGORIES) == STAGES
    for key, cat in CATEGORIES.items():
        assert cat.get("name") and cat.get("description"), key


def test_stages_are_balanced():
    sizes = {key: len(cat["challenges"]) for key, cat in CATEGORIES.items()}
    assert all(3 <= n <= 8 for n in sizes.values()), sizes


def test_every_challenge_is_on_the_path_once():
    ids = [c["id"] for c in CHALLENGES]
    assert len(ids) == len(set(ids))
    # The dashboard's first-run prompt points at the first challenge
    assert ids[0] == "physical_process"


@pytest.mark.parametrize("challenge", CHALLENGES, ids=[c["id"] for c in CHALLENGES])
def test_points_follow_the_difficulty(challenge):
    assert challenge.get("difficulty") in POINTS, challenge["id"]
    assert challenge["points"] == POINTS[challenge["difficulty"]], challenge["id"]


@pytest.mark.parametrize("stage", STAGES)
def test_a_stage_goes_from_easy_to_hard(stage):
    rank = [list(POINTS).index(c["difficulty"]) for c in CATEGORIES[stage]["challenges"]]
    assert rank == sorted(rank), [c["id"] for c in CATEGORIES[stage]["challenges"]]


def test_defense_challenges_close_the_path():
    assert {c.get("type") for c in CATEGORIES["defense"]["challenges"]} == {"defense"}
    others = [c["id"] for key, cat in CATEGORIES.items() if key != "defense"
              for c in cat["challenges"] if c.get("type") == "defense"]
    assert not others


@pytest.mark.parametrize("challenge", CHALLENGES, ids=[c["id"] for c in CHALLENGES])
def test_briefing_is_a_lesson_that_links_back(challenge):
    topic = TOPICS.get(challenge.get("theory"))
    assert topic, f"{challenge['id']}: no Theory Path lesson {challenge.get('theory')!r}"
    assert challenge["id"] in [r["id"] for r in topic.get("related", [])], \
        f"{challenge['id']}: lesson {topic['id']} does not link back"


ATTACKS = [c for c in CHALLENGES if c.get("defended_by")]


@pytest.mark.parametrize("attack", ATTACKS, ids=[c["id"] for c in ATTACKS])
def test_an_attack_is_paired_with_a_defense(attack):
    for defense in attack["defended_by"]:
        assert BY_ID.get(defense, {}).get("type") == "defense", f"{attack['id']}: {defense}"


def test_the_side_doors_are_paired_both_ways():
    """The four side doors and the one defense that closes them all."""
    side_doors = {"s7_sidedoor", "s7_cpu_stop", "openplc_restapi", "dnp3_sidedoor"}
    closers = {c["id"] for c in CHALLENGES if "defense_unused_protocols" in c.get("defended_by", [])}
    assert closers == side_doors
    readme = os.path.join(ROOT, "training", "defense_unused_protocols", "README.md")
    with open(readme, encoding="utf-8") as f:
        text = f.read()
    for attack in side_doors:
        attack_dir = BY_ID[attack]["training_content"].split("/")[1]
        assert f"../{attack_dir}/README.md" in text, attack
        with open(os.path.join(ROOT, BY_ID[attack]["training_content"]), encoding="utf-8") as f:
            assert "../defense_unused_protocols/README.md" in f.read(), f"{attack} does not link forward"


def test_training_readme_lists_the_modules_in_path_order():
    with open(os.path.join(ROOT, "training", "README.md"), encoding="utf-8") as f:
        text = f.read()
    modules = text[text.index("## 📚 Training Modules"):]
    listed = re.findall(r"^\d+\. \[[^\]]+\]\(([A-Za-z0-9_]+)/README\.md\)", modules, re.M)
    expected = []
    for c in CHALLENGES:
        d = c["training_content"].split("/")[1]
        if d not in expected:
            expected.append(d)
    assert listed == expected
    headings = re.findall(r"^### (.+)$", modules.split("\n---\n")[0], re.M)
    assert headings == [cat["name"] for cat in CATEGORIES.values()]


@pytest.mark.usefixtures("stack_ready")
def test_overview_shows_the_path_briefings_and_pairs():
    html = requests.get(f"http://{SERVER_IP}:{NGINX_PROXY_PORT}/ctf", timeout=READ_TIMEOUT).text
    sections = re.findall(r'<section class="stage[^"]*" data-category="([a-z_]+)"', html)
    assert sections == STAGES
    shown = re.findall(r'<article class="challenge-card[^"]*"\s+id="ch-([A-Za-z0-9_]+)"', html)
    assert shown == [c["id"] for c in CHALLENGES]
    for c in CHALLENGES:
        card = html[html.index(f'id="ch-{c["id"]}"'):]
        card = card[:card.index("</article>")]
        assert f'data-difficulty="{c["difficulty"]}"' in card, c["id"]
        assert f'href="/theory/{c["theory"]}" data-nav="theory"' in card, c["id"]
        for defense in c.get("defended_by", []):
            assert f'href="/ctf/challenge/{defense}" data-nav="ctf"' in card, c["id"]
    side = html[html.index('id="ch-defense_unused_protocols"'):]
    side = side[:side.index("</article>")]
    for attack in ("s7_sidedoor", "s7_cpu_stop", "openplc_restapi", "dnp3_sidedoor"):
        assert f'href="/ctf/challenge/{attack}"' in side, attack
    assert html.count('class="next-badge"') <= 1
