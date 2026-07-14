# AGENTS.md

Route card for owner-local statistical questions in
`aoa-stackoverflow-connector`. Read the root `AGENTS.md` first.

## Applies To

Everything under `stats/`.

## Role

This directory owns bounded statistics over StackOverflow connector source and
evidence objects. Shared measurement grammar and cross-owner composition remain
owned by `aoa-stats`; eval verdicts remain owned by `aoa-evals`.

## Read Before Editing

1. Root `AGENTS.md`, `CHARTER.md`, `BOUNDARIES.md`, and `ROADMAP.md`.
2. The canonical starter fixture under `connector/fixtures/stackexchange/`.
3. The parser, normalizer, and source policy that own record identity and
   allowed source routes.
4. `docs/STARTER_PROOF.md`, `docs/ARCHITECTURE.md`, and `evals/AGENTS.md`.
5. `stats/README.md`, `stats/port.manifest.json`, and the central contracts
   under `aoa-stats/stats/`.

## Boundaries

- The population is the complete non-empty set of unique question, answer,
  comment, and linked-question records in the canonical public starter fixture.
- A source record enters the numerator only when one normalized evidence item
  preserves its expected kind, parent identities, policy-allowed source route,
  non-empty evidence text, and source-shape marker.
- A valid population with no materialized evidence items is an observed zero.
- A missing materialized item is an observed gap. Malformed, empty, duplicate,
  unsupported, contradictory, or unexpected input is unknown, not zero.
- Accepted-answer and score fields remain source signals and do not become
  truth through this measurement.
- The reference packet is weaker than the fixture, parser, normalizer, policy,
  executable tests, evals, and any live source evidence.
- Structural materialization does not prove content completeness, claim or
  answer correctness, retrieval quality, eval success, connector readiness, or
  runtime health.

## Validation

Inspect the fixture census, normalized identities, policy decisions, and packet
first. The port validator requires a compatible `aoa-stats` checkout through
`AOA_STATS_ROOT`, `.deps/aoa-stats`, or the workspace sibling route; CI supplies
its pinned checkout explicitly. Then run:

```bash
python scripts/validate_local_stats_port.py
python -m pytest -q tests/unit/test_local_stats_port.py
```

Use the root route for repository-wide validation.

## Closeout

Report the exact source-record population, materialized numerator, manual
positive and negative cases, packet posture, central validation, and repository
validation.
