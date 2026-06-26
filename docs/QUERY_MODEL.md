# Query Model

The starter query model is deliberately small and deterministic.

## Keyword Index

The index tokenizes title, tags, question text, answer text, comment text, and
linked-question text. It preserves exact technical terms such as
`datetime.now(timezone.utc)`, `datetime.utcnow`, `replace(tzinfo=...)`,
`offset-naive`, and `offset-aware`, and ranks local evidence items by a
BM25-like term score plus exact technical term boosts.

## Graph Enrichment

`query-graph` attaches claim and relation context from the graph to each local
result:

- claim IDs
- relation kinds
- claim nodes
- source refs
- item IDs
- question/answer/comment IDs
- tag, score, accepted-answer, duplicate, and freshness context

## Insufficient Evidence

If a query lacks grounded local evidence, the answer renderer returns
`insufficient_evidence`. That is a successful result because it prevents the
agent from pretending the local database knows more than it does.
