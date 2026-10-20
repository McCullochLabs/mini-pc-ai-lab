# Evaluation report template — no measurements entered

Status: planned / measured / fixture (select one). Never present this blank template as a completed evaluation.

- System/evaluation unit and acquisition terms:
- Test date, operator and protocol version:
- CPU; RAM capacity/type/channels; GPU/usable memory:
- OS/build; BIOS; drivers; power mode; AC/battery:
- Ollama version; model name; digest; quantization:
- Verified backend placement and verification tool:
- Context/output limits; seed; prompt revision; configuration file:
- Ambient conditions/background work:
- Cold/warm state; cache handling; run order:
- Raw JSON and reviewed inventory artifact:

| Workload | Clients | Samples | Success/fail | Quality passes | TTFT seconds | Generation tokens/s | Prompt tokens/s | Batch output tokens/s |
|---|---:|---:|---|---:|---|---|---|---|
| No data | — | — | — | — | — | — | — | — |

Report per-request values and range/median when justified by sample size. Include every failure and timeout. Mark each observation directly measured, server-reported, manually measured, estimated or unavailable. Do not turn missing metrics into zero.

| Additional metric | Value | Method/tool/version | Sampling/calibration | Limitation |
|---|---|---|---|---|
| Peak RAM/GPU memory | Unmeasured | — | — | No built-in telemetry |
| CPU/GPU utilization | Unmeasured | — | — | No built-in telemetry |
| Temperature/throttling | Unmeasured | — | — | No built-in telemetry |
| Wall power | Unmeasured | — | — | No built-in telemetry |

Discuss task correctness separately from inference speed. State that client concurrency does not establish multi-agent autonomy, server parallel execution, or ability to host several large models. Note small-sample, cache, thermal and software differences. Describe suitable workloads and observed limits only to the extent supported by data.

Hardware provision and affiliation disclosure:

Editorial review and correction history:

Owner publication approval: pending. Review [publication checklist](docs/PUBLICATION_CHECKLIST.md) before releasing any artifact.
