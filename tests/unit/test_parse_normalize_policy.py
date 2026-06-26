import json
from pathlib import Path

from aoa_stackoverflow_connector.normalize import normalize_snapshot
from aoa_stackoverflow_connector.parse import extract_questions, load_question_bundle
from aoa_stackoverflow_connector.policy.rules import route_decision


FIXTURE_URL = "https://stackoverflow.com/questions/fixture-python-datetime-timezone-aware-utc"
FIXTURE = Path("connector/fixtures/stackexchange/python_datetime_timezone_question_bundle.json")


def test_parser_extracts_stackexchange_question_shape() -> None:
    bundle = load_question_bundle(FIXTURE)
    questions = extract_questions(bundle)
    assert len(questions) == 1
    question = questions[0]
    assert question["accepted_answer_id"] == "fixture-answer-aware-utc"
    assert len(question["answers"]) == 3
    assert len(question["linked_questions"]) == 2
    assert "offset-naive" in question["body_text"]
    assert "replace(tzinfo=...)" in question["answers"][0]["comments"][0]["body_text"]


def test_normalizer_extracts_stackoverflow_entities(tmp_path: Path) -> None:
    output = normalize_snapshot(FIXTURE, FIXTURE_URL, tmp_path)
    topic = json.loads(output.read_text(encoding="utf-8"))
    assert topic["schema"] == "aoa_stackoverflow_normalized_topic_v1"
    assert topic["topic_id"] == "python-datetime-timezone"
    assert len(topic["questions"]) == 1
    kinds = {item["item_kind"] for item in topic["evidence_items"]}
    assert {"question", "accepted_answer", "answer", "comment", "linked_question"}.issubset(kinds)
    text = json.dumps(topic, ensure_ascii=False)
    assert "datetime.now(timezone.utc)" in text
    assert "datetime.utcnow" in text
    assert "accepted_answer" in text
    assert "score_is_weak_signal" in text
    assert "duplicate" in text


def test_policy_denies_forbidden_routes() -> None:
    assert route_decision(FIXTURE_URL)["allowed"] is True
    assert route_decision("https://api.stackexchange.com/2.3/questions/1/answers?site=stackoverflow")["allowed"] is True
    assert route_decision("https://stackoverflow.com/search?q=datetime")["allowed"] is False
    assert route_decision("https://stackoverflow.com/users/login")["allowed"] is False
    assert route_decision("https://stackoverflow.com/questions/ask")["allowed"] is False
    assert route_decision("https://stackoverflow.com/posts/1/edit")["allowed"] is False
