import json
import os
import subprocess
import sys


def _run(*args: str, env: dict[str, str] | None = None) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-m", "aoa_stackoverflow_connector.cli", *args],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    return json.loads(completed.stdout)


def test_cli_materialize_build_and_eval() -> None:
    materialize = _run("materialize", "fixture", "--run", "pytest-fixture")
    assert materialize["network_touched"] is False
    index = _run("build-index", "--run", "pytest-fixture")
    assert index["doc_count"] >= 8
    graph = _run("build-graph", "--run", "pytest-fixture")
    assert graph["claim_stats"]["claim_count"] >= 7
    assert graph["claim_stats"]["accepted_signal_count"] >= 1
    claim_eval = _run("eval", "claim-relations")
    assert claim_eval["status"] == "pass"
    answer_eval = _run("eval", "answer-packets")
    assert answer_eval["status"] == "pass"


def test_cli_sources_registry_plans_stackoverflow_fetch_scope(tmp_path) -> None:
    env = os.environ.copy()
    env["CONNECTOR_DATA_ROOT"] = str(tmp_path / "data")
    env["CONNECTOR_CACHE_ROOT"] = str(tmp_path / "cache")
    env["CONNECTOR_ARTIFACT_ROOT"] = str(tmp_path / "artifacts")

    question = _run(
        "sources",
        "add",
        "https://stackoverflow.com/questions/fixture-python-datetime-timezone-aware-utc",
        "--kind",
        "question",
        "--tags",
        "python,datetime",
        "--trust-score",
        "0.75",
        env=env,
    )
    assert question["status"] == "ok"
    assert question["source"]["access"] == "public"
    listed = _run("sources", "list", "--tag", "python", env=env)
    assert listed["selected_count"] == 1
    plan = _run("sources", "plan", "--run", "pytest-so-sources", "--limit", "10", env=env)
    assert plan["schema"] == "aoa_stackoverflow_source_fetch_plan_v1"
    assert plan["steps"][0]["operation"] == "fetch"
    assert plan["network_touched"] is False
