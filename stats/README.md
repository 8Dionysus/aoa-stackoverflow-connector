# aoa-stackoverflow-connector local stats port

This directory exposes statistical questions whose domain meaning belongs to
the StackOverflow connector. It uses the shared `aoa-stats` grammar without
moving StackOverflow source policy, evidence content, accepted-answer or score
interpretation, eval verdicts, or runtime state into the central stats organ.

## Current Reference Measurement

| Measurement | Question | Reference value |
| --- | --- | --- |
| `aoa-stackoverflow-connector/public-fixture-source-record-evidence-materialization-ratio` | What fraction of valid question, answer, comment, and linked-question records declared by the canonical public Stack Exchange-shaped starter fixture are materialized as normalized evidence items with matching source identity and policy-allowed source routes? | `10 / 10` at evidence revision `43221ca5700687feefa2fce5dc809c9b80fe9372` |

The population is a census of one question, three answers, four comments, and
two linked questions. Accepted status is an answer attribute, not a fifth
source-record kind. A record enters the numerator only when the normalizer emits
one evidence item with the expected item kind, parent identifiers, allowed
source URL, non-empty text, and Stack Exchange source-shape marker.

A missing item is an observed materialization gap, and a valid complete
population with no materialized items is an observed zero. Malformed or empty
source populations, duplicate identities, unsupported schemas, contradictory
normalized identities, or unexpected normalized items are unknown.

## Evidence Posture

The packet is a public, reference-only snapshot derived from the committed
sanitized fixture and the connector-owned normalizer. It contains counts and
source handles, not question, answer, comment, or linked-question text. It does
not read configured storage, live StackOverflow, generated indexes, graphs,
answer packets, or eval output.

## Authority

The ratio reports fixture structural evidence materialization only. It does not
establish content completeness or correctness, live-source coverage,
accepted-answer truth, score meaning, claim extraction, index or graph quality,
retrieval or answer quality, connector readiness, eval success, proof verdicts,
or runtime health.

## Surfaces

- `port.manifest.json` declares the owner-local question and measurement.
- `packets/public-fixture-source-record-evidence-materialization-ratio.reference.json`
  records the evidence-linked reference observation.
- the canonical starter fixture owns the source-record population;
- the normalizer and source policy own materialized evidence identity and
  allowed source routes;
- `aoa-stats` owns shared validation and cross-owner composition.
