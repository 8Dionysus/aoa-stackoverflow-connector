# Releasing `aoa-stackoverflow-connector`

This guide defines the bounded owner-local publication route for the connector.
The repository is a source/method release: its release identity is the
canonical `CHANGELOG.md` section, an annotated SemVer tag, and the matching
GitHub Release. No package registry publication or runtime deployment is
implied.

## Release boundaries

- Publish method, code, schemas, small sanitized fixtures, local validation,
  and the bounded KAG/stats owner surfaces.
- Keep raw StackOverflow captures, broad crawls, private/account/write routes,
  runtime MCP activation, central proof, and human acceptance outside this
  release's authority.
- Keep provider dependencies exact and provider-before-consumer:

  | Surface | Published tag | Resolved commit |
  | --- | --- | --- |
  | `8Dionysus/aoa-kag` provider | `v0.5.0` | `f46f146cc79a26fa81ad0f400b9c5774df293e57` |
  | `8Dionysus/aoa-kag` action `repo-local-kag-index` | not a provider tag | `f46f146cc79a26fa81ad0f400b9c5774df293e57` |
  | `8Dionysus/aoa-stats` provider | `v0.2.0` | `88ff38b1b38eef939f2c5b4541cbe8363a05fc8d` |

  The workflow declares the provider tag/commit identities separately from
  the KAG action identity. Release preparation must verify that each provider
  commit is the object named by its published tag, that the action reference
  resolves to the declared action commit, and must run the consumer checks
  against fresh checkouts of the provider tags.

The shared `aoa release` federation route does not currently register this
connector as an SDK-paired owner. Do not widen that sibling-owned registry as
a release shortcut. The owner-local script below is the authoritative route
for this repository until an explicit owner change admits it to federation.

## Preparation and validation

1. Start from a clean worktree based on current `origin/main` and move the
   complete landed range into the versioned changelog. Preserve the
   `First-Parent Reconciliation` ledger whenever reconciling an initial
   release.
2. Keep `pyproject.toml` and
   `src/aoa_stackoverflow_connector/__init__.py` at the same version. Do not
   invent duplicate version fields in schemas or generated manifests.
3. Run the owner route against exact provider tag checkouts: `AOA_STATS_ROOT=.deps/aoa-stats python scripts/validate_local_stats_port.py`, `python scripts/validate_connector.py`, `PYTHONPATH=src python -m pytest -q`, `PYTHONPATH=src python -m aoa_stackoverflow_connector.cli doctor`, `PYTHONPATH=src python -m aoa_stackoverflow_connector.cli policy check`, and `python /srv/AbyssOS/aoa-evals/scripts/validate_local_eval_port.py --target-root . --json`.

4. Run the exact KAG owner-family gate from the checkout of
   `aoa-kag@v0.5.0`, using the separately pinned
   `repo-local-kag-index@f46f146cc79a26fa81ad0f400b9c5774df293e57` action
   identity. The KAG gate is a generated/provider validation claim;
   it is not runtime health, proof, or acceptance.
5. Build a source-only sdist/wheel in a task-local directory if artifact
   evidence is needed. Hash and inspect those files, but do not describe them
   as published or trusted external artifacts unless an owner registry and
   attestation actually admit them.

## Owner-local dry-run and publication

The script is intentionally fail-closed and does not mutate with `dry-run`:
run `python scripts/release.py dry-run --version 0.1.0 --tag v0.1.0 --expected-commit <exact-landed-main-sha> --json`.

The dry-run verifies the branch, clean tree, exact `origin/main` identity,
version markers, canonical changelog section, provider pins, absent remote
tag/release, and source-only release posture. It is the owner-local strict
preflight for this non-federated repository.

Only after the dry-run passes and the exact commit is on `main`, publish with
the explicit mutation gate `python scripts/release.py publish --version 0.1.0 --tag v0.1.0 --expected-commit <exact-landed-main-sha> --confirm --json`.

The command creates an annotated tag at the exact landed commit, pushes only
that tag, and creates a non-draft, non-prerelease GitHub Release whose body is
the exact canonical changelog section. It creates no package-registry asset.
If the tag push succeeds but release creation fails, rerun the same command
only after inspecting the exact tag identity; the script will not retag a
different commit.

On hosts whose system SSH configuration is not usable, keep the workaround
explicit at the command boundary rather than changing repository remotes. Use
`GIT_SSH_COMMAND='ssh -F /dev/null' python scripts/release.py publish --version 0.1.0 --tag v0.1.0 --expected-commit <exact-landed-main-sha> --confirm --json`.

## Postpublish audit

Run the audit separately on the published state with `python scripts/release.py audit --version 0.1.0 --tag v0.1.0 --expected-commit <exact-landed-main-sha> --json`.

The audit checks the annotated tag object and peeled commit, release body,
release URL, published/non-prerelease/latest semantics, absence of unexpected
assets, and the local `main`/`origin/main` clean identity. A successful audit
proves source publication integrity only. It does not prove runtime binding,
deployment, health, consumer admission, central eval proof, rollback
execution, or human acceptance.
