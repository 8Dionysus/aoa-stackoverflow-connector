"""Parse tiny Stack Exchange API-shaped StackOverflow question bundles."""

from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


TAG_RE = re.compile(r"<[^>]+>")


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, _attrs: list[tuple[str, str | None]]) -> None:
        if self.skip_depth or tag.lower() in {"script", "style"}:
            self.skip_depth += 1
        elif tag.lower() in {"p", "br", "li", "pre", "code"}:
            self.parts.append(" ")

    def handle_endtag(self, _tag: str) -> None:
        if self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = data.strip()
        if text:
            self.parts.append(text)

    def get_text(self) -> str:
        return clean_text(" ".join(self.parts))


def load_question_bundle(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("StackOverflow fixture bundle must be a JSON object")
    if not isinstance(payload.get("questions"), list):
        raise ValueError("StackOverflow fixture bundle must contain a questions list")
    return payload


def extract_questions(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for raw_question in bundle.get("questions", []):
        if not isinstance(raw_question, dict):
            continue
        question = dict(raw_question)
        question["body_text"] = html_to_text(str(question.get("body_html") or question.get("body") or ""))
        question["comments"] = [_parse_comment(comment) for comment in question.get("comments", []) if isinstance(comment, dict)]
        question["answers"] = [_parse_answer(answer) for answer in question.get("answers", []) if isinstance(answer, dict)]
        question["linked_questions"] = [
            _parse_linked_question(linked) for linked in question.get("linked_questions", []) if isinstance(linked, dict)
        ]
        questions.append(question)
    return questions


def bundle_id(bundle: dict[str, Any]) -> str:
    explicit = bundle.get("bundle_id")
    if explicit:
        return slug(str(explicit))
    questions = extract_questions(bundle)
    if questions:
        return f"question-{questions[0].get('question_id', 'fixture')}"
    return "stackoverflow-fixture"


def html_to_text(fragment: str) -> str:
    extractor = TextExtractor()
    extractor.feed(fragment)
    text = extractor.get_text()
    if text:
        return text
    return clean_text(TAG_RE.sub(" ", html.unescape(fragment)))


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def slug(value: str) -> str:
    lowered = value.casefold()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-") or "item"


def _parse_answer(answer: dict[str, Any]) -> dict[str, Any]:
    parsed = dict(answer)
    parsed["body_text"] = html_to_text(str(parsed.get("body_html") or parsed.get("body") or ""))
    parsed["comments"] = [_parse_comment(comment) for comment in parsed.get("comments", []) if isinstance(comment, dict)]
    return parsed


def _parse_comment(comment: dict[str, Any]) -> dict[str, Any]:
    parsed = dict(comment)
    parsed["body_text"] = html_to_text(str(parsed.get("body_html") or parsed.get("body") or ""))
    return parsed


def _parse_linked_question(linked: dict[str, Any]) -> dict[str, Any]:
    parsed = dict(linked)
    parsed["title_text"] = clean_text(str(parsed.get("title") or ""))
    return parsed
