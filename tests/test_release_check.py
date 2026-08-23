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
    assert result["provider_pins"]["aoa-kag@v0.5.0"] == "813a7f69dc96ec031dad9b897a6991792cc48b7a"
    assert result["provider_pins"]["aoa-stats@v0.2.0"] == "dc608fd5de3fcaf0301f356c9efd52e2bdd350ce"


def test_release_section_is_canonical_and_human_first() -> None:
    section = load_module().release_section((ROOT / "CHANGELOG.md").read_text(), "0.1.0")
    assert section.startswith("## [0.1.0]")
    assert "First-Parent Reconciliation (14/14)" in section
    assert "runtime health" in section
