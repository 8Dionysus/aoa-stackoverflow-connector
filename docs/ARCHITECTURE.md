# Architecture

`aoa-stackoverflow-connector` is a source-specific adapter that implements a
portable connector-family runtime contract.

## Pipeline

```text
public-safe fixture or bounded StackOverflow question/API/StackPrinter snapshot
-> StackOverflow parser
-> normalized question/answer/comment/linked-question evidence items
-> keyword index
-> claim graph
-> evidence packet
-> answer packet
```

## Portable Layer

The following concepts are connector-family concepts:

- `claim`
- `claim_relation`
- `conflict_report`
- `freshness_report`
- `applicability_report`
- `warning_report`
- answer packet evidence chain
- `read_only=true`
- `network_touched=false`
- `insufficient_evidence`

## StackOverflow-Specific Layer

The following concepts are source/profile-specific:

- Stack Exchange API-shaped question bundle parsing
- StackOverflow route policy
- question, answer, accepted-answer, comment, tag, edit, score, and linked
  question fields
- accepted answer as strong but non-final signal
- score as weak crowd signal, not truth
- duplicate/related question graph context
- Python datetime starter profile and fixture shape

## No Premature Shared Repo

The portable doctrine is duplicated locally in connector repos for now. A
future shared `aoa-connectors` or connector-family doctrine repo should be
created only after several connectors prove which parts are truly common.

See `docs/CROSS_CONNECTOR_GENERALIZATION_REPORT.md` for the current 4PDA, XDA,
and StackOverflow comparison.

## Local Statistics

The root `stats/` port measures bounded properties of connector-authored source
and normalized evidence objects. Its current reference question is whether the
canonical public fixture's complete source-record census is materialized with
matching StackOverflow identities and policy-allowed source routes. The port
does not evaluate claim extraction, graph or answer quality, source truth,
readiness, or runtime behavior.
