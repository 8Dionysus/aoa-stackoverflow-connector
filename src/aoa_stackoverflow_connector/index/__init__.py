"""Tiny local keyword index for StackOverflow starter evidence."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path


TOKEN_RE = re.compile(r"[0-9A-Za-z]+(?:[._/\-][0-9A-Za-z]+)*")
PYTHON_ALIAS_PATTERNS = (
    (re.compile(r"\bdatetime\.now\(\s*timezone\.utc\s*\)", re.I), "datetime.now(timezone.utc)"),
    (re.compile(r"\bdatetime\.now\(\s*UTC\s*\)", re.I), "datetime.now(utc)"),
    (re.compile(r"\bdatetime\.utcnow\s*\(", re.I), "datetime.utcnow"),
    (re.compile(r"\breplace\(\s*tzinfo\s*=", re.I), "replace(tzinfo=...)"),
    (re.compile(r"\boffset[-\s]?naive\b", re.I), "offset-naive"),
    (re.compile(r"\boffset[-\s]?aware\b", re.I), "offset-aware"),
)


def tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in TOKEN_RE.findall(text) if len(token) > 1]
    for alias in technical_alias_tokens(text):
        if alias not in tokens:
            tokens.append(alias)
    return tokens


def technical_alias_tokens(text: str) -> list[str]:
    aliases: list[str] = []
    for pattern, alias in PYTHON_ALIAS_PATTERNS:
        if pattern.search(text):
            _append_unique(aliases, alias.lower())
    return aliases


def extract_exact_terms(tokens: list[str]) -> list[str]:
    exact_terms: list[str] = []
    for token in tokens:
        if _is_exact_term(token) and token not in exact_terms:
            exact_terms.append(token)
    return exact_terms


def build_keyword_index(normalized_dir: Path, output_dir: Path, profile_id: str = "python-datetime-timezone") -> Path:
    docs: list[dict[str, object]] = []
    inverted: dict[str, list[dict[str, object]]] = defaultdict(list)
    exact: dict[str, list[str]] = defaultdict(list)
    for topic_path in sorted(normalized_dir.glob("topic-*.json")):
        topic = json.loads(topic_path.read_text(encoding="utf-8"))
        title = str(topic.get("title", ""))
        for item in topic.get("evidence_items", []):
            if not isinstance(item, dict):
                continue
            text = str(item.get("text") or "")
            doc_id = str(item.get("item_id"))
            tags = [str(tag) for tag in item.get("tags", [])]
            search_text = f"{title} {' '.join(tags)} {item.get('item_kind')} {text}".strip()
            tokens = tokenize(search_text)
            counts = Counter(tokens)
            exact_terms = extract_exact_terms(tokens)
            docs.append(
                {
                    "doc_id": doc_id,
                    "topic_id": topic.get("topic_id"),
                    "question_id": item.get("question_id"),
                    "answer_id": item.get("answer_id"),
                    "comment_id": item.get("comment_id"),
                    "linked_question_id": item.get("linked_question_id"),
                    "item_id": item.get("item_id"),
                    "item_kind": item.get("item_kind"),
                    "source_url": item.get("source_url"),
                    "created_at": item.get("created_at"),
                    "last_edit_at": item.get("last_edit_at"),
                    "captured_at": item.get("captured_at"),
                    "title": title,
                    "tags": tags,
                    "score": item.get("score"),
                    "stackoverflow": item.get("stackoverflow", {}),
                    "text": text,
                    "exact_text": " ".join(tokens),
                    "exact_terms": exact_terms,
                    "tokens": sum(counts.values()),
                }
            )
            for token, count in counts.items():
                inverted[token].append({"doc_id": doc_id, "count": count})
            for token in exact_terms:
                exact[token].append(doc_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "keyword_index.json"
    payload = {
        "schema": "aoa_stackoverflow_keyword_index_v1",
        "profile_id": profile_id,
        "unit": "evidence_item",
        "built_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "doc_count": len(docs),
        "term_count": len(inverted),
        "docs": docs,
        "inverted": inverted,
        "exact": exact,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _is_exact_term(token: str) -> bool:
    return any(char.isdigit() for char in token) or any(separator in token for separator in [".", "_", "/", "-", "(", ")"])


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)
