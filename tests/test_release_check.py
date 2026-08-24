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
    assert result["version_markers"] == {"pyproject": "0.1.0", "package": "0.1.0"}
    assert result["provider_pins"]["aoa-kag@v0.5.0"] == "f46f146cc79a26fa81ad0f400b9c5774df293e57"
    assert result["provider_pins"]["aoa-stats@v0.2.0"] == "88ff38b1b38eef939f2c5b4541cbe8363a05fc8d"
    assert result["action_pins"]["aoa-kag/.github/actions/repo-local-kag-index"] == "f46f146cc79a26fa81ad0f400b9c5774df293e57"


def test_release_section_is_canonical_and_human_first() -> None:
    section = load_module().release_section((ROOT / "CHANGELOG.md").read_text(), "0.1.0")
    assert section.startswith("## [0.1.0]")
    assert "aoa-stats@v0.2.0" in section
    assert "aoa-kag@v0.5.0" in section
    assert "runtime health" in section
