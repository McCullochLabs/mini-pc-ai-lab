# Result format and interpretation

`python scripts/lab.py validate FILE` is the executable validator. New runs use schema 2 / toolkit 1.0.0; legacy schema1 fixtures remain readable and cannot be treated as measured runs by relabeling mode alone. JSON rejects non-finite values. Checks validate consistency, not authenticity; an operator can forge data.

## v2 record

Required provenance includes `run_id` UUID, tool version, explicit UTC start/end timestamps, mode, completion status, normalized config, hardware/specification fingerprint, model/digest/size/quantization metadata, backend version/residency, workload digest, capacity estimate, warm-up/measured batches, resource observations, warnings and hardware disclosure.

States distinguish running, completed, completed-with-errors, budget-exhausted, interrupted and failed records (the JSON uses underscore-separated names). Incomplete states retain only completed batches and never claim the full requested trial succeeded. A successful request can have failed quality. Model output text/source, private endpoints and raw error strings are not retained.

Each batch identifies phase, workload, client count and repeat, with positive batch duration, individual request IDs/outcomes and aggregate throughput. Request timings include inclusive wall time, nullable output-fragment TTFT, client dispatch delay, backend counts/durations and derived rates. Errors retain a safe class rather than raw private diagnostics. Grader identity must match fixture/legacy exact-JSON/static-AST provenance.

Warm-ups are excluded from measured tables. Resources are sampled local-system observations with interval, timestamps, sample count, sources and summary. System RAM/CPU cannot be attributed to the model; optional NVIDIA framebuffer/utilization is vendor-specific. Sampled peaks can miss spikes. Unknown CPU/GPU/power/thermal values stay null/unavailable, never zero.

Measurement classes are explicit in structure and report: client/OS **actual observation**, Ollama **backend-reported**, capacity guard **estimate**, null/unsupported **unavailable**, fixture mode **synthetic**. The report summarizes resources; the JSON retains samples.

## Configuration and comparison

The original eight settings remain accepted: model, context length, output cap, seed, client counts, repeats, request timeout and workload IDs. v2 adds optional threads, warmups and run budget. The CLI exposes model/thread/warmup/repeat/budget overrides. Bounds and heavier-run policy are enforced before requests; see [usage](README.md).

Compare only completed measured v2 records with identical model/digest/quantization, configuration, prompt digest, runtime/tool versions and placement category. Synthetic or incompatible records are rejected. Different hardware/OS/conditions still require interpretation; raw speed does not imply better task quality. Raw records and reproduction settings should accompany any public comparison.

## Review before publication

Inspect custom model/device names, all metadata and sponsorship disclosure before sharing. Unknown extra fields are not a privacy guarantee. Validation cannot establish that source hardware exists, model identity is genuine, clocks/sensors are accurate or results are independently reproduced. Use the public file manifest and publication checklist; no command uploads automatically.
