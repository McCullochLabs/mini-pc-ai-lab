# Roadmap

## v1.0 operational scope

The existing CLI provides environment/model detection, conservative RAM admission, bounded Ollama requests, 1/2/4-client traffic, explicit warm-ups/repeats, system RAM/CPU and optional NVIDIA sampling, v2 results/checkpoints, reports and compatible comparisons. Legacy v1 fixtures remain readable. No additional dashboard, website, orchestration platform or maintenance service is needed.

A first single-request Windows CPU smoke observation is published, including failed task quality. See [release scope](docs/V1_RELEASE.md) and [actual result](benchmarks/results/baseline-2026-10-20.md).

## Project-informed extension

The static suite now includes nine tasks. Four original workflow-review fixtures cover dual release gates, crash-safe draft checkpointing, collision-safe imports and resource cleanup. They are runnable together through `benchmarks/configurations/workflow-reliability.json`. The [sanitized lessons and priorities](docs/PROJECT_DERIVED_LESSONS.md) explain why these were selected without copying private project material.

## Routine benchmarking and hardware acquisition

Use the documented protocol on accessible systems with adequate resources. Collect controlled repeated/warm results, then real 1/2/4-client observations when safe. Validate raw records, review metadata/disclosure and publish failures as well as useful outcomes. Compare only compatible protocols and preserve hardware/condition differences.

## Future evidence-dependent work

Real Linux, AMD/Intel GPU offload, NVIDIA acceleration, thermal/power instrumentation and additional donated/loaned systems need actual access. Model-process memory and backend queue timing need suitable independent instrumentation. Secure dynamic coding execution, Android build/device fixtures, crash recovery, migrations, document-package recovery and full agent orchestration remain separate future projects rather than prerequisites for this static toolkit. Generative media and conventional processing will remain distinct categories.

No automatic outreach, paid infrastructure, model downloading or forced feature expansion is planned. The project now transitions to normal evaluations and hardware acquisition rather than continued broad development.
