"""Claim extraction primitives for StackOverflow evidence."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime


CLAIM_EXTRACTOR_VERSION = "stackoverflow_claim_heuristic_v1"
RELATION_EXTRACTOR_VERSION = "connector_claim_relation_v1"
CLAIM_RELATION_KINDS = {
    "answer_acceptance_supports_claim",
    "answer_score_weakly_supports_claim",
    "claim_applies_to_context",
    "claim_contextualizes_claim",
    "claim_contradicts_claim",
    "claim_scope_limited_by",
    "claim_supersedes_claim",
    "claim_unknown_for_context",
    "duplicate_contextualizes_question",
    "method_uses_tool",
    "method_targets_object",
    "source_links_claim",
    "source_supports_claim",
    "source_updates_claim",
    "source_warns_about_claim",
    "warning_targets_action",
    "warning_targets_object",
}


def extract_item_claims(item: dict[str, object], profile_id: str) -> list[dict[str, object]]:
    text = str(item.get("text") or "")
    lowered = text.casefold()
    entities = [entity for entity in item.get("entities", []) if isinstance(entity, dict)]
    item_kind = str(item.get("item_kind") or "")
    claims: list[dict[str, object]] = []
    context_labels = _context_labels(item, entities)
    tool_labels = _tool_labels(entities)
    warning_labels = _warning_labels(entities, text)
    risk_labels = _labels_by_kind(entities, "risk")

    for action in _labels_by_kind(entities, "answer_action"):
        claim_kind = "method"
        method_kind = _method_kind(action)
        confidence = _confidence(item, action)
        manual_review = item_kind != "accepted_answer" or "deprecated" in lowered or "avoid" in lowered
        if "avoid" in action or "strip tzinfo" in action:
            claim_kind = "warning" if "strip tzinfo" in action else "status"
        claims.append(
            _claim(
                item,
                profile_id,
                claim_kind=claim_kind,
                method_kind=method_kind,
                action_label=action,
                target_labels=_targets_for_action(action),
                tool_labels=tool_labels,
                context_labels=context_labels,
                risk_labels=risk_labels,
                warning_labels=warning_labels,
                confidence=confidence,
                extraction_rule=f"stackoverflow_{method_kind}_entity_v1",
                manual_review_required=manual_review,
                evidence_span=_evidence_span(text, action),
            )
        )

    if item_kind == "comment" and (risk_labels or warning_labels):
        warning = _first_warning_label(warning_labels, text)
        claims.append(
            _claim(
                item,
                profile_id,
                claim_kind="warning",
                method_kind="comment_warning",
                action_label=warning,
                target_labels=_comment_targets(text),
                tool_labels=tool_labels,
                context_labels=context_labels,
                risk_labels=risk_labels or ["comment_warning"],
                warning_labels=[warning],
                confidence=0.66,
                extraction_rule="stackoverflow_comment_warning_v1",
                manual_review_required=True,
                evidence_span=_evidence_span(text, warning),
            )
        )

    if item_kind == "linked_question":
        link_type = str(_stackoverflow(item).get("link_type") or "related")
        claims.append(
            _claim(
                item,
                profile_id,
                claim_kind="context",
                method_kind=f"{link_type}_question",
                action_label=f"{link_type} question context",
                target_labels=[str(item.get("linked_question_id") or item.get("question_id") or "linked_question")],
                tool_labels=[],
                context_labels=context_labels + [link_type],
                risk_labels=[],
                warning_labels=[],
                confidence=0.52,
                extraction_rule="stackoverflow_linked_question_v1",
                manual_review_required=False,
                evidence_span=_evidence_span(text, link_type),
            )
        )

    if item_kind in {"answer", "accepted_answer"} and "deprecated" in lowered and "datetime.utcnow" in lowered:
        claims.append(
            _claim(
                item,
                profile_id,
                claim_kind="status",
                method_kind="freshness_update",
                action_label="datetime.utcnow is stale for new UTC code",
                target_labels=["datetime.utcnow"],
                tool_labels=["datetime"],
                context_labels=context_labels,
                risk_labels=["naive_datetime"],
                warning_labels=["prefer aware UTC replacement"],
                confidence=_confidence(item, "datetime.utcnow is stale"),
                extraction_rule="stackoverflow_deprecation_language_v1",
                manual_review_required=True,
                evidence_span=_evidence_span(text, "datetime.utcnow"),
            )
        )

    return _dedupe_claims(claims)


def assign_freshness_windows(claims: list[dict[str, object]]) -> None:
    if not claims:
        return
    ranked = sorted(claims, key=lambda claim: (_claim_time_sort_key(claim), str(claim.get("claim_id"))))
    count = len(ranked)
    by_target: dict[str, list[dict[str, object]]] = {}
    for claim in ranked:
        by_target.setdefault(_relation_key(claim), []).append(claim)
    for index, claim in enumerate(ranked):
        freshness = claim.setdefault("freshness_context", {})
        if not isinstance(freshness, dict):
            freshness = {}
            claim["freshness_context"] = freshness
        newer_related = [
            str(other.get("claim_id"))
            for other in by_target.get(_relation_key(claim), [])
            if _claim_time_sort_key(other) > _claim_time_sort_key(claim)
        ]
        freshness["profile_window"] = "latest_window" if index == count - 1 else ("early" if index < count / 2 else "middle")
        freshness["newer_related_claim_ids"] = newer_related
        freshness["newer_related_claims_exist"] = bool(newer_related)
        freshness["possibly_superseded"] = bool(newer_related)


def graph_nodes_for_claims(claims: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    nodes: dict[str, dict[str, object]] = {}
    for claim in claims:
        claim_id = str(claim["claim_id"])
        source_url = str(claim.get("source_url") or "")
        nodes[claim_id] = {
            "schema": "aoa_connector_claim_node_v1",
            "node_id": claim_id,
            "kind": "claim",
            "label": str(claim.get("label") or claim.get("action") or claim_id),
            "source_refs": [source_url] if source_url else [],
            "confidence": float(claim.get("confidence") or 0.0),
            "claim": claim,
        }
        method_id = str(claim.get("method_id") or "")
        if method_id:
            _upsert_node(nodes, method_id, "method", str(claim.get("method_label") or method_id), source_url, 0.65)
        action_node = _action_node_id(claim.get("action"))
        if action_node:
            _upsert_node(nodes, action_node, "action", str(claim.get("action")), source_url, 0.65)
        for label in _strings(claim.get("target_labels", [])):
            _upsert_node(nodes, _target_node_id(label), "target", label, source_url, 0.65)
        for label in _strings(claim.get("tool_labels", [])):
            _upsert_node(nodes, _tool_node_id(label), "tool", label, source_url, 0.65)
        for label in _strings(claim.get("applicability_context", [])):
            _upsert_node(nodes, _context_node_id(label), "applicability_context", label, source_url, 0.6)
        for label in _strings(claim.get("warning_labels", [])):
            _upsert_node(nodes, _warning_node_id(label), "warning", label, source_url, 0.65)
    return nodes


def relation_edges_for_claims(claims: list[dict[str, object]]) -> list[dict[str, object]]:
    edges: list[dict[str, object]] = []
    for claim in claims:
        claim_id = str(claim["claim_id"])
        item_node = f"item:{claim.get('source_item_id')}"
        claim_kind = str(claim.get("claim_kind") or "")
        if claim_kind == "warning":
            source_kind = "source_warns_about_claim"
        elif claim_kind == "status":
            source_kind = "source_updates_claim"
        elif claim_kind == "context":
            source_kind = "source_links_claim"
        else:
            source_kind = "source_supports_claim"
        _append_claim_edge(edges, source_kind, item_node, claim_id, claim, confidence=float(claim.get("confidence") or 0.0))
        stackoverflow = claim.get("stackoverflow", {})
        if isinstance(stackoverflow, dict) and stackoverflow.get("is_accepted"):
            _append_claim_edge(edges, "answer_acceptance_supports_claim", item_node, claim_id, claim, confidence=0.58)
        if _score_value(claim) is not None:
            _append_claim_edge(edges, "answer_score_weakly_supports_claim", item_node, claim_id, claim, confidence=0.35)
        method_id = str(claim.get("method_id") or "")
        action_node = _action_node_id(claim.get("action"))
        if action_node:
            _append_claim_edge(edges, "claim_applies_to_context", claim_id, action_node, claim, confidence=0.55)
        if method_id:
            for label in _strings(claim.get("tool_labels", [])):
                _append_claim_edge(edges, "method_uses_tool", method_id, _tool_node_id(label), claim, confidence=0.58)
            for label in _strings(claim.get("target_labels", [])):
                _append_claim_edge(edges, "method_targets_object", method_id, _target_node_id(label), claim, confidence=0.62)
        for label in _strings(claim.get("applicability_context", [])):
            _append_claim_edge(edges, "claim_applies_to_context", claim_id, _context_node_id(label), claim, confidence=0.55)
        if claim_kind == "warning":
            for label in _strings(claim.get("target_labels", [])):
                _append_claim_edge(edges, "warning_targets_object", claim_id, _target_node_id(label), claim, confidence=0.62)
            if action_node:
                _append_claim_edge(edges, "warning_targets_action", claim_id, action_node, claim, confidence=0.55)
    _append_cross_claim_edges(edges, claims)
    return edges


def claim_graph_stats(claims: list[dict[str, object]], edges: list[dict[str, object]]) -> dict[str, object]:
    relation_counts: dict[str, int] = {}
    for edge in edges:
        kind = str(edge.get("kind") or "")
        if kind in CLAIM_RELATION_KINDS:
            relation_counts[kind] = relation_counts.get(kind, 0) + 1
    return {
        "schema": "aoa_connector_claim_graph_stats_v1",
        "claim_count": len(claims),
        "method_count": sum(1 for claim in claims if claim.get("claim_kind") == "method"),
        "warning_count": sum(1 for claim in claims if claim.get("claim_kind") == "warning"),
        "status_count": sum(1 for claim in claims if claim.get("claim_kind") == "status"),
        "context_count": sum(1 for claim in claims if claim.get("claim_kind") == "context"),
        "relation_counts": relation_counts,
        "supersedes_count": relation_counts.get("claim_supersedes_claim", 0),
        "contradicts_count": relation_counts.get("claim_contradicts_claim", 0),
        "contextualizes_count": relation_counts.get("claim_contextualizes_claim", 0),
        "score_signal_count": relation_counts.get("answer_score_weakly_supports_claim", 0),
        "accepted_signal_count": relation_counts.get("answer_acceptance_supports_claim", 0),
    }


def _claim(
    item: dict[str, object],
    profile_id: str,
    *,
    claim_kind: str,
    method_kind: str,
    action_label: str,
    target_labels: list[str],
    tool_labels: list[str],
    context_labels: list[str],
    risk_labels: list[str],
    warning_labels: list[str],
    confidence: float,
    extraction_rule: str,
    manual_review_required: bool,
    evidence_span: dict[str, object],
) -> dict[str, object]:
    label = _claim_label(action_label, target_labels, tool_labels, context_labels)
    item_id = str(item.get("item_id") or "unknown")
    method_id = f"method:{profile_id}:{_slug(method_kind)}:{_slug(label)}" if claim_kind == "method" else None
    claim_id = f"claim:{profile_id}:{_slug(item_id)}:{_slug(claim_kind)}:{_slug(label)}"
    if len(claim_id) > 160:
        claim_id = f"claim:{profile_id}:{_slug(item_id)}:{_slug(claim_kind)}:{hashlib.sha256(label.encode('utf-8')).hexdigest()[:16]}"
    source_item = {
        "item_id": item.get("item_id"),
        "item_kind": item.get("item_kind"),
        "question_id": item.get("question_id"),
        "answer_id": item.get("answer_id"),
        "comment_id": item.get("comment_id"),
        "linked_question_id": item.get("linked_question_id"),
        "source_url": item.get("source_url"),
        "created_at": item.get("created_at"),
        "last_edit_at": item.get("last_edit_at"),
        "captured_at": item.get("captured_at"),
        "score": item.get("score"),
        "stackoverflow": item.get("stackoverflow", {}),
    }
    freshness_context = {
        "created_at": item.get("created_at"),
        "last_edit_at": item.get("last_edit_at"),
        "captured_at": item.get("captured_at"),
        "source_freshness": "stackexchange_creation_edit_and_capture_metadata",
        "profile_window": "unknown",
        "update_language": _has_update_language(str(item.get("text") or "")),
        "negative_status_language": _has_negative_language(str(item.get("text") or "")),
    }
    return {
        "schema": "aoa_connector_claim_v1",
        "claim_id": claim_id,
        "claim_kind": claim_kind,
        "method_id": method_id,
        "method_kind": method_kind,
        "method_label": label if claim_kind == "method" else None,
        "action": action_label,
        "label": label,
        "target_labels": _unique(target_labels),
        "tool_labels": _unique(tool_labels),
        "condition_labels": [],
        "applicability_context": _unique(context_labels),
        "risk_labels": _unique(risk_labels),
        "warning_labels": _unique(warning_labels),
        "source_item": source_item,
        "source_item_id": item.get("item_id"),
        "source_url": item.get("source_url"),
        "created_at": item.get("created_at"),
        "last_edit_at": item.get("last_edit_at"),
        "captured_at": item.get("captured_at"),
        "evidence_span": evidence_span,
        "freshness_context": freshness_context,
        "confidence": round(confidence, 3),
        "confidence_basis": {
            "basis": extraction_rule,
            "extractor_version": CLAIM_EXTRACTOR_VERSION,
            "stackoverflow_signals_are_not_truth": True,
        },
        "manual_review_required": manual_review_required,
        "score_signal": _score_value_from_item(item),
        "stackoverflow": item.get("stackoverflow", {}),
    }


def _append_cross_claim_edges(edges: list[dict[str, object]], claims: list[dict[str, object]]) -> None:
    for older in claims:
        for newer in claims:
            if older is newer:
                continue
            if _claim_time_sort_key(newer) <= _claim_time_sort_key(older):
                continue
            older_action = str(older.get("action") or "").casefold()
            newer_action = str(newer.get("action") or "").casefold()
            if "datetime.utcnow" in newer_action and ("datetime.utcnow" in older_action or "current utc" in older_action):
                _append_claim_edge(edges, "claim_supersedes_claim", str(newer["claim_id"]), str(older["claim_id"]), newer, confidence=0.52)
            if "timezone-aware" in newer_action and "strip tzinfo" in older_action:
                _append_claim_edge(edges, "claim_contradicts_claim", str(newer["claim_id"]), str(older["claim_id"]), newer, confidence=0.58)
            if older.get("source_item", {}).get("answer_id") and older.get("source_item", {}).get("answer_id") == newer.get("source_item", {}).get("answer_id"):
                if newer.get("claim_kind") == "warning":
                    _append_claim_edge(edges, "claim_contextualizes_claim", str(newer["claim_id"]), str(older["claim_id"]), newer, confidence=0.55)
                    _append_claim_edge(edges, "claim_scope_limited_by", str(older["claim_id"]), str(newer["claim_id"]), older, confidence=0.5)
    for claim in claims:
        if claim.get("claim_kind") == "context" and "duplicate" in _strings(claim.get("applicability_context", [])):
            for target in claims:
                if target is not claim and target.get("source_item", {}).get("question_id") == claim.get("source_item", {}).get("question_id"):
                    _append_claim_edge(edges, "duplicate_contextualizes_question", str(claim["claim_id"]), str(target["claim_id"]), claim, confidence=0.5)


def _append_claim_edge(
    edges: list[dict[str, object]],
    kind: str,
    from_node: str,
    to_node: str,
    claim: dict[str, object],
    *,
    confidence: float,
) -> None:
    edge_id = f"{from_node}->{to_node}:{kind}"
    if any(edge.get("edge_id") == edge_id for edge in edges):
        return
    source_item = claim.get("source_item", {})
    source_item_ids = []
    if isinstance(source_item, dict) and source_item.get("item_id"):
        source_item_ids.append(str(source_item["item_id"]))
    edges.append(
        {
            "schema": "aoa_connector_claim_relation_v1",
            "edge_id": edge_id,
            "kind": kind,
            "from_node": from_node,
            "to_node": to_node,
            "source_refs": [str(claim.get("source_url") or "")],
            "source_item_ids": source_item_ids,
            "confidence": confidence,
            "extractor_version": RELATION_EXTRACTOR_VERSION,
            "relation_reason": _relation_reason(kind, claim),
        }
    )


def _relation_reason(kind: str, claim: dict[str, object]) -> str:
    if kind == "answer_acceptance_supports_claim":
        return "StackOverflow accepted answer is a source signal, not a truth guarantee."
    if kind == "answer_score_weakly_supports_claim":
        return "StackOverflow score is treated as weak crowd signal only."
    if kind == "claim_supersedes_claim":
        return "Newer/deprecation language creates possible freshness supersession."
    if kind == "duplicate_contextualizes_question":
        return "Duplicate or linked question gives graph context."
    return str(claim.get("confidence_basis", {}).get("basis", "local_claim_relation"))


def _confidence(item: dict[str, object], action: str) -> float:
    confidence = 0.56
    stackoverflow = _stackoverflow(item)
    if stackoverflow.get("is_accepted"):
        confidence += 0.12
    score = _score_value_from_item(item)
    if score is not None:
        confidence += min(0.08, max(0.0, score / 1000.0))
    if "avoid" in action or "deprecated" in action:
        confidence += 0.04
    return min(confidence, 0.82)


def _targets_for_action(action: str) -> list[str]:
    lowered = action.casefold()
    if "utcnow" in lowered:
        return ["datetime.utcnow", "naive UTC datetime"]
    if "timezone-aware" in lowered or "current utc" in lowered:
        return ["aware UTC datetime"]
    if "tzinfo" in lowered:
        return ["tzinfo labeling"]
    if "astimezone" in lowered:
        return ["instant conversion"]
    if "duplicate" in lowered:
        return ["linked question context"]
    return ["StackOverflow evidence"]


def _tool_labels(entities: list[dict[str, object]]) -> list[str]:
    labels = []
    for value in _labels_by_kind(entities, "python_symbol"):
        if value in {"datetime", "timezone", "UTC", "tzinfo", "astimezone", "pytz", "zoneinfo"}:
            labels.append(value)
    for value in _labels_by_kind(entities, "api_call"):
        labels.append(value)
    return _unique(labels)


def _context_labels(item: dict[str, object], entities: list[dict[str, object]]) -> list[str]:
    labels = [str(tag) for tag in item.get("tags", [])]
    labels.extend(_labels_by_kind(entities, "context"))
    stackoverflow = _stackoverflow(item)
    if stackoverflow.get("is_accepted"):
        labels.append("accepted_answer_signal")
    if item.get("score") is not None:
        labels.append("score_is_weak_signal")
    if stackoverflow.get("link_type"):
        labels.append(str(stackoverflow["link_type"]))
    return _unique(labels)


def _warning_labels(entities: list[dict[str, object]], text: str) -> list[str]:
    labels = _labels_by_kind(entities, "risk")
    lowered = text.casefold()
    if "replace(tzinfo" in lowered and ("not convert" in lowered or "incorrect instant" in lowered):
        labels.append("replace(tzinfo=...) can mislabel an instant")
    if "strip tzinfo" in lowered or "remove tzinfo" in lowered:
        labels.append("stripping tzinfo can lose timezone meaning")
    if "score" in lowered and "truth" in lowered:
        labels.append("score is not truth")
    return _unique(labels)


def _first_warning_label(warning_labels: list[str], text: str) -> str:
    return warning_labels[0] if warning_labels else text[:180]


def _comment_targets(text: str) -> list[str]:
    lowered = text.casefold()
    targets = []
    if "replace(tzinfo" in lowered:
        targets.append("replace(tzinfo=...)")
    if "utcnow" in lowered:
        targets.append("datetime.utcnow")
    if "score" in lowered:
        targets.append("score signal")
    if "strip tzinfo" in lowered:
        targets.append("strip tzinfo")
    return targets or ["commented answer"]


def _method_kind(action: str) -> str:
    lowered = action.casefold()
    if "utcnow" in lowered:
        return "utcnow_freshness"
    if "timezone-aware" in lowered:
        return "timezone_aware_utc"
    if "tzinfo" in lowered:
        return "tzinfo_labeling"
    if "astimezone" in lowered:
        return "astimezone_conversion"
    if "strip tzinfo" in lowered:
        return "strip_tzinfo"
    return "stackoverflow_answer"


def _claim_label(action: str, targets: list[str], tools: list[str], contexts: list[str]) -> str:
    parts = [action]
    if targets:
        parts.append("target=" + ",".join(targets[:3]))
    if tools:
        parts.append("tools=" + ",".join(tools[:3]))
    if contexts:
        parts.append("context=" + ",".join(contexts[:3]))
    return " | ".join(parts)


def _evidence_span(text: str, needle: str) -> dict[str, object]:
    if not text:
        return {"start": 0, "end": 0, "text": ""}
    lowered = text.casefold()
    query = needle.casefold().split(" ")[0]
    start = lowered.find(query) if query else -1
    if start < 0:
        start = 0
    end = min(len(text), start + 260)
    return {"start": start, "end": end, "text": text[start:end]}


def _relation_key(claim: dict[str, object]) -> str:
    targets = "|".join(_strings(claim.get("target_labels", [])))
    action = str(claim.get("action") or "")
    if "utcnow" in action.casefold():
        return "datetime.utcnow"
    if "timezone-aware" in action.casefold():
        return "aware UTC datetime"
    return targets or action


def _claim_time_sort_key(claim: dict[str, object]) -> str:
    return str(claim.get("last_edit_at") or claim.get("created_at") or "")


def _score_value(claim: dict[str, object]) -> int | None:
    return _score_value_from_item(claim.get("source_item", {}) if isinstance(claim.get("source_item"), dict) else {})


def _score_value_from_item(item: dict[str, object]) -> int | None:
    score = item.get("score")
    if isinstance(score, int):
        return score
    try:
        return int(score) if score is not None else None
    except (TypeError, ValueError):
        return None


def _stackoverflow(item: dict[str, object]) -> dict[str, object]:
    value = item.get("stackoverflow", {})
    return value if isinstance(value, dict) else {}


def _labels_by_kind(entities: list[dict[str, object]], kind: str) -> list[str]:
    return _unique([str(entity.get("value") or "") for entity in entities if entity.get("kind") == kind])


def _strings(values: object) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    if isinstance(values, list):
        return [str(value) for value in values if value is not None]
    return [str(values)]


def _dedupe_claims(claims: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[str] = set()
    unique: list[dict[str, object]] = []
    for claim in claims:
        claim_id = str(claim.get("claim_id"))
        if claim_id in seen:
            continue
        seen.add(claim_id)
        unique.append(claim)
    return unique


def _upsert_node(nodes: dict[str, dict[str, object]], node_id: str, kind: str, label: str, source_url: str, confidence: float) -> None:
    node = nodes.setdefault(
        node_id,
        {
            "schema": "aoa_stackoverflow_graph_node_v1",
            "node_id": node_id,
            "kind": kind,
            "label": label,
            "source_refs": [],
            "confidence": confidence,
        },
    )
    if source_url and source_url not in node["source_refs"]:
        node["source_refs"].append(source_url)


def _action_node_id(value: object) -> str | None:
    if not value:
        return None
    return f"action:{_slug(str(value))}"


def _target_node_id(label: str) -> str:
    return f"target:{_slug(label)}"


def _tool_node_id(label: str) -> str:
    return f"tool:{_slug(label)}"


def _context_node_id(label: str) -> str:
    return f"context:{_slug(label)}"


def _warning_node_id(label: str) -> str:
    return f"warning:{_slug(label)}"


def _has_update_language(text: str) -> bool:
    lowered = text.casefold()
    return any(term in lowered for term in ["deprecated", "modern python", "newer", "python 3.12", "prefer"])


def _has_negative_language(text: str) -> bool:
    lowered = text.casefold()
    return any(term in lowered for term in ["avoid", "do not", "loses", "incorrect", "deprecated"])


def _unique(values: list[str]) -> list[str]:
    unique: list[str] = []
    for value in values:
        clean = re.sub(r"\s+", " ", str(value)).strip()
        if clean and clean not in unique:
            unique.append(clean)
    return unique


def _slug(value: str) -> str:
    lowered = value.casefold()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-") or "item"
