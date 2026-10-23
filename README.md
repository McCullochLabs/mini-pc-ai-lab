# Mini PC AI Lab

**Testing affordable hardware for real-world local AI development.**

Independent, reproducible evaluation of affordable computers for local AI. We report task correctness, useful performance, memory limits and failures without promising favorable findings or audience reach.

## Toolkit

**Detect → Configure → Validate → Benchmark → Record → Report**, using Python 3.10+ and its standard library. The existing CLI supports Windows/Linux inventory, Ollama detection/model listing, RAM admission checks, bounded single/concurrent requests, warm-ups/repeats, system telemetry, nine static coding/workflow-review tasks, validated JSON/Markdown reports and compatible-result comparison. No model is downloaded, generated code executed or result uploaded automatically.

```powershell
python scripts/lab.py check --probe-server
python scripts/lab.py models
python scripts/lab.py run --fixture --output .local/fixture.json
python scripts/lab.py report .local/fixture.json --output .local/fixture.md
```

Linux uses `python3`. See [Windows/Linux quick start, real runs and troubleshooting](benchmarks/README.md), [methodology](BENCHMARK_METHODOLOGY.md), [result format](benchmarks/RESULT_FORMAT.md) and [release validation/limitations](docs/V1_RELEASE.md). Real inference requires an existing local model, known memory headroom and explicit opt-in; heavier settings require an additional deliberate authorization flag.

## Actual results and limits

The [first real smoke observation](benchmarks/results/baseline-2026-10-20.md) used an i5-8250U laptop with approximately 16 GB RAM, Qwen2.5 3B Q4_K_M, Ollama 0.40.6 and two CPU threads. One request completed: **8.76 backend-reported generation tokens/s**, **14.62 s client latency including loading**, **strict task grade failed**. No favorable retry replaced it. This single observation does not establish general coding ability, steady-state speed or a hardware comparison.

The [earlier readiness record](benchmarks/results/readiness-2026-10-20.md) explains why inference was initially deferred. Memory headroom improved before the later trial. Old pending statements describe that earlier snapshot.

**56 automated tests** cover actual CLI/core behavior with synthetic/mock services and platform fixtures. Linux, AMD graphics and NVIDIA paths have mocked coverage; real hardware certification is not claimed. iGPU/dGPU inference, actual concurrent/repeated/warm-up trials, power, thermals, model-process peak memory and full agent orchestration remain **Pending — not yet measured**. The completed single request's backend reported CPU residency; GPU presence alone is not acceleration evidence.

## Real-World Development Experience

- **AI Retro Game Studio:** inspected Android development/build/test artifacts, retained validation receipts and documented OpenCode-assisted roles inform isolated coding/review tasks. Historical executions were not rerun or authenticated as a public release.
- **SladePuzzleCo:** a read-only staged review observation and separately inspected sample-only acceptance-check material inform synthetic content QA. Stored status does not certify publishing readiness or commercial output quality.
- **MischiefToons:** named with authorization; source evidence was unavailable. Creative accomplishments are not inferred from its name.

See the [portfolio](docs/TECHNICAL_PORTFOLIO.md), [sanitized evidence register](docs/EVIDENCE_REGISTER.md), [project-derived lessons](docs/PROJECT_DERIVED_LESSONS.md) and [workload plan](docs/REAL_WORLD_WORKLOADS.md). Private source, architecture, dashboards, commercial assets and raw evidence stay excluded. API client concurrency shares one model; it is not full multi-agent orchestration.

## Hardware partnerships and independence

Evaluation units, loaners, refurbished/open-box computers, donated systems and appropriate components can support useful studies. A complete previous-generation machine is welcome. No sponsorship, audience statistics or guaranteed coverage is claimed. See [partnerships](PARTNERSHIPS.md), [proposal](outreach/MANUFACTURER_PROPOSAL.md) and [wishlist](docs/HARDWARE_WISHLIST.md). An initial non-confidential GitHub issue is welcome; keep personal contact/shipping/agreement details private.

All hardware/financial support is disclosed; factual corrections are welcome, but partners cannot control conclusions or hide unfavorable findings. Read the [editorial policy](EDITORIAL_POLICY.md), [results template](RESULTS_TEMPLATE.md), [publication safeguards](docs/PUBLICATION_CHECKLIST.md) and [roadmap](ROADMAP.md).

Original code/software fixtures: **MIT**. Original documentation/report text/diagram: **CC BY 4.0**. [Licensing boundaries](LICENSING.md) preserve third-party rights and exclude private material.
