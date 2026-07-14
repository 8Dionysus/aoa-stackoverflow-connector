# aoa-stackoverflow-connector

`aoa-stackoverflow-connector` is a GitHub-publishable AoA connector skeleton for
public StackOverflow question evidence. It is the third-source proof for the
connector family after 4PDA and XDA.

The point of this repo is not to mirror StackOverflow. It preserves method,
schemas, fixtures, source policy, local evals, and a deterministic starter
runtime that can build local search, graph, claim, and answer packets from a
bounded question bundle.

## What This Repository Does

| Function | Surface |
| --- | --- |
| Connector identity and boundaries | `CHARTER.md`, `BOUNDARIES.md` |
| Agent route and validation | `AGENTS.md` |
| Source policy | `connector/SOURCE_POLICY.md`, `connector/manifests/route_allowlist.yaml` |
| Storage contract | `connector/STORAGE_POLICY.md`, `.env.example` |
| Repo-local state scaffold | `.connector-state/` |
| Executable skeleton | `src/aoa_stackoverflow_connector/` |
| CLI entrypoint | `aoa-stackoverflow` |
| Schemas | `connector/schemas/` |
| Public-safe fixtures | `connector/fixtures/` |
| Local eval port | `evals/PORT.yaml`, `evals/suites/` |
| Starter profile and seeds | `connector/profiles/`, `connector/seeds/` |
| Runtime contract | `docs/RUNTIME_CONTRACT.md` |
| Cross-connector report | `docs/CROSS_CONNECTOR_GENERALIZATION_REPORT.md` |
| Validation | `scripts/validate_connector.py`, `tests/` |

## Bounded Operator Route

The short validation and no-network starter route lives in `AGENTS.md`.
Package metadata and the installed entry point live in `pyproject.toml`; exact
behavior remains with the CLI parser, repository validator, tests, and CI
workflow.

The default skeleton does not crawl StackOverflow. It materializes a tiny
synthetic/sanitized Stack Exchange API-shaped question bundle for no-network
proof work.

## Starter Profile

The first bounded proof profile is `python-datetime-timezone`. It models a
StackOverflow-shaped technical question with:

- question, answer, accepted answer, comment, tag, score, edit, and linked
  question fields
- an accepted answer that is useful but not absolute truth
- score/vote values treated as weak evidence signals
- comment warnings around `replace(tzinfo=...)`
- newer answer/edit language around `datetime.utcnow`
- duplicate/related question graph context
- an insufficient-evidence query path

## Search Posture

The connector must not use StackOverflow internal search as a crawler or data
source. It builds local deep search from allowed public snapshots:

```text
public question/API/StackPrinter snapshot
-> normalized question/answer/comment/linked-question evidence items
-> keyword index
-> claim graph
-> evidence packets
-> answer packets with source URLs, item IDs, question/answer/comment IDs, and claim IDs
```

## Storage Roots

Without environment variables, generated connector state goes to ignored
repo-local storage:

```text
.connector-state/data
.connector-state/cache
.connector-state/artifacts
```

For larger local runs, route generated state outside Git with the portable
variables defined by `connector/STORAGE_POLICY.md` and `.env.example`.

## Local Statistics

The root `stats/` port reports how much of the canonical public starter
fixture's question, answer, comment, and linked-question record population is
materialized as normalized evidence with matching source identity. It exports
only reference counts and owner evidence links. Source content, accepted-answer
and score interpretation, eval verdicts, retrieval quality, readiness, and
runtime truth remain with their owners.

## Current Status

Starter pipeline is offline and deterministic. It parses the fixture bundle,
normalizes evidence items, builds a keyword index, builds a claim graph, and
renders answer packets with conflict, freshness, applicability, warning, and
score-signal reports. Live StackOverflow expansion is intentionally deferred
until a bounded seed run is explicitly requested.
