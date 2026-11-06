# Roadmap

## Measured and runnable today

The Python CLI supports environment and Ollama detection, conservative RAM admission, bounded requests, configurable warm-ups and repetitions, system telemetry, checkpointed results and compatible comparisons. The static suite contains 13 original cases across nine categories. The [single measured CPU request](benchmarks/results/baseline-2026-10-20.md) completed and failed strict task grading. See the [operating guide](benchmarks/README.md) and [release scope](docs/V1_RELEASE.md).

## Establish repeatable workstation baselines

Acquire or borrow a [tier 1 system](docs/HARDWARE_WISHLIST.md), document its configuration and rerun the narrow baseline under fixed conditions. Measure cold and resident runs and then real 1/2/4-client serving under controlled memory pressure. Build an original Gradle/Godot test fixture with separate build, test and packaging timings. Add power and thermal readings when measurement is available.

## Validate acceleration and split-host operation

Use a tier 2 candidate to compare CPU and confirmed GPU placement at fixed model settings. Track quality, load time, memory residency, throughput and energy independently. Compare same-host and dedicated-host workflows while reporting server and client timings separately. Consider tier 3 only when the results show capacity or contention limits with a documented workload.

## Increase workflow fidelity

Prototype disposable test-generation and structured-output acceptance checks, then test forced interruption, resume, duplicate receipts and bounded fallback. Add an orchestration trial only when independent roles and acceptance can be observed end to end. Require an explicit run budget for extended sessions or heavy workloads. These are proposed studies. See the [workload plan](docs/REAL_WORLD_WORKLOADS.md).
