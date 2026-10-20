# Mini PC AI Lab

**Testing affordable hardware for real-world local AI development.**

## About Mini PC AI Lab

Mini PC AI Lab is a new independent initiative evaluating whether affordable compact computers can support useful local AI development. We prioritize reproducible workloads, task correctness, usable memory, compatibility and complete-system cost. We publish limitations and unsuccessful trials alongside useful findings.

## Current status

| Area | Available now |
|---|---|
| Implemented tools | Python inventory/checks, bounded Ollama streaming client, synthetic quality graders, 1/2/4-client request tests, JSON validation and Markdown reports |
| Validation | 19 automated tests using synthetic fixtures and a local mock HTTP service; no model required |
| Published observations | [Windows host inventory and three brief CPU/memory readings](benchmarks/results/readiness-2026-10-20.md) |
| Inference throughput, TTFT, model quality, concurrency | **Pending — not yet measured** |
| Sponsorships and comparison systems | None claimed |

The first identified host is a Core i5-8250U laptop with approximately 16 GB RAM and integrated UHD 620 graphics. At inspection, only 0.85–0.91 GiB physical memory was free and the default Ollama service was unavailable. Zero inference requests were submitted. File presence does not establish successful model loading or GPU acceleration. Fixture numbers are synthetic software checks and must never be used as hardware results.

## Real-World Development Experience

- **AI Retro Game Studio:** inspected Android application/build/test material, retained successful build and device-test receipts, and documented AI-assisted OpenCode development roles inform proposed coding, review and repair workloads. The retained XML snapshot reports 85 tests without failures/errors/skips; it was not rerun by this lab and does not authenticate a public release.
- **SladePuzzleCo:** a read-only observation of staged publishing review and inspected sample-only acceptance-check material inform original structured-content and quality-review fixtures. Stored statuses do not certify publishing readiness or commercial output quality.
- **MischiefToons:** source evidence was unavailable in the scoped investigation. Animation, media-processing and creative AI workloads remain proposals; no accomplishment or capability is inferred from the project name.

See the [technical portfolio](docs/TECHNICAL_PORTFOLIO.md), [sanitized evidence register](docs/EVIDENCE_REGISTER.md) and [workload plan](docs/REAL_WORLD_WORKLOADS.md). Private code, source assets, internal architecture, dashboards and raw evidence are excluded.

## Benchmark Categories

| Category | Scope and status |
|---|---|
| Ollama and local coding models | Client and two narrow synthetic quality tasks implemented; real-model measurements pending |
| CPU / integrated GPU / dedicated GPU inference | Planned backend-specific evaluations; placement and compatibility must be verified on each system |
| OpenCode-inspired workloads | Proposed original feature, test-generation, review and repair fixtures; no connection to private projects |
| Multi-agent concurrency | 1/2/4 simultaneous API clients implemented; actual agent coordination and server parallelism are separate, pending experiments |
| Memory limitations and stability | Host readiness snapshots available; inference peak memory and extended reliability pending |
| Power efficiency and thermals | Pending suitable instruments and approved controlled trials; no inferred power scores |

## Reproducibility

Use Python 3.10 or newer. No third-party Python dependency, model download or installation is required for fixture tests:

```powershell
python -m unittest discover -s tests -v
python scripts/check_repository.py
python scripts/lab.py run --fixture --output .local/fixture.json
python scripts/lab.py validate .local/fixture.json
python scripts/lab.py report .local/fixture.json --output .local/fixture.md
```

Read the [toolkit documentation](benchmarks/README.md), [methodology](BENCHMARK_METHODOLOGY.md), [result format](benchmarks/RESULT_FORMAT.md), [results template](RESULTS_TEMPLATE.md) and [test environment](docs/TEST_ENVIRONMENT.md). Real inference requires explicit opt-in and sufficient headroom; the toolkit never automatically pulls a model. Keep raw local outputs private until reviewed.

## Hardware Partnerships

Manufacturers, distributors, refurbishers and donors may offer evaluation units, temporary loaners, refurbished computers, donated systems or appropriate component support. A complete previous-generation system can answer useful questions. Supplied hardware does not guarantee favorable coverage, a publication schedule or audience reach.

See [partnership information](PARTNERSHIPS.md), the [evaluation proposal](outreach/MANUFACTURER_PROPOSAL.md) and [hardware wishlist](docs/HARDWARE_WISHLIST.md). Public GitHub issues can be used for an initial non-confidential inquiry; do not post shipping details, personal contact data or agreements there. No hardware arrangement has been accepted.

## Editorial Independence

All donations, loans, discounts and financial relationships will be disclosed. Partners may correct factual errors but cannot control conclusions or conceal unfavorable results. See the [editorial and disclosure policy](EDITORIAL_POLICY.md) and [roadmap](ROADMAP.md).

## Licensing

Original benchmark code and synthetic software fixtures: **MIT**. Original documentation, reports and the original proposed diagram: **CC BY 4.0**. Read [licensing boundaries](LICENSING.md); names and third-party rights are not relicensed. [Publication checks](docs/PUBLICATION_CHECKLIST.md) describe the public selection and privacy safeguards.
