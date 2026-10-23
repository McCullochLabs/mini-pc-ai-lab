# Real-world workloads

These are proposed synthetic equivalents inspired by the [evidence register](EVIDENCE_REGISTER.md). They do not execute, copy, connect to or modify the existing projects. A configured prompt alone is not a completed end-to-end benchmark.

| Workload | Evidence inspiration | Isolated fixture and success criterion | Measurements | Status |
|---|---|---|---|---|
| Android feature repair | E01–E04 | Disposable Kotlin project with seeded state/reset defect; owner-supplied Android toolchain; hidden behavioral checks and build success | Wall time, valid patch rate, test/build overhead separately from inference | Planned advanced fixture |
| Code review | E05/E07 | Small original function with seeded defect and clean control; score known-defect precision/recall, including false positives | Inference latency, token rates, correctness | Planned evaluation |
| Test generation | E01/E07 | Original pure-function specification with seeded mutants; generated tests must pass correct implementation and reject mutants | Mutation detection, validity, elapsed time | Planned evaluation |
| Structured content QA | E07/E09 | Invented puzzle metadata and short text; reject missing fields, duplicate IDs and broken constraints | JSON/schema pass rate and semantic error rate separately | Planned evaluation |
| Bounded repair loop | E05/E07 | Original disposable fixture, fixed attempt budget, independent checks and final artifact hashes | Attempts, completion, failure class, total time | Planned orchestration |
| 1/2/4 simultaneous requests | Related multi-role design E05 | Same fixed prompt/model/context at bounded concurrency | Per-request latency, queueing, throughput, failure rate and memory when measurable | Planned serving evaluation |
| Dedicated local inference server | E05 validation design | Separate lab client and explicitly configured model host | Client-observed latency, model-server timings, network overhead separately | Planned topology |
| Extended coordination | E05/E08 | Disposable tasks with explicit stop budget and retained state | Task acceptance, recovery, contention and reliable completion | Planned; owner approval before extended stress |
| Workflow reliability review | Sanitized cross-project review | Four original static cases: dual gates, draft checkpointing, import identity collision and connection cleanup | Exact-contract correctness and inference metrics | Implemented static profile |

## Measurement boundaries

Concurrent requests to one model measure serving contention. They do not prove multiple autonomous agents, independent models or coordinated task completion. An agent benchmark additionally needs roles, task state, tool execution, independent acceptance and a complete trace. Prompt processing, generation, load time, client latency and build time must be reported separately. A plausible response that fails correctness is a failed task.

Use fixed prompts, model digest/quantization, input/output limits, warm/cold policy, repeated trials and raw receipts. Keep model quality and speed separate. Record inaccessible telemetry as unavailable, never zero. Network calls require an explicit local target; no production source or private assets enter prompts.

## Creative scope

MischiefToons source was unavailable. No image generation, video generation, conventional rendering or media-processing benchmark is claimed implemented or completed based on that project. If later added, keep all four separate from text inference, require original/licensed fixtures and independently record engine, quality, resolution and execution evidence. Conventional encoding/rendering cannot be presented as AI inference.

## Current implementation

The toolkit implements nine narrow static categories: original feature, bug correction, unit-test generation, refactoring, boundary review and four workflow-reliability reviews. These bounded JSON/AST contracts do not execute generated code or establish general semantic correctness. Trusted fixture pass/fail/unsafe samples validate the graders; the broader behavioral/build/mutation studies above remain proposed. One real legacy review request has a recorded failed strict grade; no real nine-task model suite or autonomous orchestration is claimed. See [project-derived lessons](PROJECT_DERIVED_LESSONS.md) for the sanitized rationale and the higher-fidelity backlog.

Consult [benchmark documentation](../benchmarks/README.md) for the actual toolkit commands and supported measurements. The table above is a research backlog; do not infer implementation from its inclusion here.
