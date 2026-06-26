"""Normalize StackOverflow question bundles into evidence items."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aoa_stackoverflow_connector.parse import bundle_id, extract_questions, load_question_bundle, slug


PYTHON_SYMBOL_RE = re.compile(r"\b(?:datetime|timezone|UTC|utcnow|tzinfo|astimezone|replace|pytz|zoneinfo)\b", re.I)
CALL_RE = re.compile(r"\bdatetime\.(?:now|utcnow|fromtimestamp)\([^)]*\)|\b(?:replace|astimezone|localize)\([^)]*\)", re.I)
WARNING_TERMS = {
    "warning": "warning",
    "do not": "do_not",
    "avoid": "avoid",
    "deprecated": "deprecated",
    "naive": "naive_datetime",
    "aware": "aware_datetime",
    "loses": "lossy_conversion",
    "incorrect instant": "incorrect_instant",
}
CONTEXT_TERMS = {
    "python 3.11": "Python 3.11",
    "python 3.12": "Python 3.12",
    "python 3.13": "Python 3.13",
    "django": "Django",
    "pytz": "pytz",
    "zoneinfo": "zoneinfo",
    "utc": "UTC",
}


def normalize_snapshot(raw_path: Path, source_url: str, output_dir: Path) -> Path:
    bundle = load_question_bundle(raw_path)
    captured_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    topic_id = bundle_id(bundle)
    questions = [_normalize_question(question, captured_at) for question in extract_questions(bundle)]
    items = [item for question in questions for item in question["evidence_items"]]
    topic = {
        "schema": "aoa_stackoverflow_normalized_topic_v1",
        "topic_id": topic_id,
        "source_url": source_url,
        "title": str(bundle.get("title") or (questions[0]["title"] if questions else "StackOverflow fixture")),
        "site": bundle.get("site", "stackoverflow"),
        "captured_at": captured_at,
        "source_shape": {
            "kind": "stackexchange_question_bundle",
            "network_touched": False,
            "fixture_origin": bundle.get("fixture_origin"),
            "license_note": bundle.get("license_note"),
        },
        "questions": questions,
        "evidence_items": items,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"topic-{topic_id}.json"
    output_path.write_text(json.dumps(topic, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def extract_entities(text: str, *, tags: list[str] | None = None, item_kind: str = "evidence") -> list[dict[str, str]]:
    entities: list[dict[str, str]] = []
    lowered = text.casefold()
    for tag in tags or []:
        _add_entity(entities, "tag", str(tag))
    for match in PYTHON_SYMBOL_RE.finditer(text):
        _add_entity(entities, "python_symbol", _canonical_symbol(match.group(0)))
    for match in CALL_RE.finditer(text):
        _add_entity(entities, "api_call", _canonical_spaces(match.group(0)))
    for raw, canonical in CONTEXT_TERMS.items():
        if raw in lowered:
            _add_entity(entities, "context", canonical)
    for raw, canonical in WARNING_TERMS.items():
        if raw in lowered:
            _add_entity(entities, "risk", canonical)
    if "accepted" in lowered or item_kind == "accepted_answer":
        _add_entity(entities, "answer_signal", "accepted_answer")
    if "score" in lowered:
        _add_entity(entities, "answer_signal", "score_signal")
    if "duplicate" in lowered:
        _add_entity(entities, "link_signal", "duplicate")
    if "newer" in lowered or "modern python" in lowered or "python 3.12" in lowered or "deprecated" in lowered:
        _add_entity(entities, "status", _status_excerpt(text))
    _add_actions(entities, lowered)
    return entities


def _normalize_question(question: dict[str, Any], captured_at: str) -> dict[str, Any]:
    question_id = str(question.get("question_id") or "fixture-question")
    source_url = str(question.get("link") or question.get("source_url") or f"https://stackoverflow.com/questions/{question_id}")
    tags = [str(tag) for tag in question.get("tags", [])]
    q_item = _evidence_item(
        item_kind="question",
        item_id=f"question:{question_id}",
        question_id=question_id,
        source_url=source_url,
        text=str(question.get("body_text") or ""),
        title=str(question.get("title") or ""),
        created_at=question.get("creation_date"),
        last_activity_at=question.get("last_activity_date"),
        last_edit_at=question.get("last_edit_date"),
        score=question.get("score"),
        tags=tags,
        captured_at=captured_at,
        stackoverflow={"is_answered": question.get("is_answered"), "accepted_answer_id": question.get("accepted_answer_id")},
    )
    answer_items = [
        _evidence_item(
            item_kind="accepted_answer" if answer.get("is_accepted") else "answer",
            item_id=f"answer:{answer.get('answer_id')}",
            question_id=question_id,
            answer_id=str(answer.get("answer_id")),
            source_url=f"{source_url.rstrip('/')}#{answer.get('answer_id')}",
            text=str(answer.get("body_text") or ""),
            title=str(question.get("title") or ""),
            created_at=answer.get("creation_date"),
            last_activity_at=question.get("last_activity_date"),
            last_edit_at=answer.get("last_edit_date"),
            score=answer.get("score"),
            tags=tags,
            captured_at=captured_at,
            stackoverflow={"is_accepted": bool(answer.get("is_accepted")), "accepted_answer_id": question.get("accepted_answer_id")},
        )
        for answer in question.get("answers", [])
    ]
    comment_items = []
    for comment in question.get("comments", []):
        comment_items.append(
            _comment_item(comment, question_id, None, source_url, str(question.get("title") or ""), tags, captured_at)
        )
    for answer in question.get("answers", []):
        answer_id = str(answer.get("answer_id"))
        answer_url = f"{source_url.rstrip('/')}#{answer_id}"
        for comment in answer.get("comments", []):
            comment_items.append(
                _comment_item(comment, question_id, answer_id, answer_url, str(question.get("title") or ""), tags, captured_at)
            )
    linked_items = [
        _linked_question_item(linked, question_id, str(question.get("title") or ""), tags, captured_at)
        for linked in question.get("linked_questions", [])
    ]
    items = [q_item, *answer_items, *comment_items, *linked_items]
    return {
        "schema": "aoa_stackoverflow_normalized_question_v1",
        "question_id": question_id,
        "source_url": source_url,
        "title": str(question.get("title") or ""),
        "tags": tags,
        "score": question.get("score"),
        "is_answered": bool(question.get("is_answered")),
        "accepted_answer_id": question.get("accepted_answer_id"),
        "created_at": question.get("creation_date"),
        "last_activity_at": question.get("last_activity_date"),
        "last_edit_at": question.get("last_edit_date"),
        "captured_at": captured_at,
        "answers": [item for item in items if item["item_kind"] in {"answer", "accepted_answer"}],
        "comments": [item for item in items if item["item_kind"] == "comment"],
        "linked_questions": [item for item in items if item["item_kind"] == "linked_question"],
        "evidence_items": items,
    }


def _comment_item(
    comment: dict[str, Any],
    question_id: str,
    answer_id: str | None,
    parent_url: str,
    title: str,
    tags: list[str],
    captured_at: str,
) -> dict[str, Any]:
    comment_id = str(comment.get("comment_id") or f"{question_id}-comment")
    return _evidence_item(
        item_kind="comment",
        item_id=f"comment:{comment_id}",
        question_id=question_id,
        answer_id=answer_id,
        comment_id=comment_id,
        source_url=f"{parent_url.rstrip('/')}#comment-{comment_id}",
        text=str(comment.get("body_text") or ""),
        title=title,
        created_at=comment.get("creation_date"),
        score=comment.get("score"),
        tags=tags,
        captured_at=captured_at,
        stackoverflow={"parent_answer_id": answer_id},
    )


def _linked_question_item(linked: dict[str, Any], question_id: str, title: str, tags: list[str], captured_at: str) -> dict[str, Any]:
    linked_id = str(linked.get("question_id") or slug(str(linked.get("title") or "linked")))
    link_type = str(linked.get("link_type") or "related")
    linked_title = str(linked.get("title_text") or linked.get("title") or "")
    text = f"{link_type} question: {linked_title}"
    return _evidence_item(
        item_kind="linked_question",
        item_id=f"linked:{linked_id}",
        question_id=question_id,
        linked_question_id=linked_id,
        source_url=str(linked.get("link") or linked.get("source_url") or f"https://stackoverflow.com/questions/{linked_id}"),
        text=text,
        title=title,
        created_at=linked.get("creation_date"),
        score=linked.get("score"),
        tags=tags,
        captured_at=captured_at,
        stackoverflow={"link_type": link_type},
    )


def _evidence_item(
    *,
    item_kind: str,
    item_id: str,
    question_id: str,
    source_url: str,
    text: str,
    title: str,
    captured_at: str,
    created_at: Any = None,
    last_activity_at: Any = None,
    last_edit_at: Any = None,
    score: Any = None,
    tags: list[str] | None = None,
    answer_id: str | None = None,
    comment_id: str | None = None,
    linked_question_id: str | None = None,
    stackoverflow: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entities = extract_entities(text, tags=tags or [], item_kind=item_kind)
    if score is not None:
        _add_entity(entities, "answer_signal", "score_is_weak_signal")
    if item_kind == "accepted_answer":
        _add_entity(entities, "answer_signal", "accepted_answer")
    return {
        "schema": "aoa_stackoverflow_normalized_item_v1",
        "item_id": item_id,
        "item_kind": item_kind,
        "question_id": question_id,
        "answer_id": answer_id,
        "comment_id": comment_id,
        "linked_question_id": linked_question_id,
        "source_url": source_url,
        "title": title,
        "text": text[:12000],
        "tags": tags or [],
        "score": score,
        "created_at": created_at,
        "last_activity_at": last_activity_at,
        "last_edit_at": last_edit_at,
        "captured_at": captured_at,
        "entities": entities,
        "stackoverflow": stackoverflow or {},
        "source_shape": "stackexchange_api_question_bundle",
    }


def _add_actions(entities: list[dict[str, str]], lowered: str) -> None:
    if "datetime.now(timezone.utc)" in lowered or "datetime.now(utc)" in lowered:
        _add_entity(entities, "answer_action", "prefer timezone-aware current UTC")
    if "datetime.utcnow" in lowered:
        _add_entity(entities, "answer_action", "avoid datetime.utcnow naive UTC")
    if "replace(tzinfo" in lowered:
        _add_entity(entities, "answer_action", "label datetime with tzinfo")
    if "astimezone" in lowered:
        _add_entity(entities, "answer_action", "convert instant with astimezone")
    if "strip tzinfo" in lowered or "remove tzinfo" in lowered:
        _add_entity(entities, "answer_action", "strip tzinfo before comparing")
    if "duplicate" in lowered:
        _add_entity(entities, "graph_action", "follow duplicate question context")


def _status_excerpt(text: str) -> str:
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        lowered = sentence.casefold()
        if any(term in lowered for term in ["deprecated", "newer", "modern python", "python 3.12"]):
            return sentence[:220]
    return text[:220]


def _add_entity(entities: list[dict[str, str]], kind: str, value: str) -> None:
    canonical = _canonical_spaces(value)
    if not canonical:
        return
    if any(entity["kind"] == kind and entity["value"].casefold() == canonical.casefold() for entity in entities):
        return
    entities.append({"kind": kind, "value": canonical})


def _canonical_symbol(value: str) -> str:
    if value.casefold() == "utc":
        return "UTC"
    return value


def _canonical_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
