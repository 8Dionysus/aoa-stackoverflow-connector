"""Graph builder for normalized StackOverflow evidence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from aoa_stackoverflow_connector.claims import (
    assign_freshness_windows,
    claim_graph_stats,
    extract_item_claims,
    graph_nodes_for_claims,
    relation_edges_for_claims,
)


def build_graph(normalized_dir: Path, output_dir: Path, profile_id: str = "python-datetime-timezone") -> Path:
    nodes: dict[str, dict[str, object]] = {}
    edges: list[dict[str, object]] = []
    claims: list[dict[str, object]] = []
    for topic_path in sorted(normalized_dir.glob("topic-*.json")):
        topic = json.loads(topic_path.read_text(encoding="utf-8"))
        topic_node = f"topic:{topic['topic_id']}"
        nodes[topic_node] = _node(topic_node, "topic", str(topic.get("title", topic["topic_id"])), topic.get("source_url"), 1.0)
        for question in topic.get("questions", []):
            if not isinstance(question, dict):
                continue
            question_node = f"question:{question.get('question_id')}"
            nodes[question_node] = _node(question_node, "question", str(question.get("title") or question.get("question_id")), question.get("source_url"), 1.0)
            _append_edge(edges, "topic_contains_question", topic_node, question_node, question.get("source_url"), 1.0)
            for tag in question.get("tags", []):
                tag_node = f"tag:{tag}"
                nodes.setdefault(tag_node, _node(tag_node, "tag", str(tag), question.get("source_url"), 0.7))
                _append_edge(edges, "question_tagged_with", question_node, tag_node, question.get("source_url"), 0.7)
            if question.get("accepted_answer_id"):
                answer_node = f"item:answer:{question.get('accepted_answer_id')}"
                _append_edge(edges, "question_accepts_answer", question_node, answer_node, question.get("source_url"), 0.58)
        for item in topic.get("evidence_items", []):
            if not isinstance(item, dict):
                continue
            item_node = f"item:{item['item_id']}"
            nodes[item_node] = _node(item_node, str(item.get("item_kind") or "evidence_item"), _item_label(item), item.get("source_url"), 1.0)
            question_node = f"question:{item.get('question_id')}"
            _append_edge(edges, "question_contains_item", question_node, item_node, item.get("source_url"), 1.0)
            if item.get("answer_id"):
                answer_node = f"item:answer:{item.get('answer_id')}"
                if item_node != answer_node:
                    _append_edge(edges, "answer_has_comment", answer_node, item_node, item.get("source_url"), 0.75)
            if item.get("linked_question_id"):
                linked_node = f"question:{item.get('linked_question_id')}"
                nodes.setdefault(linked_node, _node(linked_node, "linked_question", _item_label(item), item.get("source_url"), 0.65))
                link_type = str(item.get("stackoverflow", {}).get("link_type") if isinstance(item.get("stackoverflow"), dict) else "related")
                _append_edge(edges, f"question_{link_type}_to", question_node, linked_node, item.get("source_url"), 0.6)
            for entity in item.get("entities", []):
                if not isinstance(entity, dict):
                    continue
                entity_node = _entity_node_id(entity)
                value = str(entity.get("value") or "")
                kind = str(entity.get("kind") or "term")
                nodes.setdefault(entity_node, _node(entity_node, kind, value, item.get("source_url"), 0.6))
                _append_edge(edges, "item_mentions_entity", item_node, entity_node, item.get("source_url"), 0.6)
            claims.extend(extract_item_claims(item, profile_id))

    assign_freshness_windows(claims)
    nodes.update(graph_nodes_for_claims(claims))
    claim_edges = relation_edges_for_claims(claims)
    edges.extend(claim_edges)
    stats = claim_graph_stats(claims, claim_edges)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "graph.json"
    payload = {
        "schema": "aoa_stackoverflow_graph_export_v1",
        "profile_id": profile_id,
        "built_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "claim_stats": stats,
        "nodes": list(nodes.values()),
        "edges": edges,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _node(node_id: str, kind: str, label: str, source_url: object, confidence: float) -> dict[str, object]:
    return {
        "schema": "aoa_stackoverflow_graph_node_v1",
        "node_id": node_id,
        "kind": kind,
        "label": label,
        "source_refs": [str(source_url or "")],
        "confidence": confidence,
    }


def _append_edge(edges: list[dict[str, object]], kind: str, from_node: str, to_node: str, source_url: object, confidence: float) -> None:
    edge_id = f"{from_node}->{to_node}:{kind}"
    if any(edge.get("edge_id") == edge_id for edge in edges):
        return
    edges.append(
        {
            "schema": "aoa_stackoverflow_graph_edge_v1",
            "edge_id": edge_id,
            "kind": kind,
            "from_node": from_node,
            "to_node": to_node,
            "source_refs": [str(source_url or "")],
            "confidence": confidence,
        }
    )


def _item_label(item: dict[str, object]) -> str:
    kind = str(item.get("item_kind") or "item")
    if item.get("answer_id"):
        return f"{kind} {item.get('answer_id')}"
    if item.get("comment_id"):
        return f"{kind} {item.get('comment_id')}"
    if item.get("linked_question_id"):
        return f"{kind} {item.get('linked_question_id')}"
    return f"{kind} {item.get('question_id')}"


def _entity_node_id(entity: dict[str, object]) -> str:
    return f"entity:{entity.get('kind', 'term')}:{entity.get('value', '')}"
