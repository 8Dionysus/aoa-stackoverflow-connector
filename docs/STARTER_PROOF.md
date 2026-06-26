# Starter Proof

The starter proof uses a synthetic/sanitized Stack Exchange API-shaped fixture
for Python datetime timezone handling.

It proves:

- parser extracts question, answer, accepted-answer, comment, tag, score, edit,
  and linked-question fields
- normalizer emits source-grounded evidence items
- keyword index searches full question/answer/comment text, not only titles
- claim extractor produces method, warning, status, and context claims
- graph builder emits accepted-answer, score, duplicate, warning, conflict, and
  supersession relation semantics
- answer packet includes conflict, freshness, applicability, warning, and
  score-signal reports
- eval suites catch accepted-answer-as-signal, score-as-weak-signal, comment
  warnings, duplicate context, freshness supersession, conflicts, and
  insufficient evidence

It does not prove:

- full StackOverflow coverage
- live crawling readiness
- write/search/private route support
- completeness for Python datetime
- that accepted answers or high scores are truth
