"""Answer rendering over local StackOverflow evidence packets."""

from __future__ import annotations


def render_answer_packet(evidence_packet: dict[str, object], limit: int = 5) -> dict[str, object]:
    results = [result for result in evidence_packet.get("results", [])[:limit] if isinstance(result, dict)]
    answered = bool(results)
    answers = [_answer_for_result(result, evidence_packet.get("created_at")) for result in results] if answered else []
    evidence_chain = _evidence_chain(answers, results)
    grounding = _grounding_report(results)
    conflict_report = _conflict_report(evidence_chain, grounding)
    freshness_report = _freshness_report(evidence_chain, grounding, conflict_report)
    applicability_report = _applicability_report(evidence_chain, grounding)
    warning_report = _warning_report(evidence_chain, grounding)
    score_report = _score_signal_report(evidence_chain)
    return {
        "schema": "aoa_connector_answer_packet_v1",
        "answer_id": str(evidence_packet.get("packet_id", "query")).replace("query-", "answer-", 1),
        "query": evidence_packet.get("query", ""),
        "created_at": evidence_packet.get("created_at"),
        "answer_report": {
            "renderer": "stackoverflow_starter_claim_context_v1",
            "source_packet_id": evidence_packet.get("packet_id"),
            "source_packet_schema": evidence_packet.get("schema"),
            "query_algorithm": _query_algorithm(evidence_packet),
            **grounding,
        },
        "answers": answers,
        "evidence_chain": evidence_chain,
        "nuance_report": _nuance_report(evidence_chain, grounding),
        "conflict_report": conflict_report,
        "freshness_report": freshness_report,
        "applicability_report": applicability_report,
        "warning_report": warning_report,
        "score_signal_report": score_report,
        "agent_answer": _agent_answer(
            evidence_packet.get("query", ""),
            evidence_chain,
            grounding,
            conflict_report,
            freshness_report,
            warning_report,
            score_report,
        ),
        "policy": {
            "source": "local_keyword_index_plus_graph_answer_renderer",
            "internal_search_used": False,
            "stackoverflow_score_is_truth": False,
            "accepted_answer_is_truth": False,
        },
        "network_touched": False,
        "read_only": True,
    }


def _query_algorithm(packet: dict[str, object]) -> object:
    report = packet.get("query_report", {})
    return report.get("algorithm") if isinstance(report, dict) else None


def _grounding_report(results: list[dict[str, object]]) -> dict[str, object]:
    return {
        "answer_status": "answered" if results else "insufficient_evidence",
        "gap_reason": None if results else "no_candidate_evidence",
        "candidate_result_count": len(results),
        "grounded_candidate_count": len(results),
        "filtered_candidate_count": 0,
        "deduplicated_candidate_count": 0,
    }


def _answer_for_result(result: dict[str, object], packet_created_at: object) -> dict[str, object]:
    graph_context = result.get("graph_context", {})
    if not isinstance(graph_context, dict):
        graph_context = {}
    claims = [node.get("claim") for node in graph_context.get("claim_nodes", []) if isinstance(node, dict) and isinstance(node.get("claim"), dict)]
    warning_labels = _claim_field_labels(claims, "warning_labels")
    target_labels = _claim_field_labels(claims, "target_labels")
    tool_labels = _claim_field_labels(claims, "tool_labels")
    context_labels = _claim_field_labels(claims, "applicability_context")
    claim_ids = [str(claim.get("claim_id")) for claim in claims if claim.get("claim_id")]
    answer_kind = _answer_kind(claims, warning_labels, str(result.get("item_kind") or ""))
    answer_text = _answer_text(answer_kind, result, target_labels, tool_labels, context_labels)
    stackoverflow = result.get("stackoverflow", {})
    if not isinstance(stackoverflow, dict):
        stackoverflow = {}
    return {
        "answer_kind": answer_kind,
        "answer_text": answer_text,
        "source_url": result.get("source_url"),
        "topic_id": result.get("topic_id"),
        "question_id": result.get("question_id"),
        "answer_id": result.get("answer_id"),
        "comment_id": result.get("comment_id"),
        "linked_question_id": result.get("linked_question_id"),
        "item_id": result.get("item_id"),
        "item_kind": result.get("item_kind"),
        "created_at": result.get("created_at"),
        "last_edit_at": result.get("last_edit_at"),
        "captured_at": result.get("captured_at"),
        "chunk_id": result.get("chunk_id"),
        "score": result.get("score"),
        "source_score": result.get("source_score"),
        "tags": result.get("tags", []),
        "stackoverflow": stackoverflow,
        "evidence_refs": result.get("evidence_refs", []),
        "source_refs": [result.get("source_url")],
        "claim_ids": claim_ids,
        "warning_labels": warning_labels,
        "target_labels": target_labels,
        "tool_labels": tool_labels,
        "claim_context_labels": context_labels,
        "claim_freshness_windows": _claim_freshness_windows(claims),
        "claim_relation_edges": graph_context.get("relation_edges", []),
        "relation_kinds": graph_context.get("relation_kinds", []),
        "freshness": {
            "basis": "stackexchange_created_edit_capture_metadata",
            "created_at": result.get("created_at"),
            "last_edit_at": result.get("last_edit_at"),
            "captured_at": result.get("captured_at"),
            "packet_created_at": packet_created_at,
            "note": "Freshness is local-evidence freshness, not a live StackOverflow truth claim.",
        },
        "confidence": {
            "basis": "local_graph_grounding_with_stackoverflow_signals",
            "score": result.get("score"),
            "source_score_is_weak_signal": result.get("source_score"),
            "accepted_answer_signal": bool(stackoverflow.get("is_accepted")),
        },
    }


def _evidence_chain(answers: list[dict[str, object]], results: list[dict[str, object]]) -> list[dict[str, object]]:
    chain: list[dict[str, object]] = []
    for index, (answer, result) in enumerate(zip(answers, results, strict=True), start=1):
        relation_kinds = _strings(answer.get("relation_kinds", []))
        chain.append(
            {
                "chain_step": index,
                "role": _chain_role(index, answer, relation_kinds),
                "answer_kind": answer.get("answer_kind"),
                "summary": answer.get("answer_text"),
                "source_url": answer.get("source_url"),
                "topic_id": answer.get("topic_id"),
                "question_id": answer.get("question_id"),
                "answer_id": answer.get("answer_id"),
                "comment_id": answer.get("comment_id"),
                "linked_question_id": answer.get("linked_question_id"),
                "item_id": answer.get("item_id"),
                "item_kind": answer.get("item_kind"),
                "chunk_id": answer.get("chunk_id"),
                "created_at": answer.get("created_at"),
                "last_edit_at": answer.get("last_edit_at"),
                "captured_at": answer.get("captured_at"),
                "freshness": answer.get("freshness", {}),
                "evidence_refs": answer.get("evidence_refs", []),
                "source_refs": answer.get("source_refs", []),
                "claim_ids": answer.get("claim_ids", []),
                "claim_relation_edges": answer.get("claim_relation_edges", []),
                "claim_freshness_windows": answer.get("claim_freshness_windows", []),
                "matched_terms": _strings(result.get("matched_terms", [])),
                "matched_exact_terms": _strings(result.get("matched_exact_terms", [])),
                "matched_specific_terms": _strings(result.get("matched_specific_terms", [])),
                "relation_kinds": relation_kinds,
                "warning_labels": answer.get("warning_labels", []),
                "target_labels": answer.get("target_labels", []),
                "tool_labels": answer.get("tool_labels", []),
                "claim_context_labels": answer.get("claim_context_labels", []),
                "score": answer.get("score"),
                "source_score": answer.get("source_score"),
                "stackoverflow": answer.get("stackoverflow", {}),
            }
        )
    return chain


def _chain_role(index: int, answer: dict[str, object], relation_kinds: list[str]) -> str:
    if index == 1:
        return "primary"
    if "claim_contradicts_claim" in relation_kinds:
        return "conflicting"
    if "claim_supersedes_claim" in relation_kinds:
        return "superseding"
    if answer.get("warning_labels"):
        return "caution"
    if "duplicate_contextualizes_question" in relation_kinds or "claim_contextualizes_claim" in relation_kinds:
        return "contextual"
    return "supporting"


def _nuance_report(chain: list[dict[str, object]], grounding: dict[str, object]) -> dict[str, object]:
    return {
        "chain_step_count": len(chain),
        "question_count": len({step.get("question_id") for step in chain if step.get("question_id")}),
        "answer_count": len({step.get("answer_id") for step in chain if step.get("answer_id")}),
        "comment_count": len({step.get("comment_id") for step in chain if step.get("comment_id")}),
        "source_count": len({step.get("source_url") for step in chain if step.get("source_url")}),
        "relation_kinds": _unique([kind for step in chain for kind in _strings(step.get("relation_kinds", []))]),
        "limitations": [] if chain else [{"kind": str(grounding.get("gap_reason") or "insufficient_evidence"), "count": 1}],
    }


def _conflict_report(chain: list[dict[str, object]], grounding: dict[str, object]) -> dict[str, object]:
    if not chain or grounding.get("answer_status") == "insufficient_evidence":
        return {
            "schema": "aoa_connector_conflict_report_v1",
            "status": "insufficient_evidence",
            "primary_claim_id": None,
            "primary_item_id": None,
            "supporting_claim_ids": [],
            "conflicting_claim_ids": [],
            "superseding_claim_ids": [],
            "contextual_claim_ids": [],
            "warnings": [],
            "missing": ["no_candidate_evidence"],
            "confidence": "none",
        }
    edges = _chain_relation_edges(chain)
    conflicting = _edge_claim_ids(edges, {"claim_contradicts_claim"})
    superseding = _edge_claim_ids(edges, {"claim_supersedes_claim"})
    contextual = _edge_claim_ids(edges, {"claim_contextualizes_claim", "duplicate_contextualizes_question", "claim_scope_limited_by"})
    status = "clear"
    if conflicting:
        status = "conflict_detected"
    elif superseding:
        status = "possibly_superseded"
    elif contextual:
        status = "contextualized"
    primary_claims = _strings(chain[0].get("claim_ids", []))
    return {
        "schema": "aoa_connector_conflict_report_v1",
        "status": status,
        "primary_claim_id": primary_claims[0] if primary_claims else None,
        "primary_item_id": chain[0].get("item_id"),
        "supporting_claim_ids": _unique([claim_id for step in chain for claim_id in _strings(step.get("claim_ids", []))]),
        "conflicting_claim_ids": conflicting,
        "superseding_claim_ids": superseding,
        "contextual_claim_ids": contextual,
        "warnings": _warning_claim_ids(chain),
        "missing": [],
        "confidence": "medium" if conflicting or superseding else "starter",
    }


def _freshness_report(chain: list[dict[str, object]], grounding: dict[str, object], conflict_report: dict[str, object]) -> dict[str, object]:
    if not chain or grounding.get("answer_status") == "insufficient_evidence":
        status = "insufficient_evidence"
    elif conflict_report.get("status") == "conflict_detected":
        status = "conflicting_evidence"
    elif conflict_report.get("status") == "possibly_superseded" or conflict_report.get("superseding_claim_ids"):
        status = "possibly_superseded"
    elif conflict_report.get("status") == "contextualized":
        status = "context_limited"
    else:
        status = "fresh_answer"
    dates = _strings([step.get("last_edit_at") or step.get("created_at") for step in chain])
    return {
        "schema": "aoa_connector_freshness_report_v1",
        "status": status,
        "basis": "created_at_last_edit_claim_relations_and_local_graph",
        "latest_source_timestamp": max(dates) if dates else None,
        "newer_related_claims_visible": bool(conflict_report.get("superseding_claim_ids")),
    }


def _applicability_report(chain: list[dict[str, object]], grounding: dict[str, object]) -> dict[str, object]:
    if not chain or grounding.get("answer_status") == "insufficient_evidence":
        return {"schema": "aoa_connector_applicability_report_v1", "status": "insufficient_evidence", "contexts": [], "conditions": []}
    contexts = _unique([label for step in chain for label in _strings(step.get("claim_context_labels", []))])
    return {
        "schema": "aoa_connector_applicability_report_v1",
        "status": "applicability_supported" if contexts else "context_limited",
        "contexts": contexts,
        "conditions": [],
        "basis": "tags_answer_signals_and_claim_context_labels",
    }


def _warning_report(chain: list[dict[str, object]], grounding: dict[str, object]) -> dict[str, object]:
    if not chain or grounding.get("answer_status") == "insufficient_evidence":
        return {"schema": "aoa_connector_warning_report_v1", "status": "insufficient_evidence", "warning_claim_ids": [], "risk_labels": []}
    warning_claim_ids = _warning_claim_ids(chain)
    warning_labels = _unique([label for step in chain for label in _strings(step.get("warning_labels", []))])
    return {
        "schema": "aoa_connector_warning_report_v1",
        "status": "warning_supported" if warning_claim_ids or warning_labels else "no_warning_claim_in_evidence",
        "warning_claim_ids": warning_claim_ids,
        "warning_labels": warning_labels,
        "risk_labels": _unique([label for label in warning_labels if label]),
    }


def _score_signal_report(chain: list[dict[str, object]]) -> dict[str, object]:
    accepted = [step.get("item_id") for step in chain if isinstance(step.get("stackoverflow"), dict) and step.get("stackoverflow", {}).get("is_accepted")]
    scored = [step for step in chain if step.get("source_score") is not None]
    return {
        "schema": "aoa_stackoverflow_score_signal_report_v1",
        "accepted_answer_item_ids": accepted,
        "scored_item_count": len(scored),
        "max_source_score": max([int(step.get("source_score")) for step in scored], default=None),
        "interpretation": "accepted answer and score are ranking/context signals, not truth predicates",
    }


def _agent_answer(
    query: object,
    chain: list[dict[str, object]],
    grounding: dict[str, object],
    conflict_report: dict[str, object],
    freshness_report: dict[str, object],
    warning_report: dict[str, object],
    score_report: dict[str, object],
) -> dict[str, object]:
    if not chain:
        text = "Local StackOverflow evidence is insufficient for this query."
    else:
        primary = chain[0]
        notes = [str(primary.get("summary") or "Local evidence found.")]
        if score_report.get("accepted_answer_item_ids"):
            notes.append("An accepted-answer signal is present, but it is not treated as final authority.")
        if warning_report.get("status") == "warning_supported":
            notes.append("Warning/comment evidence is present and must be carried with the answer.")
        if conflict_report.get("status") in {"conflict_detected", "possibly_superseded"}:
            notes.append("Conflict or supersession evidence is visible in the local claim graph.")
        if freshness_report.get("status") == "context_limited":
            notes.append("Duplicate or contextual linked-question evidence limits the answer scope.")
        text = " ".join(notes)
    return {
        "format": "deterministic_cited_brief_v1",
        "status": grounding.get("answer_status"),
        "language": "en",
        "query": query,
        "text": text,
        "citations": [
            {
                "ref": f"[{step.get('chain_step')}]",
                "role": step.get("role"),
                "question_id": step.get("question_id"),
                "answer_id": step.get("answer_id"),
                "comment_id": step.get("comment_id"),
                "item_id": step.get("item_id"),
                "source_url": step.get("source_url"),
                "created_at": step.get("created_at"),
                "last_edit_at": step.get("last_edit_at"),
                "captured_at": step.get("captured_at"),
            }
            for step in chain
        ],
        "freshness": freshness_report,
        "limitations": [] if chain else ["no_candidate_evidence"],
    }


def _answer_kind(claims: list[object], warning_labels: list[str], item_kind: str) -> str:
    kinds = {str(claim.get("claim_kind")) for claim in claims if isinstance(claim, dict)}
    if "warning" in kinds or warning_labels or item_kind == "comment":
        return "warning"
    if "status" in kinds:
        return "status_update"
    if "context" in kinds or item_kind == "linked_question":
        return "context"
    if "method" in kinds:
        return "method"
    return "snippet"


def _answer_text(answer_kind: str, result: dict[str, object], target_labels: list[str], tool_labels: list[str], context_labels: list[str]) -> str:
    target = ", ".join(target_labels) if target_labels else "the matched StackOverflow evidence"
    tools = ", ".join(tool_labels) if tool_labels else "the mentioned Python API"
    contexts = ", ".join(context_labels) if context_labels else "the local fixture context"
    if answer_kind == "warning":
        return f"Warning/context evidence applies to {target}; carry it with {tools} under {contexts}."
    if answer_kind == "status_update":
        return f"Freshness evidence affects {target}; review newer StackOverflow guidance before using older snippets."
    if answer_kind == "context":
        return f"Linked-question evidence adds context for {target}; use it to scope the answer."
    if answer_kind == "method":
        return f"Local StackOverflow evidence supports a method for {target} using {tools} under {contexts}."
    return str(result.get("snippet") or "Local StackOverflow evidence matched the query.")


def _claim_field_labels(claims: list[object], field: str) -> list[str]:
    labels: list[str] = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        labels.extend(_strings(claim.get(field, [])))
    return _unique(labels)


def _claim_freshness_windows(claims: list[object]) -> list[str]:
    values: list[str] = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        freshness = claim.get("freshness_context", {})
        if isinstance(freshness, dict) and freshness.get("profile_window"):
            values.append(str(freshness["profile_window"]))
    return _unique(values)


def _chain_relation_edges(chain: list[dict[str, object]]) -> list[dict[str, object]]:
    return [edge for step in chain for edge in step.get("claim_relation_edges", []) if isinstance(edge, dict)]


def _edge_claim_ids(edges: list[dict[str, object]], kinds: set[str]) -> list[str]:
    ids: list[str] = []
    for edge in edges:
        if edge.get("kind") not in kinds:
            continue
        for endpoint in [edge.get("from_node"), edge.get("to_node")]:
            value = str(endpoint or "")
            if value.startswith("claim:"):
                ids.append(value)
    return _unique(ids)


def _warning_claim_ids(chain: list[dict[str, object]]) -> list[str]:
    ids: list[str] = []
    for step in chain:
        if step.get("warning_labels"):
            ids.extend(_strings(step.get("claim_ids", [])))
    return _unique(ids)


def _strings(values: object) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    if isinstance(values, list):
        return [str(value) for value in values if value is not None]
    return [str(values)]


def _unique(values: list[str]) -> list[str]:
    unique: list[str] = []
    for value in values:
        if value and value not in unique:
            unique.append(value)
    return unique
