# Install

## Executable Owners

`pyproject.toml` owns package metadata and the installed entry point.
`scripts/validate_connector.py` owns repository validation, the CLI parser owns
exact command syntax, and `.github/workflows/validate.yml` owns the required CI
sequence. The bounded operator route is kept in `AGENTS.md`.

## No-Network Starter Proof

After installation, follow the short route in `AGENTS.md`. It diagnoses local
storage, materializes the sanitized fixture, builds its index and graph, and
exercises the local eval surfaces without crawling StackOverflow.

## External Storage

For larger local runs, configure the portable roots defined by
`connector/STORAGE_POLICY.md` and `.env.example`. Generated state from those
roots remains outside Git.
