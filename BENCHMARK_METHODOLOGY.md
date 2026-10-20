# Benchmark methodology v1

Status: implemented synthetic workloads and fixture-tested local Ollama client; **no hardware inference results yet**. Fixture artifacts are prominently marked and excluded from comparisons.

Record each system's CPU, memory capacity/type/channels, GPU and usable dedicated/shared memory, OS build, BIOS/power mode, driver versions, Ollama version, exact model name/digest, quantization, prompt version, context/output limits and seed. Document ambient temperature, AC/battery state, background work and cooling. Inventory is allowlisted and may be incomplete; unknown means unknown. An advertised NPU TOPS value does not establish Ollama support or inference performance. Check backend placement independently before describing a run as CPU, iGPU or dedicated GPU inference.

## Implemented protocol

1. Obtain authorization for the bounded run; use the smallest installed suitable model. Never auto-install or pull a model.
2. Run read-only checks and inventory; review the data. Copy the smoke configuration, set the exact installed name, and retain the configuration with results.
3. Run two synthetic workloads at concurrency 1. No hidden warm-up is performed. The first request may load the model; subsequent requests may be warm. Label this mixed state explicitly. For publication, run separately labeled cold and warm sessions with documented cache state; the toolkit does not force unload or flush caches.
4. If separately approved, use concurrency 1, 2 and 4. Each batch launches that many requests to **one model**; successive workloads/repeats run in sequence. Record all failures; do not drop slow or failed requests.
5. Validate JSON, generate Markdown, attach the reviewed environment and manual readings, then review the publication checklist. Do not compare fixture data with measured systems.

## Metrics and interpretation

Client wall time uses a monotonic performance clock. TTFT is elapsed client time until the first nonempty `response` fragment, including connection, queue, model loading and transport. It is an output-fragment proxy; thinking output is ignored. No fragment yields null. It is not exact tokenizer-level first-token timing.

The final Ollama streaming object supplies nanosecond total/load/evaluation durations and token counts. Generation throughput is `eval_count * 1e9 / eval_duration`. Prompt throughput uses `(prompt_eval_count - prompt_eval_cached_count) * 1e9 / prompt_eval_duration`; absent cached count defaults to zero and should be treated cautiously across versions. Zero durations yield null throughput. Client batch throughput is total output tokens from successful requests divided by batch wall seconds; it includes queue/connection time and pool startup. Do not sum individual generation rates to claim aggregate serving speed. Per-request JSON is the primary evidence; the report is a compact summary.

Concurrent API clients simulate simultaneous inference demand. They do not implement agent delegation, task orchestration, long-running repair loops or multiple independent models. Server parallelism and queue time are not separately measured; elapsed latency alone does not isolate them. Repeat count is bounded at three; tiny smoke samples are unsuitable for stable percentile claims. Disclose order, sample count and failure count; do not claim statistical significance.

Task correctness is separate from speed. The exact JSON graders test a known one-line defect and three synthetic QA records. Equivalent prose/code formatting can fail this narrow contract. No generated code is executed. Expanded coding tasks need an isolated sandbox and an independently reviewed grader before use.

Peak process/system RAM, GPU memory, CPU/GPU utilization, thermal throttling, power and backend placement are **unmeasured** by the stdlib client. Record independently collected telemetry with tool version, sampling interval and calibration; distinguish wall-meter readings from software estimates. Do not infer utilization, memory pressure or power from token rates. Sustained reliability testing requires a separate approved plan; the bounded smoke protocol does not establish long-run stability.

No creative media performance is implemented. Generative image/video inference, conventional media processing, and rendering must remain separate categories with their own reproducible workloads, model identities and quality measures; never combine them into a single score.

## API sources

Checked 2026-10-20: [Ollama generate API](https://docs.ollama.com/api/generate), [streaming](https://docs.ollama.com/api/streaming), [installed model metadata](https://docs.ollama.com/api/tags), and [API version](https://docs.ollama.com/api/version). API versions can change; preserve the tested server version and review metrics before comparisons.
