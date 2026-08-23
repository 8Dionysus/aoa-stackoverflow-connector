#!/usr/bin/env python3
"""Validate the source-owned release contract without network or mutation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PROVIDER_PINS = {
    "aoa-kag@v0.5.2": "8136d3eb629da28cea1206d13a8f1df52ee14739",
    "aoa-stats@v0.2.2": "f119805cda69b3edeb2a4c5e407368d70e68650d",
}
EXPECTED_ACTION_PINS = {
    "aoa-kag/.github/actions/repo-local-kag-index": "8136d3eb629da28cea1206d13a8f1df52ee14739",
}


def release_section(changelog: str, version: str) -> str:
    pattern = re.compile(rf"^## \[?{re.escape(version)}\]?[^\n]*\n", re.MULTILINE)
    match = pattern.search(changelog)
    if match is None:
        raise ValueError(f"CHANGELOG.md has no release section for {version}")
    next_heading = re.search(r"^## (?!#)[^\n]*\n", changelog[match.end() :], re.MULTILINE)
    end = match.end() + (next_heading.start() if next_heading else len(changelog[match.end() :]))
    section = changelog[match.start() : end].rstrip() + "\n"
    if len(section.splitlines()) < 4:
        raise ValueError(f"CHANGELOG.md release section for {version} is too short")
    return section


def _provider_pins(workflow: str) -> dict[str, str]:
    kag_match = re.search(
        r"#\s*Provider:\s*aoa-kag@v0\.5\.2,\s*resolved at\s*([0-9a-f]{40})",
        workflow,
    )
    stats_match = re.search(
        r"repository:\s*8Dionysus/aoa-stats.*?\n\s*#\s*Provider:\s*aoa-stats@v0\.2\.2,\s*resolved at\s*([0-9a-f]{40})",
        workflow,
        re.DOTALL,
    )
    return {
        "aoa-kag@v0.5.2": kag_match.group(1) if kag_match else "",
        "aoa-stats@v0.2.2": stats_match.group(1) if stats_match else "",
    }


def _action_pins(workflow: str) -> dict[str, str]:
    action_match = re.search(
        r"8Dionysus/aoa-kag/\.github/actions/repo-local-kag-index@([0-9a-f]{40})",
        workflow,
    )
    return {
        "aoa-kag/.github/actions/repo-local-kag-index": action_match.group(1)
        if action_match
        else ""
    }


def validate(*, version: str = "0.1.2", tag: str = "v0.1.2") -> dict[str, Any]:
    errors: list[str] = []
    pyproject_path = REPO_ROOT / "pyproject.toml"
    package_path = REPO_ROOT / "src" / "aoa_stackoverflow_connector" / "__init__.py"
    changelog_path = REPO_ROOT / "CHANGELOG.md"
    workflow_path = REPO_ROOT / ".github" / "workflows" / "validate.yml"

    try:
        project_version = str(tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"]["version"])
    except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        project_version = ""
        errors.append(f"cannot read project version: {exc}")

    package_text = package_path.read_text(encoding="utf-8") if package_path.is_file() else ""
    package_match = re.search(r'^__version__\s*=\s*[\"\']([^\"\']+)[\"\']\s*$', package_text, re.MULTILINE)
    package_version = package_match.group(1) if package_match else ""
    if project_version != version:
        errors.append(f"pyproject project.version is {project_version!r}, expected {version!r}")
    if package_version != version:
        errors.append(f"package __version__ is {package_version!r}, expected {version!r}")
    if project_version != package_version:
        errors.append("pyproject and package version markers disagree")

    try:
        section = release_section(changelog_path.read_text(encoding="utf-8"), version)
    except (OSError, ValueError) as exc:
        section = ""
        errors.append(str(exc))

    workflow = workflow_path.read_text(encoding="utf-8") if workflow_path.is_file() else ""
    pins = _provider_pins(workflow)
    action_pins = _action_pins(workflow)
    for dependency, expected in EXPECTED_PROVIDER_PINS.items():
        if pins.get(dependency) != expected:
            errors.append(f"workflow pin for {dependency} is {pins.get(dependency)!r}, expected {expected!r}")
    for action, expected in EXPECTED_ACTION_PINS.items():
        if action_pins.get(action) != expected:
            errors.append(f"workflow action pin for {action} is {action_pins.get(action)!r}, expected {expected!r}")

    if not tag.startswith("v") or tag[1:] != version:
        errors.append(f"tag {tag!r} does not match version {version!r}")

    return {
        "schema_version": "aoa_stackoverflow_release_check_v1",
        "repo_id": "aoa-stackoverflow-connector",
        "ok": not errors,
        "version": version,
        "tag": tag,
        "version_markers": {"pyproject": project_version, "package": package_version},
        "provider_pins": pins,
        "action_pins": action_pins,
        "release_section_sha256": f"sha256:{hashlib.sha256(section.encode()).hexdigest()}" if section else None,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="0.1.2")
    parser.add_argument("--tag", default="v0.1.2")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate(version=args.version, tag=args.tag)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("ok" if result["ok"] else "failed")
        for error in result["errors"]:
            print(f"error: {error}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
