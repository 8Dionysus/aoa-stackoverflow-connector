# Charter

`aoa-stackoverflow-connector` exists to turn bounded public StackOverflow
question evidence into local, source-grounded packets an agent can query
without touching private, write, account-gated, or internal-search routes.

The charter is not to mirror StackOverflow. The charter is to preserve method,
contracts, fixtures, and evals so a local agent can install the connector,
materialize a small proof database, and later expand through bounded public
seeds.

## Success Shape

- public-ready repo skeleton
- explicit source and storage policy
- no-network fixture proof
- question/answer/comment/linked-question source model
- reusable connector-family claim vocabulary
- evidence chains with source URLs, item IDs, question/answer/comment IDs, and
  claim IDs
- accepted answer and score handled as signals, not truth
- local eval suites before live expansion
- heavy generated data excluded from Git
