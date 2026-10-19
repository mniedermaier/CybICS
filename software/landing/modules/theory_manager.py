"""
Theory Path management: illustrated, interactive background reading.

A JSON config orders the topics into sections. Each topic is a Markdown
article (which may contain inline SVG diagrams and widget placeholders) plus a
sidecar JSON with its objectives, takeaways, checkpoints and quiz, see
training/theory/AUTHORING.md.

Articles are rendered once per change of the file and sanitised with nh3, so
a page can only ever carry markup from the allowlist below: no scripts, no
event handlers. Their <style> blocks are lifted out before sanitising and put
back into the page head; tests/test_theory_content.py makes sure every
selector in them is scoped to the article's own figure.

Quiz progress is kept on the board, next to the CTF progress, rather than in
the browser: a student who changes browsers or clears site data keeps it.
"""
import json
import math
import os
import re
import threading
import time

import markdown
import nh3

from utils.logger import logger
from utils.config import (
    THEORY_CONFIG_FILE, THEORY_PROGRESS_FILE, THEORY_GLOSSARY_FILE,
    THEORY_PASS_RATIO, PLC_HOST, PLC_MODBUS_PORT)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Students read slower than the 200-250 wpm usually quoted, and these pages
# are technical. Each figure and widget asks for some time of its own.
WORDS_PER_MINUTE = 170
MINUTES_PER_FIGURE = 0.5

_SVG_TAGS = {
    'svg', 'g', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline',
    'polygon', 'text', 'tspan', 'defs', 'marker', 'clippath', 'title', 'desc',
    'use', 'lineargradient', 'radialgradient', 'stop', 'pattern', 'symbol',
}
_HTML_TAGS = {
    'figure', 'figcaption', 'details', 'summary', 'div', 'span', 'section',
    'abbr', 'kbd', 'mark', 'sup', 'sub', 'small',
}
# SVG names are case-sensitive and nh3 compares them as written, so the
# camelCase spellings must be listed as such: a lower-case 'viewbox' alone
# silently strips every viewBox and the figures lose their scaling.
_SVG_CAMEL_TAGS = {'clipPath', 'linearGradient', 'radialGradient'}
ALLOWED_TAGS = set(nh3.ALLOWED_TAGS) | _SVG_TAGS | _SVG_CAMEL_TAGS | _HTML_TAGS
_SVG_ATTRIBUTES = {
    'viewbox', 'xmlns', 'width', 'height', 'x', 'y', 'x1', 'x2', 'y1', 'y2',
    'cx', 'cy', 'r', 'rx', 'ry', 'd', 'points', 'transform', 'fill',
    'fill-opacity', 'stroke', 'stroke-width', 'stroke-opacity',
    'stroke-dasharray', 'stroke-dashoffset', 'stroke-linecap',
    'stroke-linejoin', 'opacity', 'font-family', 'font-size', 'font-weight',
    'font-style', 'text-anchor', 'dominant-baseline', 'letter-spacing',
    'marker-end', 'marker-start', 'markerwidth', 'markerheight', 'orient',
    'refx', 'refy', 'clip-path', 'pathlength', 'offset', 'stop-color',
    'stop-opacity', 'gradientunits', 'preserveaspectratio', 'dx', 'dy',
    'href', 'patternunits',
    'viewBox', 'markerWidth', 'markerHeight', 'refX', 'refY', 'pathLength',
    'gradientUnits', 'preserveAspectRatio', 'patternUnits',
}
ALLOWED_ATTRIBUTES = {
    '*': {'class', 'id', 'role', 'aria-label', 'aria-hidden', 'style', 'title',
          'lang'} | _SVG_ATTRIBUTES,
    'a': {'href', 'title'},
    'img': {'src', 'alt', 'width', 'height'},
    'td': {'colspan', 'rowspan', 'align'},
    'th': {'colspan', 'rowspan', 'align', 'scope'},
    'details': {'open'},
    'ol': {'start'},
}

_STYLE_BLOCK = re.compile(r'<style>(.*?)</style>', re.S | re.I)
_UNSAFE_CSS = re.compile(r'@import|url\s*\(|expression\s*\(|</', re.I)


def _count_words(html):
    text = re.sub(r'<(svg|style|pre)\b.*?</\1>', ' ', html, flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    return len(re.findall(r"[\w'’-]+", text))


class _Cached:
    """A value derived from one file, rebuilt only when the file changes."""

    def __init__(self, build):
        self._build = build
        self._entries = {}
        self._lock = threading.Lock()

    def get(self, path):
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = None
        with self._lock:
            entry = self._entries.get(path)
            if entry and entry[0] == mtime:
                return entry[1]
        value = self._build(path) if mtime is not None else None
        with self._lock:
            self._entries[path] = (mtime, value)
        return value


class TheoryManager:
    def __init__(self):
        self.config = self._load_json(THEORY_CONFIG_FILE, {"sections": {}})
        self.sections = self.config.get('sections', {})
        self.topics = []
        for section_id, section in self.sections.items():
            for topic in section.get('topics', []):
                self.topics.append({**topic, 'section_id': section_id})
        for number, topic in enumerate(self.topics, start=1):
            topic['number'] = number
        self._by_id = {t['id']: t for t in self.topics}
        self._articles = _Cached(self._render_article)
        self._sidecars = _Cached(lambda p: self._load_json(p, {}))
        self._glossary = _Cached(lambda p: self._load_json(p, []))
        self.progress = ProgressStore(THEORY_PROGRESS_FILE)
        logger.info(f"TheoryManager initialized with {len(self.topics)} topics")

    @staticmethod
    def _load_json(path, default):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Theory file not found: {path}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing {path}: {e}")
        return default

    # ---- Topics ----

    def get_topic(self, topic_id):
        topic = self._by_id.get(topic_id)
        if not topic:
            return None, None
        return topic, self.sections[topic['section_id']]

    def neighbours(self, topic_id):
        index = self.topics.index(self._by_id[topic_id])
        before = self.topics[index - 1] if index > 0 else None
        after = self.topics[index + 1] if index + 1 < len(self.topics) else None
        return before, after

    def _path(self, relative):
        return os.path.join(BASE_DIR, relative)

    def sidecar(self, topic):
        path = self._path(topic['content'][:-3] + '.json')
        return self._sidecars.get(path) or {}

    def article(self, topic):
        """The rendered article: head (the title), body, css, toc, minutes. Never None."""
        rendered = self._articles.get(self._path(topic.get('content', '')))
        if rendered is None:
            logger.warning(f"Theory content not found: {topic.get('content')}")
            return {'head': '', 'body': '<p><em>This lesson is not available.</em></p>',
                    'css': '', 'toc': [], 'minutes': 1}
        return rendered

    def overview(self):
        """Per-topic data for the overview cards, in path order."""
        cards = {}
        for topic in self.topics:
            sidecar = self.sidecar(topic)
            cards[topic['id']] = {
                'number': topic['number'],
                'minutes': self.article(topic)['minutes'],
                'level': sidecar.get('level', 'beginner'),
                'questions': len(sidecar.get('quiz', [])),
            }
        return cards

    def glossary(self):
        return self._glossary.get(THEORY_GLOSSARY_FILE) or []

    # ---- Rendering ----

    def _render_article(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()

        css = []
        for block in _STYLE_BLOCK.findall(source):
            if _UNSAFE_CSS.search(block):
                logger.warning(f"Dropped an unsafe <style> block from {path}")
            else:
                css.append(block.strip())
        source = _STYLE_BLOCK.sub('', source)
        # Markdown inside these blocks is only parsed when md_in_html is told to.
        source = re.sub(r'<(details|summary|div|figcaption)(?![^>]*\bmarkdown=)([^>]*)>',
                        r'<\1\2 markdown="1">', source)

        md = markdown.Markdown(extensions=[
            'fenced_code', 'codehilite', 'tables', 'extra', 'md_in_html', 'toc'],
            extension_configs={'toc': {'toc_depth': '2-2'}})
        html = md.convert(source)
        html = nh3.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES,
                         generic_attribute_prefixes={'data-'},
                         link_rel='noopener noreferrer',
                         strip_comments=True)

        toc = [{'id': t['id'], 'name': t['name']} for t in md.toc_tokens]
        figures = html.count('<figure') + html.count('data-widget=')
        minutes = max(1, math.ceil(_count_words(html) / WORDS_PER_MINUTE
                                   + figures * MINUTES_PER_FIGURE))
        # The template puts the learning objectives right under the title.
        head, sep, body = html.partition('</h1>')
        if not sep:
            head, body = '', html
        else:
            head += sep
        return {'head': head, 'body': body, 'css': '\n'.join(css), 'toc': toc,
                'minutes': minutes}


class ProgressStore:
    """Quiz results per topic, persisted as JSON on the landing data volume."""

    def __init__(self, path):
        self._path = path
        self._lock = threading.Lock()

    def load(self):
        try:
            with open(self._path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self, data):
        tmp = self._path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, self._path)

    def record(self, topic_id, correct, total):
        """Store one quiz attempt; the best score counts."""
        ratio = correct / total if total else 0.0
        with self._lock:
            data = self.load()
            entry = data.get(topic_id, {'best': 0.0, 'attempts': 0, 'passed': False})
            entry['attempts'] += 1
            entry['best'] = max(entry['best'], round(ratio, 3))
            entry['passed'] = entry['passed'] or ratio >= THEORY_PASS_RATIO
            entry['updated'] = int(time.time())
            data[topic_id] = entry
            self._save(data)
            return entry

    def reset(self):
        with self._lock:
            self._save({})


class PlantReader:
    """Read-only view of the plant as the PLC holds it, for the live widgets.

    One persistent Modbus connection, function codes 01 and 03 only: reads
    raise nothing in the IDS, and keeping the connection open avoids a SYN per
    poll. Results are shared for a short while, so several open pages cost the
    PLC one request.
    """

    MAX_AGE = 0.8

    def __init__(self, host=PLC_HOST, port=PLC_MODBUS_PORT):
        self._host, self._port = host, port
        self._client = None
        self._lock = threading.Lock()
        self._last = (float('-inf'), None)

    def _connect(self):
        from pymodbus.client import ModbusTcpClient
        if self._client is None:
            self._client = ModbusTcpClient(self._host, port=self._port, timeout=1, retries=0)
        if not self._client.connected:
            self._client.connect()
        return self._client

    def read(self):
        with self._lock:
            stamp, values = self._last
            # A failed read is shared too, so a PLC that is down costs one
            # connection timeout per MAX_AGE rather than one per open page.
            if time.monotonic() - stamp < self.MAX_AGE:
                return values
            try:
                client = self._connect()
                coils = client.read_coils(0, count=4, slave=1)
                regs = client.read_holding_registers(1124, count=11, slave=1)
                if coils.isError() or regs.isError():
                    raise IOError('Modbus error response')
                values = {
                    'heartbeat': bool(coils.bits[0]),
                    'compressor': bool(coils.bits[1]),
                    'systemValve': bool(coils.bits[2]),
                    'gstSig': bool(coils.bits[3]),
                    'gst': regs.registers[0],
                    'hpt': regs.registers[2],
                    'sysSen': regs.registers[8],
                    'boSen': regs.registers[10],
                }
            except Exception as e:
                logger.debug(f"Plant read failed: {e}")
                if self._client is not None:
                    self._client.close()
                self._last = (time.monotonic(), None)
                return None
            self._last = (time.monotonic(), values)
            return values
