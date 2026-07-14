from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

from aoa_stackoverflow_connector.normalize import normalize_snapshot
from aoa_stackoverflow_connector.policy.rules import route_decision


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    REPO_ROOT
    / "connector"
    / "fixtures"
    / "stackexchange"
    / "python_datetime_timezone_question_bundle.json"
)
FIXTURE_URL = "https://stackoverflow.com/questions/fixture-python-datetime-timezone-aware-utc"
PORT_PATH = REPO_ROOT / "stats" / "port.manifest.json"
PACKET_PATH = (
    REPO_ROOT
    / "stats"
    / "packets"
    / "public-fixture-source-record-evidence-materialization-ratio.reference.json"
)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_fixture(tmp_path: Path) -> dict[str, object]:
    path = normalize_snapshot(FIXTURE_PATH, FIXTURE_URL, tmp_path / "normalized")
    return load_json(path)


def _add_expected(
    expected: dict[str, dict[str, object]],
    *,
    item_id: object,
    item_kind: str,
    source_record_kind: str,
    question_id: object,
    source_url: object,
    evidence_text: object,
    answer_id: object = None,
    comment_id: object = None,
    linked_question_id: object = None,
) -> None:
    required = (item_id, item_kind, source_record_kind, question_id, source_url, evidence_text)
    if any(not isinstance(value, str) or not value.strip() for value in required):
        raise ValueError("malformed_source_record")
    if route_decision(str(source_url)).get("allowed") is not True:
        raise ValueError("disallowed_source_route")
    if item_id in expected:
        raise ValueError("duplicate_source_identity")
    expected[str(item_id)] = {
        "item_kind": item_kind,
        "source_record_kind": source_record_kind,
        "question_id": question_id,
        "answer_id": answer_id,
        "comment_id": comment_id,
        "linked_question_id": linked_question_id,
        "source_url": source_url,
    }


def _expected_records(fixture: object) -> dict[str, dict[str, object]]:
    if not isinstance(fixture, dict) or fixture.get("schema") != "aoa_stackoverflow_stackexchange_fixture_v1":
        raise ValueError("malformed_or_unsupported_fixture")
    questions = fixture.get("questions")
    if (
        not isinstance(questions, list)
        or not questions
        or any(not isinstance(question, dict) for question in questions)
    ):
        raise ValueError("malformed_or_empty_population")

    expected: dict[str, dict[str, object]] = {}
    for question in questions:
        question_id = question.get("question_id")
        source_url = question.get("link")
        _add_expected(
            expected,
            item_id=f"question:{question_id}",
            item_kind="question",
            source_record_kind="question",
            question_id=question_id,
            source_url=source_url,
            evidence_text=question.get("body_html") or question.get("body"),
        )

        answers = question.get("answers", [])
        comments = question.get("comments", [])
        linked_questions = question.get("linked_questions", [])
        if any(not isinstance(records, list) for records in (answers, comments, linked_questions)):
            raise ValueError("malformed_source_collection")

        for comment in comments:
            if not isinstance(comment, dict):
                raise ValueError("malformed_source_record")
            comment_id = comment.get("comment_id")
            _add_expected(
                expected,
                item_id=f"comment:{comment_id}",
                item_kind="comment",
                source_record_kind="comment",
                question_id=question_id,
                comment_id=comment_id,
                source_url=f"{source_url}#comment-{comment_id}",
                evidence_text=comment.get("body_html") or comment.get("body"),
            )

        for answer in answers:
            if not isinstance(answer, dict):
                raise ValueError("malformed_source_record")
            answer_id = answer.get("answer_id")
            answer_url = f"{source_url}#{answer_id}"
            _add_expected(
                expected,
                item_id=f"answer:{answer_id}",
                item_kind="accepted_answer" if answer.get("is_accepted") else "answer",
                source_record_kind="answer",
                question_id=question_id,
                answer_id=answer_id,
                source_url=answer_url,
                evidence_text=answer.get("body_html") or answer.get("body"),
            )
            answer_comments = answer.get("comments", [])
            if not isinstance(answer_comments, list):
                raise ValueError("malformed_source_collection")
            for comment in answer_comments:
                if not isinstance(comment, dict):
                    raise ValueError("malformed_source_record")
                comment_id = comment.get("comment_id")
                _add_expected(
                    expected,
                    item_id=f"comment:{comment_id}",
                    item_kind="comment",
                    source_record_kind="comment",
                    question_id=question_id,
                    answer_id=answer_id,
                    comment_id=comment_id,
                    source_url=f"{answer_url}#comment-{comment_id}",
                    evidence_text=comment.get("body_html") or comment.get("body"),
                )

        for linked in linked_questions:
            if not isinstance(linked, dict):
                raise ValueError("malformed_source_record")
            linked_question_id = linked.get("question_id")
            _add_expected(
                expected,
                item_id=f"linked:{linked_question_id}",
                item_kind="linked_question",
                source_record_kind="linked_question",
                question_id=question_id,
                linked_question_id=linked_question_id,
                source_url=linked.get("link"),
                evidence_text=linked.get("title"),
            )

    if not expected:
        raise ValueError("empty_population")
    return expected


def derive_source_record_materialization_ratio(
    fixture: object,
    normalized: object,
) -> dict[str, object]:
    try:
        expected = _expected_records(fixture)
    except ValueError as exc:
        return {"status": "unknown", "reason": str(exc)}

    if (
        not isinstance(normalized, dict)
        or normalized.get("schema") != "aoa_stackoverflow_normalized_topic_v1"
    ):
        return {"status": "unknown", "reason": "malformed_or_unsupported_normalized_snapshot"}
    items = normalized.get("evidence_items")
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        return {"status": "unknown", "reason": "malformed_normalized_collection"}

    materialized: dict[str, dict[str, object]] = {}
    for item in items:
        item_id = item.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            return {"status": "unknown", "reason": "malformed_normalized_identity"}
        if item_id in materialized:
            return {"status": "unknown", "reason": "duplicate_normalized_identity"}
        if item_id not in expected:
            return {"status": "unknown", "reason": "unexpected_normalized_identity"}

        contract = expected[item_id]
        for field in (
            "item_kind",
            "question_id",
            "answer_id",
            "comment_id",
            "linked_question_id",
            "source_url",
        ):
            if item.get(field) != contract[field]:
                return {
                    "status": "unknown",
                    "reason": f"contradictory_normalized_identity:{item_id}:{field}",
                }
        if (
            item.get("schema") != "aoa_stackoverflow_normalized_item_v1"
            or item.get("source_shape") != "stackexchange_api_question_bundle"
            or not isinstance(item.get("text"), str)
            or not str(item["text"]).strip()
            or not isinstance(item.get("captured_at"), str)
            or not item.get("captured_at")
        ):
            return {"status": "unknown", "reason": f"malformed_normalized_item:{item_id}"}
        materialized[item_id] = item

    expected_by_kind = Counter(
        str(record["source_record_kind"]) for record in expected.values()
    )
    materialized_by_kind = Counter(
        str(expected[item_id]["source_record_kind"]) for item_id in materialized
    )
    denominator = len(expected)
    numerator = len(materialized)
    return {
        "status": "observed",
        "numerator": numerator,
        "denominator": denominator,
        "ratio": numerator / denominator,
        "breakdown": {
            kind: {
                "materialized": materialized_by_kind[kind],
                "declared": expected_by_kind[kind],
            }
            for kind in sorted(expected_by_kind)
        },
        "gap_item_ids": sorted(set(expected) - set(materialized)),
    }


def test_reference_packet_matches_current_public_fixture_census(tmp_path: Path) -> None:
    derived = derive_source_record_materialization_ratio(
        load_json(FIXTURE_PATH),
        normalized_fixture(tmp_path),
    )
    packet = load_json(PACKET_PATH)

    assert derived == {
        "status": "observed",
        "numerator": 10,
        "denominator": 10,
        "ratio": 1.0,
        "breakdown": {
            "answer": {"materialized": 3, "declared": 3},
            "comment": {"materialized": 4, "declared": 4},
            "linked_question": {"materialized": 2, "declared": 2},
            "question": {"materialized": 1, "declared": 1},
        },
        "gap_item_ids": [],
    }
    assert packet["population"]["size"] == 10
    assert packet["sample"]["size"] == 10
    assert packet["value"] == {
        "status": "observed",
        "kind": "ratio",
        "unit": "1",
        "number": 1.0,
        "numerator": 10,
        "denominator": 10,
    }
    assert packet["progress"] == {"state": "terminal", "completed": 10, "total": 10}


def test_missing_normalized_item_is_an_observed_materialization_gap(tmp_path: Path) -> None:
    normalized = normalized_fixture(tmp_path)
    normalized["evidence_items"].pop()

    derived = derive_source_record_materialization_ratio(load_json(FIXTURE_PATH), normalized)

    assert derived["status"] == "observed"
    assert derived["numerator"] == 9
    assert derived["denominator"] == 10
    assert derived["ratio"] == 0.9
    assert derived["gap_item_ids"] == ["linked:fixture-related-zoneinfo"]


def test_complete_population_without_materialized_items_is_observed_zero(tmp_path: Path) -> None:
    normalized = normalized_fixture(tmp_path)
    normalized["evidence_items"] = []

    derived = derive_source_record_materialization_ratio(load_json(FIXTURE_PATH), normalized)

    assert derived["status"] == "observed"
    assert derived["numerator"] == 0
    assert derived["denominator"] == 10
    assert derived["ratio"] == 0.0


def test_malformed_duplicate_contradictory_and_unsupported_inputs_are_unknown(
    tmp_path: Path,
) -> None:
    fixture = load_json(FIXTURE_PATH)
    normalized = normalized_fixture(tmp_path)

    duplicate_normalized = deepcopy(normalized)
    duplicate_normalized["evidence_items"].append(
        deepcopy(duplicate_normalized["evidence_items"][0])
    )
    contradictory = deepcopy(normalized)
    contradictory["evidence_items"][1]["answer_id"] = "other-answer"
    unexpected = deepcopy(normalized)
    extra = deepcopy(unexpected["evidence_items"][0])
    extra["item_id"] = "question:unexpected"
    unexpected["evidence_items"].append(extra)
    duplicate_source = deepcopy(fixture)
    duplicate_source["questions"][0]["answers"][1]["answer_id"] = duplicate_source[
        "questions"
    ][0]["answers"][0]["answer_id"]
    empty = deepcopy(fixture)
    empty["questions"] = []
    unsupported_fixture = deepcopy(fixture)
    unsupported_fixture["schema"] = "aoa_stackoverflow_stackexchange_fixture_v2"
    unsupported_normalized = deepcopy(normalized)
    unsupported_normalized["schema"] = "aoa_stackoverflow_normalized_topic_v2"

    cases = (
        derive_source_record_materialization_ratio(None, normalized),
        derive_source_record_materialization_ratio(empty, normalized),
        derive_source_record_materialization_ratio(duplicate_source, normalized),
        derive_source_record_materialization_ratio(unsupported_fixture, normalized),
        derive_source_record_materialization_ratio(fixture, {"schema": "wrong"}),
        derive_source_record_materialization_ratio(fixture, duplicate_normalized),
        derive_source_record_materialization_ratio(fixture, contradictory),
        derive_source_record_materialization_ratio(fixture, unexpected),
        derive_source_record_materialization_ratio(fixture, unsupported_normalized),
    )

    assert all(case["status"] == "unknown" for case in cases)


def test_measurement_stays_reference_only_and_below_source_eval_and_runtime_authority() -> None:
    port = load_json(PORT_PATH)
    measurement = port["measurements"][0]
    ceiling = measurement["authority_ceiling"]
    packet = load_json(PACKET_PATH)

    assert port["evidence_posture"] == {
        "live_state": "reference_only",
        "privacy": "public",
        "raw_content_allowed": False,
    }
    assert measurement["live_state"] == {"capability": "reference_only"}
    assert measurement["aggregation"] == {
        "operator": "ratio_of_sums",
        "across": ["dimension"],
    }
    assert measurement["dimensions"]["allowed"] == [
        {
            "name": "source_record_kind",
            "max_cardinality": 4,
            "sensitivity": "public",
        }
    ]
    assert "live-source coverage" in ceiling
    assert "accepted-answer truth" in ceiling
    assert "answer quality" in ceiling
    assert "eval success" in ceiling
    assert packet["posture"]["raw_content_included"] is False
