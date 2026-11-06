# Technical portfolio

The lab uses original fixtures to approximate development work observed across Android, AI-assisted engineering and content production. Evidence classifications and verification limits are recorded in the [evidence register](EVIDENCE_REGISTER.md).

## Android development

**Inspected artifacts.** Kotlin/Gradle applications define JVM suites and debug APK builds, with Android instrumentation available in one application. Godot project workflows define headless checks and Android exports. Device QA contracts cover touch input, persistence and reproducible evidence collection. An Android project documents accessibility preferences and separates layout checks, physical-device validation and assistive-technology testing.

**Historical retained evidence.** Reports record debug builds, regression checks and physical-device sessions at specific milestones. Build and test outcomes can diverge even for the same commit. Large-text and TalkBack coverage requires an explicit, versioned device receipt. These findings motivate measuring compile, test and packaging times independently, and measuring development responsiveness during a concurrent model workload.

## AI-assisted engineering

**Inspected artifacts.** OpenCode role definitions separate implementation, testing, review and supervision. Configuration includes an OpenRouter route. Freebuff-related tooling provides synthetic orchestration and receipt validation, bounded provider fallback policies, restart controls and explicit handling of unknown token usage. Ollama code in the lab and a content tool supports local model requests. Model configuration, policy and retained synthetic checks establish separate levels of evidence from live routing or full autonomous operation.

**Proposed lab study.** Use isolated workloads to measure validation gates, repeated provider failures, retry budgets, checkpoint recovery and total accepted completions. Record tokens only where reported, distinguish provider errors from task failures and use simulated outages before live experiments.

## Content production

**Inspected artifacts.** Public puzzle-engine code and tests cover generated answers, corrupted output, PDF readback and editorial audit trails. Separately retained SladePuzzleCo observations cover staged review and sample-only acceptance checks. Historical activity-pack verification recorded rendering checks and preserved failures and skips.

**Proposed lab study.** Generate original puzzle and document fixtures, validate their constraints and answer keys, render the output and detect inconsistencies after packaging. Separate deterministic generation and PDF work from model-assisted review. Commercial assets and private project material stay out of public lab runs.

See the [workload plan](REAL_WORLD_WORKLOADS.md) and [project-derived lessons](PROJECT_DERIVED_LESSONS.md).
