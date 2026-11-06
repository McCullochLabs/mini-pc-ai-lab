# Sanitized evidence register

The first table preserves the 2026-10-20 inspection snapshot. Verification applies to source/artifact presence or retained receipt content, not newly rerun execution or authenticated historical provenance. Raw evidence, private paths and hashes are excluded.

| ID | Claim / source | Type | Status | Public disclosure | Benchmark relevance | Limits |
|---|---|---|---|---|---|---|
| E01 | Android application build/test material — AI Retro Game Studio | Source inspection | Verified | General summary only | Coding and build tasks | No public-release certification |
| E02 | Successful retained build receipt and APK presence — AI Retro Game Studio | Retained log/artifacts | Verified | Summary only | Build validation | Not rerun; source/build identity unauthenticated |
| E03 | Retained XML: 85 tests, zero failures/errors/skips — AI Retro Game Studio | Stored receipts | Verified | Aggregate only | Correctness gates | Older report says 73; snapshot distinction retained |
| E04 | Retained successful device-regression receipt — AI Retro Game Studio | Stored receipt | Verified | General summary | Regression checks | No fresh/physical-device execution |
| E05 | Automated validation and separate development/review roles — AI Retro Game Studio | Source/documentation | Verified | General workflow only | Review and validation | Does not certify all-agent execution |
| E06 | Historical pilot outcomes documented — AI Retro Game Studio | Narrative | Reported | Qualified summary only | Reliability questions | Not independently reproduced |
| E07 | Sample-only acceptance/evidence-integrity checks — development prototype | Source | Verified | General summary only | Structured QA | Not production integration or a fresh pass |
| E08 | Historical prototype pilot outcomes documented | Narrative | Reported | Qualified summary only | Bounded work | Execution not independently reproduced |
| E09 | Staged content review — SladePuzzleCo | Read-only observation | Verified | General workflow only | Synthetic content QA | Stored state is not publishing readiness |
| E10 | MischiefToons source not accessible | Access finding | Unavailable | Yes | Future creative tasks | No positive capability claim |
| E11 | Separate monitoring project not inspected | Access finding | Unavailable | General finding only | Future coordination | No integration claim |
| P01 | Synthetic workload research plan — Mini PC AI Lab | Proposed design | Planned | Original plan | Future tasks | Implemented subset documented separately |
| H01 | Host inventory and brief memory/CPU readings — Mini PC AI Lab | Direct observation | Historical retained evidence | Sanitized report | Baseline readiness | Zero inference requests; no performance claim |
| H02 | One Qwen2.5:3b Windows CPU smoke request; strict grade failed | Direct client/OS and backend observations | Historical retained evidence | Sanitized v2 record/report | Operational first baseline | One trial; no controlled comparison, no retained answer for independent regrading |

See [project summary](EXISTING_PROJECT_EVIDENCE.md), [implemented toolkit](../benchmarks/README.md) and [host observations](../benchmarks/results/readiness-2026-10-20.md). A fixture, roadmap or narrative cannot establish successful real execution.

## Follow-up inspection, 2026-10-25

L01-L04 in [project-derived lessons](PROJECT_DERIVED_LESSONS.md) record newly inspected local source/document evidence. These are source-inspection findings only, not fresh application test passes. Earlier entries retain their original inspection date; the private audit records current file presence and hash agreement separately. No new inference measurement was taken.

## GitHub inspection, 2026-11-06

| ID | Classification | Finding and provenance |
|---|---|---|
| G01 | Verified through inspected repository artifacts | Android game source declares Kotlin/JVM tests and a debug Gradle pipeline. OpenCode roles and an OpenRouter route are defined. Accessibility preference documentation specifies outstanding layout and assistive-technology validation. Private source locators are in the owner audit. |
| G02 | Historical retained evidence | A game milestone report records successful JVM and JavaScript tests and debug packaging, with a blocked check and separate UX evidence. GitHub recorded a failed Android workflow at the inspected remote head. These observations concern distinct execution contexts. |
| G03 | Verified through inspected repository artifacts | Godot Android export and headless suites are defined, alongside physical-device QA procedures with build identity, receipt checks and touch scenarios. A non-default branch documents development coordination. Private source locators are in the owner audit. |
| G04 | Historical retained evidence | Godot device QA reports describe earlier checkpoints. At the inspected default-branch SHA, GitHub recorded Android export success and a failed headless test workflow. The lab did not rerun these workflows. |
| G05 | Verified through inspected repository artifacts | A Kotlin Android application declares unit/instrumentation tests and debug APK workflows. GitHub records both successful and unsuccessful workflow outcomes across branch heads. Private source locators and recorded outcomes are in the owner audit. |
| G06 | Verified through inspected repository artifacts | A bridge repo contains synthetic orchestration, receipt verification and specifications for independent gates, bounded provider fallback and restart. Its latest report explicitly limits the evidence to qualified static inspection and retained regression results. Live activation and general execution remain outside the demonstrated scope. |
| G07 | Verified through inspected repository artifacts | The public puzzle engine includes [local Ollama routing](https://github.com/McCullochLabs/kdp-puzzle-engine/blob/8e054f2531971e9668e5df4bf89b7655de3579bc/publishing/studio_providers.py), [puzzle/PDF integrity tests](https://github.com/McCullochLabs/kdp-puzzle-engine/blob/8e054f2531971e9668e5df4bf89b7655de3579bc/tests/test_puzzle_integrity.py) and an [editorial review process](https://github.com/McCullochLabs/kdp-puzzle-engine/blob/8e054f2531971e9668e5df4bf89b7655de3579bc/docs/EDITORIAL_CONTENT_REVIEW.md). |
| G08 | Historical retained evidence | The public engine’s [activity-pack verification](https://github.com/McCullochLabs/kdp-puzzle-engine/blob/8e054f2531971e9668e5df4bf89b7655de3579bc/docs/ACTIVITY_PACK_VERIFICATION.md) records PDF checks and full-suite failures and skips. This evidence is separate from the historical SladePuzzleCo observation and commercial readiness. |
| G09 | Blocked or unavailable | No separate SladePuzzleCo GitHub repository was identified in the accessible inventory. Local-only development state and device receipts outside the repositories were unavailable. |
| V01 | Verified through current execution | All 59 toolkit tests passed on the pinned baseline and review copy with local mock-server connections enabled. This checks the toolkit using synthetic and mock inputs. |
| G10 | Planned or proposed | Controlled hardware, Android build, document QA and orchestration studies are specified in the [workload plan](REAL_WORLD_WORKLOADS.md). |

For the prior snapshot, “Verified” means inspected artifact or receipt content, “Reported” means owner-reported or narrative evidence without independent reproduction, and “Unavailable” means blocked or inaccessible.
