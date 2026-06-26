# Cross-Connector Generalization Report

This report compares the current 4PDA, XDA, and StackOverflow connector proofs.

## Proof Inputs

| Connector | Source Shape | Proof Role |
| --- | --- | --- |
| `aoa-4pda-connector` | public forum topic/post pages | first deep forum evidence reference |
| `aoa-xda-connector` | public forum thread/post pages | second-source forum-like transfer proof |
| `aoa-stackoverflow-connector` | public question/answer/comment/link/score records | third-source non-forum-clone stress proof |

## Now Proven Portable

- `claim`
- `claim_relation`
- `conflict_report`
- `freshness_report`
- `applicability_report`
- `warning_report`
- answer packet evidence chain
- source refs and stable evidence item IDs
- `network_touched=false`
- `read_only=true`
- `insufficient_evidence`
- local eval port pattern under `evals/`
- fixture-first install and proof route
- heavy generated state outside Git

## Still Source-Specific

| Area | 4PDA | XDA | StackOverflow |
| --- | --- | --- | --- |
| Source unit | topic/post | thread/post | question/answer/comment/linked question |
| Route policy | 4PDA public topic routes | XDA public thread routes | StackOverflow question, Stack Exchange API, StackPrinter routes |
| Freshness signal | post chronology and profile refresh | post chronology and device build context | creation, edit, accepted answer, score, linked questions |
| Search source | local public snapshots | local public snapshots | local public question bundles |
| Risk source | forum warnings and device-specific risk | Android device/root warnings | comments, newer answers, deprecated API guidance |

## Should Stay Duplicated For Now

- source policy
- storage policy wording with source examples
- parser and normalizer code
- claim extraction heuristics
- local eval fixtures and cases
- CLI profile defaults
- docs that teach a fresh agent the source-specific route

Duplication is currently useful because it keeps each public connector forkable
and prevents a shared package from freezing 4PDA/XDA assumptions into
StackOverflow.

## Possible Future Extraction

Extraction may become justified if a fourth connector repeats the same code
pressure. Candidate shared surfaces:

- answer packet renderer interfaces
- claim relation schema vocabulary
- evidence packet query result envelope
- local eval port helper conventions
- storage-root discovery helper
- generated-artifact ignore/validator helper

Do not extract parser, source policy, profile seeds, or source-specific
heuristics.

## Owner Boundaries

| Surface | Owner |
| --- | --- |
| Connector source, schemas, fixtures, local evals | child connector repo |
| Runtime MCP service | `abyss-stack` |
| Central proof doctrine and verdicts | `aoa-evals` |
| Large generated data, indexes, graphs, caches | configured local/external storage roots |
| Host storage policy | `abyss-machine` |

## Next Goal Prepared

The next goal can be one of two routes:

- fourth-source proof with a different source shape
- shared connector-family package extraction, but only after another connector
  or repeated maintenance pressure proves the common core
