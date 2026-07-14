# Boundaries

## In Scope

- Public StackOverflow question pages.
- Public Stack Exchange API question, answer, comment, and linked-question
  routes.
- Public StackPrinter exports scoped to `service=stackoverflow`.
- Bounded starter profiles and seed manifests.
- Synthetic/sanitized fixtures that preserve source shape without copying full
  public posts into Git.
- Local indexes, graphs, claims, and answer packets built from allowed public
  snapshots.
- Connector-local eval suites that check behavior without central proof
  promotion.

## Out Of Scope

- Login, account, private inbox, user-specific, or write routes.
- Asking, answering, commenting, editing, voting, deleting, reviewing, or
  moderation routes.
- StackOverflow internal search as crawler or corpus source.
- Broad crawling or completeness claims.
- Treating accepted answers or scores as truth.
- Runtime MCP service ownership; that belongs in `abyss-stack`.
- Central eval verdicts; that belongs in `aoa-evals`.

## Public Repo Rule

The repo may include method, code, schemas, docs, small fixtures, and small
proof reports. It must not include full raw captures, large normalized corpora,
indexes, vector databases, graph databases, or generated caches.

## Local Statistics Boundary

The root `stats/` port may derive privacy-bounded measurements from public
fixtures and connector outputs. It does not own StackOverflow content,
accepted-answer or score truth, claim or answer correctness, eval verdicts,
connector readiness, or runtime state. Shared measurement grammar remains with
`aoa-stats`.
