# AOA-STACKOVERFLOW-D-0001: Separate Third-Source Connector Proof

## Status

Accepted.

## Context

The 4PDA connector proves deep public forum evidence over topic/post material.
The XDA connector proves that a second forum-like source can use the same
claim/report/answer-packet vocabulary without inheriting 4PDA policy and parser
details.

The next proof must not be another forum clone. StackOverflow has a different
source shape: questions, answers, accepted answers, comments, scores, tags,
duplicates/linked questions, edits, and freshness drift.

## Decision

Create `aoa-stackoverflow-connector` as a separate public-ready repository under
`/srv/AbyssOS/connectors/aoa-stackoverflow-connector`, with duplicated local
doctrine and the same connector-family claim/report vocabulary for now.

Use a synthetic/sanitized Stack Exchange API-shaped fixture for the starter
proof to avoid copying full StackOverflow post text into Git while preserving
question/answer/comment/link/score semantics.

Do not create a shared connector monorepo yet. Do not build a full StackOverflow
MCP before the connector proof exists.

## Options Considered

- Put StackOverflow inside `aoa-4pda-connector`: rejected because each source
  connector must remain independently publishable and grow its own data/storage
  route.
- Treat StackOverflow as another forum thread source: rejected because the goal
  is to stress the architecture with a different source model.
- Create a shared connector-family repo first: rejected because third-source
  proof should show what is actually shared before extracting doctrine.
- Create an independent StackOverflow repo with duplicated portable doctrine:
  chosen because it proves transfer while preserving source-specific ownership.

## Consequences

- StackOverflow owns its parser, source policy, profile, fixtures, local evals,
  and validator.
- 4PDA and XDA remain references, not parents.
- `abyss-stack` remains the future owner for `aoa-stackoverflow-connector-mcp`.
- `aoa-evals` remains proof doctrine owner; this repo owns only its local eval
  port and reports.
- Heavy generated state stays outside Git.
- Accepted answer and score are explicitly modeled as signals, not truth.

## Boundary Lenses

- Owner/source: this ADR is local to StackOverflow and references 4PDA, XDA,
  `aoa-evals`, and `abyss-stack` as separate owners.
- Portability/overlay: the claim vocabulary is portable; StackOverflow API
  fields, score/accepted-answer semantics, duplicate links, and fixtures are
  local adaptation.
- Lifecycle/time: shared doctrine extraction is deferred until duplication is
  harmful or another connector proves the common core.
