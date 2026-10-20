# Evaluation title

Status: actual measurement / backend-reported / estimate / unavailable / synthetic. Never mix fixture numbers with measured hardware comparisons.

- Run ID, UTC start/end, toolkit/schema version and completion status:
- Hardware/specification fingerprint, OS, CPU/RAM/GPU, inventory sources:
- Backend/version, model digest/quantization, backend-reported residency:
- Exact config, prompt digest, thread/context/output limits, repeats and warm-ups:
- Hardware ownership, donation/loan/discount/financial disclosure, return obligations:
- Conditions: power mode, AC state, ambient temperature, background activity, cache state:

## Request and task outcomes

Record inclusive client latency, output-fragment TTFT proxy, backend load/evaluation durations, token counts/rates, aggregate throughput, all errors and deterministic quality grades. Coding static-contract success is not dynamic correctness. Distinguish actual concurrency from autonomous agents or server parallelism.

## Resources

Record OS-wide sampled RAM/CPU, optional vendor-specific GPU metrics, sources, interval, sample count, sampled peaks and unavailable fields. Do not attribute whole-system memory/CPU to the model. Power/thermals and process peak RAM remain unavailable without instruments.

## Interpretation and limits

Retain partial/interrupted/error status. Explain sample size, warm/cold conditions, grading limits and missing telemetry. Do not infer causality, general coding skill or a universal score from raw speed. Generated answers are not retained, so the recorded quality grade cannot be independently recomputed from the result alone; rerun the original task/grader for reproduction.

## Reproduction and publication

Attach reviewed machine-readable JSON and generated Markdown, exact configuration and toolkit revision. Use [usage instructions](benchmarks/README.md) and the [methodology](BENCHMARK_METHODOLOGY.md). Review private metadata and disclosure under the [editorial policy](EDITORIAL_POLICY.md) before manual publication. Compare only compatible completed measured v2 runs.
