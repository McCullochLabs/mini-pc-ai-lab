# Benchmark methodology

**Detect -> Configure -> Validate -> Benchmark -> Record -> Report.** Original fixtures isolate this work from private projects. Transport success, task correctness and speed are separate outcomes.

## Environment, admission and stopping

Collect allowlisted OS/CPU/RAM/GPU/software details without usernames, hostnames, serials, network identifiers or process lists. Hardware ID hashes selected specifications; it is not a serial or unique physical asset identity. Missing observations remain unavailable.

Detect installation, service reachability, model availability and backend residency separately. Never pull models or start services automatically. Preserve exact model digest/quantization, runtime version, context/output limits, seed, thread count, configuration and prompt digest.

RAM admission uses a conservative model-file-size/context/reserve estimate. It is an **estimate**, not measured allocation or an OOM guarantee, and may reject a model that could fit through offload/residency. Unknown/insufficient RAM fails closed. Severe/unknown availability stops new batches; existing unrelated processes are never terminated. Larger contexts/outputs, repeats, warm-ups, more clients and extended budgets need deliberate heavier-run opt-in.

Warm-up batches are recorded separately and excluded from measured tables. No forced cache flush/unload occurs; zero warm-ups does not prove a cold start. Use at least three measured repetitions for later controlled comparisons and document power mode, AC state, ambient conditions and background work. Tiny samples do not support stable percentiles or significance claims.

Socket timeouts include an elapsed guard; they are not exact server deadlines. The run budget stops new dispatch and drains in-flight requests. Interruption/error/budget status and completed batches are checkpointed locally. No background stress runner or hidden retry loop exists. A disconnected server can continue work.

## Measurement sources

| Metric | Source and interpretation |
|---|---|
| Request/batch latency | Actual client monotonic clock; includes connection, queue, model loading and transport |
| Output-fragment TTFT | Actual time to first nonempty response fragment; proxy rather than exact token timing; thinking ignored |
| Model loading | Backend-reported Ollama nanoseconds, separate from inclusive client latency |
| Token throughput | Backend counts divided by corresponding backend durations; zero duration gives null |
| Prompt throughput | Uncached prompt count/duration; absent cached count defaults to zero and needs version-aware interpretation |
| Aggregate throughput | Successful output tokens divided by actual batch wall time; not summed per-request rates |
| Client dispatch delay | Actual delay to worker start; not server queue time |
| RAM/CPU | Sampled OS-wide observations, not model/process allocation; sources/interval retained |
| NVIDIA memory/utilization | Optional existing `nvidia-smi`; not a generic Intel/AMD graphics counter |
| Residency | Backend `/api/ps` report; not independent utilization proof or automatic iGPU/dGPU classification |
| Admission requirement | Estimated conservative safety policy |
| Power, thermals, model-process peak RAM, server queue, full agent coordination | Unavailable without separate suitable instrumentation/workloads |

Sampled peaks can miss spikes. Windows available physical memory and Linux MemAvailable have different OS semantics. Shared integrated memory is not dedicated VRAM. GPU presence/NPU TOPS does not establish usable acceleration. Preserve backend support and placement limitations.

## Coding and synthetic agent traffic

Two narrow JSON review/content tasks and nine original static coding/workflow categories are implemented: feature, bug correction, tests, refactor, boundary review, release gates, draft persistence, import integrity and resource lifecycle. The four workflow reviews are original synthetic translations of patterns documented in the [project-derived lessons](docs/PROJECT_DERIVED_LESSONS.md), not copied source. Bounded JSON/AST contracts never execute/import generated code. Passing demonstrates the specified structure only; equivalent correct implementations can fail. It does not prove functional equivalence, crash recovery, migration safety, resource cleanup, mutation coverage or general coding strength. Trusted passing/failing/unsafe fixtures test graders independently of model output.

One/two/four API clients share one model. They measure demand, latency, throughput, errors and memory pressure; they do not establish autonomous OpenCode orchestration or independent model instances. Server queue time remains unavailable.

## Integrity, reports and comparisons

v2 records run identity/time, tool/config/prompt versions, sanitized environment, model provenance, admission estimate, warm-ups, resource observations, request outcomes, completion status, warnings and hardware disclosure. Legacy v1 fixtures remain readable. Validation checks structure/consistency, not cryptographic authenticity of server/operator claims.

Fixtures use a synthetic environment and remain unmistakably synthetic. Reports validate first, preserve incomplete/error status, separate correctness/speed, show metric sources and unavailable fields. Comparison requires compatible completed measured v2 runs; differences in model/quantization/settings/runtime/prompt/placement are refused. Different hardware and conditions remain explicit, without a universal score.

Review metadata and artifacts before manual publication. Disclose equipment ownership, donation/loan/financial terms and failures under the [editorial policy](EDITORIAL_POLICY.md). No automatic upload occurs.

## API references

Checked 2026-10-20: [generation](https://docs.ollama.com/api/generate), [streaming](https://docs.ollama.com/api/streaming), [model metadata](https://docs.ollama.com/api/tags), [version](https://docs.ollama.com/api/version) and [running models](https://docs.ollama.com/api/ps). Preserve actual runtime versions; support and fields can differ.

The revised workflow-review-v2 suite uses eight cases (four defective and four clean), with finite equivalent repair forms and separate protocol grading. Historical workflow results used answer-supplying prompts and are not independent defect-detection evidence. See the follow-up in project-derived lessons.
