"""
Theory Path management: structured background reading with inline diagrams.

Mirrors the CTF manager: a JSON config groups topics into sections, and each
topic renders a Markdown article (which may contain inline SVG diagrams) to
HTML. Read progress is tracked client-side, so there is no server state here.
"""
import json
import os
import re

import markdown

from utils.logger import logger
from utils.config import THEORY_CONFIG_FILE


class TheoryManager:
    def __init__(self):
        self.config = self._load_config()
        self.sections = self.config.get('sections', {})
        logger.info(f"TheoryManager initialized with {self._count()} topics")

    def _load_config(self):
        try:
            with open(THEORY_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Theory config not found: {THEORY_CONFIG_FILE}")
            return {"sections": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing theory config: {e}")
            return {"sections": {}}

    def _count(self):
        return sum(len(s.get('topics', [])) for s in self.sections.values())

    def get_topic(self, topic_id):
        for section in self.sections.values():
            for topic in section.get('topics', []):
                if topic['id'] == topic_id:
                    return topic, section
        return None, None

    def load_markdown_content(self, relative_path):
        if not relative_path:
            return ""
        full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content = re.sub(r'<details>', '<details markdown="1">', content)
            content = re.sub(r'<summary>', '<summary markdown="1">', content)
            return markdown.markdown(content, extensions=[
                'fenced_code', 'codehilite', 'tables', 'nl2br', 'extra', 'md_in_html'])
        except FileNotFoundError:
            logger.warning(f"Theory content not found: {full_path}")
            return f"<p><em>Theory content not available at: {relative_path}</em></p>"
        except Exception as e:
            logger.error(f"Error loading theory content {full_path}: {e}")
            return f"<p><em>Error loading theory content: {e}</em></p>"
