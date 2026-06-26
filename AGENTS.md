# AGENTS.md

Root route card for `aoa-stackoverflow-connector`.

## Purpose

`aoa-stackoverflow-connector` is an AoA external-source connector skeleton for
local, policy-gated search, graph, claim, and answer evidence from public
StackOverflow question material.

The repository is GitHub-publishable method and code. It is not a corpus dump.

## Owner Lane

This repository owns:

- StackOverflow source policy and route allowlist/denylist
- StackOverflow question/answer/comment/linked-question parser and normalizer
- local keyword index, claim graph, answer packet, and eval skeletons
- small synthetic/sanitized fixtures and bounded starter profile routes
- connector-local validation and install route docs

It does not own:

- StackOverflow content or platform policy
- login, account, private, write, answer, comment, edit, delete, or search routes
- broad crawler operation or live corpus expansion
- full raw captures, large indexes, graph databases, embeddings, or caches
- runtime/MCP deployment, which belongs in `abyss-stack`
- central eval verdicts or proof doctrine, which belong in `aoa-evals`

## Start Here

1. `README.md`
2. `CHARTER.md`
3. `BOUNDARIES.md`
4. `connector/SOURCE_POLICY.md`
5. `connector/STORAGE_POLICY.md`
6. `docs/ARCHITECTURE.md`
7. `docs/RUNTIME_CONTRACT.md`
8. `docs/AGENT_INSTALL_ROUTE.md`
9. `docs/decisions/README.md`

Before large data, runtime, AI, or benchmark work, also read
`/etc/abyss-machine/AGENTS.md` and `/etc/abyss-machine/storage-policy.json`.

## Boundaries

- Do not run broad crawls unless the operator explicitly asks for a bounded
  public crawl.
- Do not use StackOverflow internal search as a crawler or corpus source.
- Do build local deep search over allowed public snapshots.
- Do not use login/account/private/write/answer/comment/edit/delete routes.
- Do not commit raw captures, indexes, graph DBs, vector stores, caches, or full
  exports.
- Treat accepted-answer and score signals as evidence context, not truth.
- The repo-local `.connector-state/` directory is an ignored workspace for
  small starter runs. Treat generated files inside it as local state, not source
  truth.

## Validation

Run from the repository root:

```bash
python scripts/validate_connector.py
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m aoa_stackoverflow_connector.cli doctor
PYTHONPATH=src python -m aoa_stackoverflow_connector.cli materialize fixture
PYTHONPATH=src python -m aoa_stackoverflow_connector.cli build-index --run starter-fixture
PYTHONPATH=src python -m aoa_stackoverflow_connector.cli build-graph --run starter-fixture
PYTHONPATH=src python -m aoa_stackoverflow_connector.cli eval claim-relations
PYTHONPATH=src python -m aoa_stackoverflow_connector.cli eval answer-packets
python /srv/AbyssOS/aoa-evals/scripts/validate_local_eval_port.py --target-root . --json
```

## Closeout

Report changed surfaces, validation results, skipped live crawl or storage
checks, and the next safe step. The first safe materialized step is
`aoa-stackoverflow materialize fixture`; any live StackOverflow expansion must
start from explicit bounded public seeds and keep generated data outside Git.
