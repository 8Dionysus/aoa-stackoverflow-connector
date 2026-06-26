# Runtime Contract

The StackOverflow connector runtime is read-only and no-network by default.

## Answer Packet

Answer packets must preserve:

- source URLs
- item IDs
- question IDs
- answer IDs and comment IDs when available
- claim IDs
- evidence_chain
- agent_answer
- `conflict_report`
- `freshness_report`
- `applicability_report`
- `warning_report`
- `score_signal_report`
- `network_touched=false`
- `read_only=true`

## Report Semantics

`conflict_report` explains whether primary evidence has supporting,
conflicting, superseding, or contextual evidence.

`freshness_report` explains whether the local evidence appears current,
possibly superseded, conflicting, context-limited, or insufficient.

`applicability_report` explains tags, version context, accepted-answer signal
context, score-signal context, and duplicate/related question context.

`warning_report` separates comment/risk evidence from ordinary answer advice.

`score_signal_report` carries StackOverflow-specific accepted-answer and score
signals. The accepted answer signal and score are never truth predicates.

`insufficient_evidence` means the connector refused to answer beyond its local
evidence. This is a valid output, not a failure.

## Future MCP Handoff

`abyss-stack` may later host `aoa-stackoverflow-connector-mcp`.

Allowed MCP tools should be thin read-only wrappers:

- status
- source route
- answer
- query graph
- query hybrid

Forbidden MCP tools:

- crawl
- refresh-build
- reindex
- write
- ask
- answer
- comment
- edit
- delete
- login
- private/account routes
- internal-search source route

The MCP wrapper must not own parser, crawler, graph, or answer logic.
