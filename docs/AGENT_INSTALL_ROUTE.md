# Agent Install Route

An agent installing this connector should:

1. Read `AGENTS.md`, `BOUNDARIES.md`, `connector/SOURCE_POLICY.md`, and
   `connector/STORAGE_POLICY.md`.
2. Create an isolated Python environment and install the package and its
   development dependencies from `pyproject.toml`.
3. Follow the bounded operator route in `AGENTS.md`; the validator, tests, CLI
   parser, and CI workflow remain the executable owners.
4. Confirm the no-network fixture path before considering connected data.

The agent must not perform live StackOverflow network expansion unless explicitly asked
and given bounded public seed scope.
