# Test environment and baseline readiness

Inspection date: 2026-10-20. Windows, Python 3.13.15 and Git 2.55.0.windows.5 are available. These are environment checks, not AI benchmark results.

Phase 1 CIM queries were denied by the restricted execution environment. Phase 2 approved read-only host queries succeeded: HP Pavilion Laptop 15-cs0xxx family, Intel Core i5-8250U (4 cores/8 logical processors), 17,043,787,776 bytes of physical memory (15.87 GiB), Intel UHD Graphics 620, and Windows 11 Home version 10.0.26300/build 26300. No serial, hostname, username or network address was retained publicly. Advertised AdapterRAM was deliberately excluded from usable GPU-memory claims. Storage, cooling, usable GPU memory and power remain unverified.

No model or software was downloaded, no global settings changed, and no inference or sustained load was run. Ollama client 0.40.6 is installed; the default local service did not respond to the Phase 2 check. Existing `qwen2.5:3b` and `llama3.2:3b` model manifests reference files present at declared sizes, but content hashes, runtime loading and backend remain unverified. Three short readings found 0.85–0.91 GiB free physical memory during existing work. This is insufficient headroom for a prudent model-loading trial. See the [actual observation](../benchmarks/results/readiness-2026-10-20.md).

## Proposed first baseline — not executed

The [first-trial configuration](../benchmarks/configurations/first-baseline.json) proposes one installed model, one prompt, concurrency one, a 32-token output cap and a 20-second request timeout after memory/service readiness is restored. Follow the [methodology](../BENCHMARK_METHODOLOGY.md). Stop on unexpected memory pressure or service errors and avoid overlapping other development tasks. Repeat only after reviewing the first trial; a smoke observation is not a statistical comparison.

For later comparisons use at least three measured trials after explicitly identified warmups. Separate cold-load runs from resident-model runs. Record OS build, runtime version, backend, model digest and quantization, context/output caps, power mode, AC state, background activity, ambient temperature where available, and instrument sampling interval. Store hostname-free inventory only after reviewing it.
