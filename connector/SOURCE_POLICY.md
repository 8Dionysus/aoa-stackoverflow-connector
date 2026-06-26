# StackOverflow Source Policy

## Allowed

- Public StackOverflow question pages.
- Public Stack Exchange API read-only question, answer, comment, and linked
  question routes.
- Public StackPrinter exports scoped to StackOverflow.
- Public source URLs needed for evidence references.
- Bounded crawl windows explicitly listed in profile seeds.
- Synthetic/sanitized local fixtures that preserve public source shape.

## Forbidden

- Login, account, inbox, user-specific private, or account-gated pages.
- Write routes such as ask, answer, comment, edit, delete, vote, review, flag,
  or moderation actions.
- StackOverflow internal search as a crawler or corpus source.
- Hidden APIs or routes that bypass public source boundaries.
- Broad unbounded crawling.
- Treating accepted answers or score as final truth.

## Search Rule

Do not use StackOverflow internal search as the data source. Build local deep
search over allowed public snapshots.

## Runtime Rule

The starter proof is no-network and read-only. Any live expansion must be
bounded by a seed profile, produce receipts, and store generated artifacts
outside Git.
