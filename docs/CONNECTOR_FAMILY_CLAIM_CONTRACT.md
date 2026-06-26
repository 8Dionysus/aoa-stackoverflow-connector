# Connector-Family Claim Contract

This document is duplicated locally while the connector family is still small.
It should stay vocabulary-compatible with 4PDA and XDA without importing their
source-specific assumptions.

## Claim

A claim is a source-grounded assertion extracted from a public evidence item.
For StackOverflow that item may be a question, answer, accepted answer, comment,
or linked question.

Every claim needs:

- stable `claim_id`
- `claim_kind`
- action label
- target/tool/context labels when available
- source item reference
- evidence span
- freshness context
- confidence basis

## Claim Relation

Contract key: `claim_relation`.

Claim relations make changing source evidence usable as a local knowledge base:

- source supports, warns about, updates, or links a claim
- a method uses a tool
- a method targets an object
- a warning targets an object or action
- a later claim supersedes an older claim
- claims contradict, contextualize, or scope-limit each other
- duplicate/linked questions contextualize a question

## Reports

The answer packet carries portable report families:

- `conflict_report`
- `freshness_report`
- `applicability_report`
- `warning_report`

The StackOverflow connector also carries `score_signal_report` as a
source-specific report. Accepted answer and score are useful signals, not truth.

## Insufficient Evidence

`insufficient_evidence` is a first-class successful state. It means local
evidence cannot safely support an answer.

## Source-Specific Boundary

Parsers, route policies, fixture choices, source URL shapes, API fields,
accepted-answer semantics, score semantics, duplicate-link semantics, and
extractor heuristics remain source-specific. Claim/report vocabulary is the
portable part.
