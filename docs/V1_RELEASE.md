# v1.0.0 release readiness

Assessment: **READY WITH LIMITATIONS**. The operational pipeline works, including a short real Windows CPU request. Hardware-dependent performance validation remains limited. A correctly recorded failed model grade is a valid benchmark outcome.

## Gap analysis

| Requirement | Initial audit | v1.0 outcome |
|---|---|---|
| Inventory | Partial | Windows/Linux normalization, available RAM and explicit unknowns |
| Backend/models | Partial | Installed/reachable distinction, model listing/selection, fit guard |
| Safe execution | Partial | Opt-ins, caps/budgets/threads, RAM refresh, no downloads |
| Resource metrics | Partial | Sourced system RAM/CPU, optional NVIDIA; absent counters null |
| 1/2/4 clients | Implemented | Existing behavior retained with additional safety |
| Coding tasks | Partial | Five original bounded static categories, no generated execution |
| Validation | v1 complete | Legacy compatibility plus v2 provenance/status/resource checks |
| Reports/comparison | Partial | Detailed Markdown and compatible-result comparison |
| Evidence sources | Partial | Actual/backend/estimated/unavailable/synthetic distinction |
| Portability | Partial | Mocked platform adapters, actual scope below |
| Privacy/isolation | Implemented | Exact public selection; local review and private files excluded |
| Operation | Partial | Existing CLI extended with direct options and concise guides |

No framework, dashboard, hosted application or orchestration platform was added. Original code remains MIT and original documentation/report text CC BY 4.0 under [licensing boundaries](../LICENSING.md).

## Validation scope

**55 tests passed**: 19 retained legacy, 13 v2 execution/schema/safety/report, 15 inventory/telemetry and 8 coding tests. These use trusted fixtures and local mock sockets, not model benchmarks. Coverage includes missing/unknown RAM, malformed inputs, heavy-run gates, warm-ups, concurrency, budget/interruption checkpoints, cleanup, source validation, report/comparison and unsafe-code rejection.

| Platform/capability | Actual validation |
|---|---|
| Windows x64 / i5-8250U / Python 3.13.15 | Actual inventory, OS RAM/CPU sampling and one Ollama request |
| Intel UHD620 | Actual identity only; acceleration/utilization unverified |
| Linux x64 | Mocked CPU/RAM/DRM behavior; no real host validation |
| AMD integrated graphics | Mocked identity; actual inference/counters pending |
| NVIDIA dedicated graphics | Mocked inventory/counters; actual runtime/VRAM pending |
| Concurrent/repeated/warm-up requests | Mock/fixture coverage; controlled real trials pending |
| Five coding categories | Trusted static pass/fail/unsafe samples; real model suite pending |

The [real smoke result](../benchmarks/results/baseline-2026-10-20.md) completed with failed strict quality. It does not establish general coding skill, steady-state speed or comparative hardware performance. Power, thermals, model-process peak memory, server queue isolation, dynamic code execution and full agents remain unmeasured/unsupported. Answers are not retained; the quality grade cannot be independently recomputed from this record alone.

## Release gates

- Existing remote/current commit verified; unrelated projects untouched.
- Essential detection, safety, execution, static grading, records and reports complete.
- Legacy/new automated tests pass; actual failed-quality observation retained.
- Fixture and clean-checkout workflow validated before publishing the stable tag.
- Docs, links, licenses, current/historical Git content and exact public selection reviewed.
- Private evidence, drafts, correspondence, raw service logs and credentials excluded.
- Hardware limitations explicit; no fabricated measurements or support claims.
- No model download, global setting change, unrelated process termination or manufacturer communication.

These are toolkit gates, not full hardware certification. The authorized stable tag is published only after all recorded checks pass. Safe tests/fixtures work without Ollama; real inference requires a running local runtime, an installed model and known memory headroom. Follow the [quick start and troubleshooting](../benchmarks/README.md). Routine evaluations and hardware acquisition are now the next work.
