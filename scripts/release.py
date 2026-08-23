#!/usr/bin/env python3
"""Owner-local dry-run, publication, and postpublish audit for one release."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from release_check import REPO_ROOT, release_section, validate


GITHUB_REPO = "8Dionysus/aoa-stackoverflow-connector"


class ReleaseError(RuntimeError):
    pass


def command(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise ReleaseError(f"command failed ({result.returncode}): {' '.join(args)}: {detail}")
    return result


def git(*args: str, check: bool = True) -> str:
    return command(["git", *args], check=check).stdout.strip()


def gh(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return command(["gh", *args], check=check)


def remote_json(endpoint: str) -> dict[str, Any] | list[Any]:
    result = gh("api", endpoint)
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ReleaseError(f"GitHub API returned invalid JSON for {endpoint}: {exc}") from exc
    if not isinstance(value, (dict, list)):
        raise ReleaseError(f"GitHub API returned an unexpected shape for {endpoint}")
    return value


def canonical_section(version: str) -> str:
    try:
        return release_section((REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), version)
    except (OSError, ValueError) as exc:
        raise ReleaseError(str(exc)) from exc


def release_check(version: str, tag: str) -> dict[str, Any]:
    result = validate(version=version, tag=tag)
    if not result["ok"]:
        raise ReleaseError("source release contract failed: " + "; ".join(result["errors"]))
    return result


def candidate_identity(expected_commit: str) -> dict[str, str]:
    head = git("rev-parse", "HEAD")
    branch = git("symbolic-ref", "--short", "HEAD", check=False)
    origin_main = git("rev-parse", "origin/main", check=False)
    status = git("status", "--porcelain")
    if branch != "main":
        raise ReleaseError(f"release candidate must be on main, observed {branch or '<detached>'}")
    if status:
        raise ReleaseError("release candidate worktree is dirty")
    if head != expected_commit:
        raise ReleaseError(f"HEAD {head} does not match expected landed commit {expected_commit}")
    if origin_main != expected_commit:
        raise ReleaseError(f"origin/main {origin_main} does not match expected landed commit {expected_commit}")
    return {"branch": branch, "head": head, "origin_main": origin_main}


def remote_tag_state(tag: str) -> dict[str, Any] | None:
    result = gh("api", f"repos/{GITHUB_REPO}/git/ref/tags/{tag}", check=False)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def remote_release_state(tag: str) -> dict[str, Any] | None:
    result = gh("api", f"repos/{GITHUB_REPO}/releases/tags/{tag}", check=False)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def assert_unpublished(tag: str) -> None:
    if remote_tag_state(tag) is not None:
        raise ReleaseError(f"remote tag {tag} already exists")
    if remote_release_state(tag) is not None:
        raise ReleaseError(f"GitHub Release for {tag} already exists")


def dry_run(version: str, tag: str, expected_commit: str) -> dict[str, Any]:
    source = release_check(version, tag)
    identity = candidate_identity(expected_commit)
    assert_unpublished(tag)
    return {
        "schema_version": "aoa_stackoverflow_release_dry_run_v1",
        "repo_id": "aoa-stackoverflow-connector",
        "ok": True,
        "version": version,
        "tag": tag,
        "candidate": identity,
        "source_contract": source,
        "publication": {"mode": "github_release_source_only", "tag_absent": True, "release_absent": True},
        "effects": [],
    }


def annotated_tag_commit(tag: str) -> tuple[str, str]:
    ref = remote_tag_state(tag)
    if not isinstance(ref, dict):
        raise ReleaseError(f"remote tag {tag} is absent")
    obj = ref.get("object")
    if not isinstance(obj, dict) or not isinstance(obj.get("sha"), str):
        raise ReleaseError(f"remote tag {tag} has no object identity")
    if obj.get("type") != "tag":
        raise ReleaseError(f"remote tag {tag} is not an annotated tag")
    tag_object = remote_json(f"repos/{GITHUB_REPO}/git/tags/{obj['sha']}")
    if not isinstance(tag_object, dict):
        raise ReleaseError(f"remote tag object for {tag} is malformed")
    target = tag_object.get("object")
    if not isinstance(target, dict) or target.get("type") != "commit" or not isinstance(target.get("sha"), str):
        raise ReleaseError(f"annotated tag {tag} does not peel to a commit")
    return obj["sha"], target["sha"]


def audit(version: str, tag: str, expected_commit: str) -> dict[str, Any]:
    source = release_check(version, tag)
    identity = candidate_identity(expected_commit)
    tag_object_sha, tag_commit = annotated_tag_commit(tag)
    if tag_commit != expected_commit:
        raise ReleaseError(f"tag {tag} peels to {tag_commit}, expected {expected_commit}")
    release = remote_release_state(tag)
    if not isinstance(release, dict):
        raise ReleaseError(f"GitHub Release for {tag} is absent")
    body = str(release.get("body") or "")
    expected_body = canonical_section(version)
    if body.rstrip() + "\n" != expected_body:
        raise ReleaseError("GitHub Release body does not match canonical CHANGELOG section")
    if release.get("draft") is not False or release.get("prerelease") is not False:
        raise ReleaseError("GitHub Release is draft or prerelease")
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise ReleaseError("GitHub Release assets field is malformed")
    latest = remote_json(f"repos/{GITHUB_REPO}/releases/latest")
    if not isinstance(latest, dict) or latest.get("tag_name") != tag:
        raise ReleaseError(f"latest release marker is not {tag}")
    return {
        "schema_version": "aoa_stackoverflow_release_postpublish_audit_v1",
        "repo_id": "aoa-stackoverflow-connector",
        "ok": True,
        "version": version,
        "tag": tag,
        "candidate": identity,
        "tag_identity": {"tag_object_sha": tag_object_sha, "commit": tag_commit},
        "release": {
            "id": release.get("id"),
            "url": release.get("html_url"),
            "published_at": release.get("published_at"),
            "draft": release.get("draft"),
            "prerelease": release.get("prerelease"),
            "latest_tag": latest.get("tag_name"),
            "asset_count": len(assets),
            "asset_attestation": "not_claimed_source_only_release",
        },
        "claim_limits": [
            "source publication integrity only",
            "no runtime deployment or health claim",
            "no consumer admission or central proof claim",
            "no human acceptance or rollback-execution claim",
        ],
    }


def publish(version: str, tag: str, expected_commit: str, confirm: bool) -> dict[str, Any]:
    if not confirm:
        raise ReleaseError("publish requires --confirm")
    source = release_check(version, tag)
    identity = candidate_identity(expected_commit)
    existing_tag = remote_tag_state(tag)
    existing_release = remote_release_state(tag)
    if existing_release is not None:
        raise ReleaseError(f"GitHub Release for {tag} already exists; refusing update")
    if existing_tag is None:
        git("tag", "--annotate", "--message", f"aoa-stackoverflow-connector {tag}", tag, expected_commit)
        command(["git", "push", "origin", f"refs/tags/{tag}"])
    else:
        _, existing_commit = annotated_tag_commit(tag)
        if existing_commit != expected_commit:
            raise ReleaseError(f"existing remote tag {tag} points to {existing_commit}, expected {expected_commit}")

    notes = canonical_section(version)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as stream:
        stream.write(notes)
        notes_path = Path(stream.name)
    try:
        gh(
            "release",
            "create",
            tag,
            "--repo",
            GITHUB_REPO,
            "--verify-tag",
            "--title",
            f"aoa-stackoverflow-connector {tag}",
            "--notes-file",
            str(notes_path),
            "--latest",
        )
    finally:
        notes_path.unlink(missing_ok=True)
    return {
        "schema_version": "aoa_stackoverflow_release_publish_v1",
        "repo_id": "aoa-stackoverflow-connector",
        "ok": True,
        "version": version,
        "tag": tag,
        "candidate": identity,
        "source_contract": source,
        "effects": ["annotated_tag_pushed", "github_release_created"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("dry-run", "publish", "audit"))
    parser.add_argument("--version", default="0.1.1")
    parser.add_argument("--tag", default="v0.1.1")
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "dry-run":
            result = dry_run(args.version, args.tag, args.expected_commit)
        elif args.command == "publish":
            result = publish(args.version, args.tag, args.expected_commit, args.confirm)
        else:
            result = audit(args.version, args.tag, args.expected_commit)
    except (ReleaseError, OSError, ValueError) as exc:
        if args.json:
            print(json.dumps({"schema_version": "aoa_stackoverflow_release_route_error_v1", "ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"release route failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) if args.json else "ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
