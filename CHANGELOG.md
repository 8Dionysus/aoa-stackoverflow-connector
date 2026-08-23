# Changelog

## Unreleased

## [0.1.1] - 2026-08-23

### Summary

Patch successor for the source and validation plane. The connector now
revalidates and pins the exact published `aoa-stats@v0.2.1` provider commit
`339ecb2db22ac4552fa88756b650896ebbff5b56` while preserving the immutable
`v0.1.0` release and its historical provider references.

### Changed

- Updated the consumer workflow and owner-local release contract to the exact
  `aoa-stats@v0.2.1` provider identity.
- Refreshed the repo-local KAG generated family for the successor source
  surface using the exact `aoa-kag@v0.5.0` owner-family gate.
- Advanced the package and source version markers to `0.1.1` for this patch
  successor.

### Fixed

- Removed the stale provider pin from the current consumer compatibility gate;
  the old `v0.1.0` tag and GitHub Release remain untouched.

### Compatibility and migration

- No breaking change is declared for connector packet schemas, CLI behavior,
  source policy, stats packet meaning, or runtime handoff fields.
- Consumers must bind the exact `v0.1.1` source release and independently
  perform their own artifact admission, deployment, runtime, proof, and
  acceptance checks.

### Validation

- Exact `aoa-stats@v0.2.1` source checkout passes the connector local stats
  port and targeted local stats tests.
- The complete connector validator, offline test suite, CLI checks, eval port,
  exact KAG owner-family gate, release dry-run, CI, tag, GitHub Release, and
  postpublish audit are recorded in the execution report.

### Notes, limitations, and non-claims

- This is a source-only patch release. It does not publish a package artifact,
  deploy a runtime, admit a consumer, establish central proof, or claim human
  acceptance or runtime health.
- Artifact trust verdicts remain owner-produced and are reported separately;
  no verdict is manually rewritten by this release.

## [0.1.0] - 2026-08-22

### Summary

Initial public source release of a bounded, read-only StackOverflow connector
skeleton. It provides policy-gated source modeling, deterministic offline
fixture proof, normalized evidence/claim/graph/answer packet schemas, a local
CLI, owner-local validation, local KAG indexes, a reference-only stats port,
and a fixture-driven evaluation contract.

This is intentionally a pre-1.0 release. It publishes method, code, schemas,
small sanitized fixtures, and validation surfaces; it does not publish a full
StackOverflow corpus or activate a live crawler or runtime MCP service.

### Added

- An independent connector repository and owner-local contract for bounded
  public StackOverflow question evidence.
- A public-route source policy for StackOverflow, the Stack Exchange API, and
  StackPrinter, with explicit denial of login, private/account, write,
  internal-search, and broad-crawl behavior.
- Parser and normalizer support for question, answer, comment, linked-question,
  item, and topic material, preserving source identifiers and evidence chains.
- Eighteen JSON schemas for normalized items, evidence, claims, graph,
  materialization receipts, quality reports, and answer packets.
- A deterministic synthetic/offline starter fixture and local materialization,
  full-text index, claim extraction, graph, answer packet, and eval skeleton.
- CLI commands for doctor, policy, fixture/index/graph construction, query,
  graph query, answer, source planning, and local eval operations.
- A local KAG provider home and canonical repository KAG index family.
- Portable v3 KAG manifest/content-addressed JSONL shards with deterministic
  v2 compatibility assembly and generated-size/migration receipts.
- An owner-local stats port with a reference packet and explicit authority
  ceilings.
- Owner CI and validator/test coverage for provider JSON, KAG parity, schema,
  digest, shard, compatibility, generated-budget, stats-port, and connector
  contracts.
- A bounded owner-local release route with a no-write dry-run, annotated-tag
  gate, canonical changelog publication, and postpublish identity audit.

### Changed

- KAG source/index data moved from tracked monoliths to the portable v3 family;
  this is a generated-state migration with compatibility assembly, not a
  declared answer-packet ABI break.
- The consumer workflow now validates against the exact published provider
  identities `aoa-kag@v0.5.0` (`813a7f69...`) and `aoa-stats@v0.2.0`
  (`dc608fd5...`), pinned by their resolved commits.
- KAG validation uses deterministic source/index parity, owner-family DAG
  checks, and generated-size budgets.
- Source planning is explicit and operator-local; live expansion remains a
  separately bounded operation.
- The future runtime integration boundary remains a documented `abyss-stack`
  read-only wrapper over already-built connector packets.

### Fixed

- Malformed provider JSON manifests are rejected with regression coverage.
- KAG source/index parity and deterministic refresh drift are checked by the
  owner validator and the pinned provider action.
- Generated KAG family references, digests, shards, compatibility assembly, and
  migration budgets are validated locally and in the landed workflow.

No security vulnerability fix or production incident fix is represented here;
these are correctness and gate improvements in the source/validation plane.

### Compatibility and migration

- No breaking change is declared for the connector answer-packet schema, CLI,
  source policy, or runtime handoff fields.
- The v2-to-v3 KAG representation migration removes tracked v2 monoliths and
  supplies deterministic compatibility assembly. Consumers must use the v3
  manifest/shard family or its compatibility route instead of assuming a
  monolith path.
- The future runtime consumer must bind this exact release tag and perform its
  own source, admission, deployment, and health checks before activation.

### Deprecated

- None is declared for the connector packet or CLI.
- Earlier tracked v2 KAG monolith paths are superseded by the v3 manifest and
  compatibility route.

### Removed

- Tracked v2 KAG monolith files were removed as part of the generated-family
  migration.
- No public source, answer/write, account, or runtime endpoint was removed;
  this repository never owned those routes.

### Security and privacy

- Read-only and network-disabled defaults are enforced for the starter path.
- No credential values, private data, raw large corpus, embedding/vector
  cache, graph database, or broad-crawl output is included.
- Login, private/account, write, internal-search, and broad-crawl routes are
  explicitly out of scope.
- Accepted-answer and score indicators remain evidence signals, not truth
  predicates.
- This source-only release has no SBOM, signature, external provenance
  attestation, package-registry artifact, or production security certification.

### Deployment, observability, recovery, and rollback

- Deployment and runtime/MCP serving remain owned by `abyss-stack`; this
  release does not deploy or activate a service.
- The stats port is a bounded reference read model and carries no runtime
  health, completeness, readiness, proof, or acceptance authority.
- The owner-local release route records exact tag/release identity. Consumer
  deployment, monitoring, recovery, and rollback must be designed and proven
  by the runtime owner when a consumer exists.

### Validation

The release candidate is based on the complete first-parent range ending at
the exact landed source commit. The final execution report records the exact
landed commit, provider tag identities, rerun results, and postpublish audit.

The owner validation contract covers:

- repository structure, schemas, KAG family, digests, shards, compatibility,
  and generated-size budgets;
- exact provider-tag compatibility for `aoa-kag@v0.5.0` and
  `aoa-stats@v0.2.0`;
- local stats-port validation against the exact `aoa-stats` tag checkout;
- local eval-port contract validation, without central proof promotion;
- CLI doctor/policy checks and the complete offline pytest suite;
- exact landed GitHub `validate` workflow checks after the release-prep PR;
- no-write owner release dry-run and postpublish tag/body/latest checks.

### Notes, limitations, and non-claims

- This is not a live StackOverflow coverage or crawl-readiness release.
- It does not prove source completeness, freshness, content correctness,
  accepted-answer correctness, score correctness, graph/index/answer quality,
  retrieval quality, or runtime health.
- It does not publish or activate `aoa-stackoverflow-connector-mcp`. That
  service belongs to `abyss-stack` and must consume an exact connector release
  after its own admission and runtime checks.
- It does not provide central `aoa-evals` proof, an eval verdict, deployment
  evidence, observability evidence, recovery execution, rollback execution, or
  human acceptance.
- A green CI check proves only the declared source validation contract. A
  release tag and GitHub Release prove publication identity only.
- No package artifact or attestation is claimed; any local build used for
  release evidence is not a published package.
- `aoa-session-memory` remains protected and untouched. Archived
  `aoa-routing` and `abyss-stack_old` remain untouched and unpublished.

### First-Parent Reconciliation (14/14)

The repository had no prior published SemVer baseline. The initial release
therefore reconciles every landed first-parent commit from the first source
commit through the release-preparation base. Each item remains separately
classified; grouped items are not silently omitted.

1. `e027af83a5d44cfa248f50beee0fa3adda6dc605` — direct main, “Create
   StackOverflow connector third-source proof” — **worthy / Added**: initial
   public connector skeleton, policy, parser/normalizer, schemas, fixture,
   local storage/index/graph/answer/eval surfaces, docs, CI, and tests.
2. `962b75c63e88015f0e9c2f17e6c6d581e4103481` — PR #1, “Add local KAG
   provider home” — **worthy / Added**, grouped with items 3–4: owner KAG
   provider records, source/storage boundaries, and validation integration.
3. `7b9e52678974f1e268e2558bf928f8d2eb233049` — PR #2, “Add repo-local KAG
   indexes” — **generated**, grouped with items 2–4: generated source index
   growth supports the provider surface and is not a separate user feature.
4. `8e523bcb1b2122a1982bcc3b3d81bc348ca9c208` — direct main, “Add operator
   source planning” — **worthy / Added**: source registry and plan commands
   are real operator-facing behavior.
5. `569592711bc57faf37cc27b832ee7f2f237945da` — PR #3, “Refresh repo-local
   KAG source index” — **generated**, grouped with items 2–4: deterministic
   index refresh, no new public capability.
6. `af6d8847aaad70bd8a11cc56da9d1061c152b8de` — PR #4, “Backfill live KAG
   source surface index” — **worthy / Changed**, grouped with KAG validation:
   source inventory, projection records, and validator contract.
7. `8970be908e1ad663fd24af82115b2969a7032f49` — PR #5, “Validate KAG
   provider JSON records” — **worthy / Fixed**: malformed-provider parsing and
   regression coverage.
8. `62cb16c45f15390c7975fc2678ac7ef5a1cb0688` — PR #6, “Enforce repo-local
   KAG index parity” — **worthy / Validation**: parity and action contract.
9. `cbd44c1a3349833c3d44c1dd90ca20ea913ad903` — PR #7, “Pin deterministic
   repo-local KAG index gate” — **internal**, grouped with validation: action
   pin and generated digest refresh, no standalone capability.
10. `2da4a9bfc84e3e1cfcc08e5b134f3c22df34a8f0` — PR #8, “Add repository KAG
    index family” — **worthy / Added**, grouped with item 11: artifact/entity/
    event index family and validation.
11. `43221ca5700687feefa2fce5dc809c9b80fe9372` — PR #9, “Publish canonical
    repository KAG indexes” — **worthy / Changed**, completion of item 10:
    canonical seven-file family and lineage-aware retrieval/federation contract.
12. `22546ecef31f9c2b6d2d5a328f3306ac7d80ddaa` — PR #10, “Add StackOverflow
    connector local stats port” — **worthy / Added**: owner-local reference
    statistics, packet, validator, tests, docs, and explicit authority limits.
13. `a239551bd629f59d32b59649eb308245be99c903` — PR #11, “Adopt portable KAG
    index family” — **worthy / Changed**: v3 manifest/content-addressed JSONL
    shards, v2 compatibility assembly, migration receipt, and removal of
    tracked v2 monoliths.
14. `164dc485724496b0edb65accb6092e109157d25e` — PR #12, “Pin accepted
    aoa-kag owner-family DAG” — **worthy / Changed**, grouped with item 13:
    final KAG action pin and manifest/shard refresh against the accepted
    owner-family DAG.

The non-landed branch snapshots `7e21307...`, `534159863...`, `27b7945...`,
and `30a8a774...` are intentionally excluded: they are not first-parent main
history or published artifacts. Release-preparation bookkeeping is recorded
in the execution report and is not presented as a product capability.
