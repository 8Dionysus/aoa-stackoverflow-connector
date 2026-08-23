from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "release_check.py"


def load_module():
    spec = importlib.util.spec_from_file_location("connector_release_check", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_release_contract_is_complete() -> None:
    result = load_module().validate()
    assert result["ok"] is True
    assert result["version_markers"] == {"pyproject": "0.1.2", "package": "0.1.2"}
    assert result["provider_pins"]["aoa-kag@v0.5.2"] == "8136d3eb629da28cea1206d13a8f1df52ee14739"
    assert result["provider_pins"]["aoa-stats@v0.2.2"] == "f119805cda69b3edeb2a4c5e407368d70e68650d"
    assert result["action_pins"]["aoa-kag/.github/actions/repo-local-kag-index"] == "8136d3eb629da28cea1206d13a8f1df52ee14739"


def test_release_section_is_canonical_and_human_first() -> None:
    section = load_module().release_section((ROOT / "CHANGELOG.md").read_text(), "0.1.2")
    assert section.startswith("## [0.1.2]")
    assert "aoa-stats@v0.2.2" in section
    assert "aoa-kag@v0.5.2" in section
    assert "runtime health" in section
