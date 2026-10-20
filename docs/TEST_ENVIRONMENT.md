# Test environment and baseline readiness

Inspection date: 2026-10-20. Windows, Python 3.13.15 and Git 2.55.0.windows.5 are available. A later Phase 4 single-request trial is now recorded separately from the initial readiness checks.

Phase 1 CIM queries were denied by the restricted execution environment. Phase 2 approved read-only host queries succeeded: HP Pavilion Laptop 15-cs0xxx family, Intel Core i5-8250U (4 cores/8 logical processors), 17,043,787,776 bytes of physical memory (15.87 GiB), Intel UHD Graphics 620, and Windows 11 Home version 10.0.26300/build 26300. No serial, hostname, username or network address was retained publicly. Advertised AdapterRAM was deliberately excluded from usable GPU-memory claims. Storage, cooling, usable GPU memory and power remain unverified.

Initially, the installed Ollama client was available but its default local service did not respond, and only 0.85–0.91 GiB RAM was free. That dated [readiness snapshot](../benchmarks/results/readiness-2026-10-20.md) remains historical. Later, approximately 6.3 GiB became available and a temporary owned local Ollama 0.40.6 backend served one existing `qwen2.5:3b` Q4_K_M request with two CPU threads. The strict task grade failed. Its [actual metrics and raw record](../benchmarks/results/baseline-2026-10-20.md) preserve that outcome; the temporary backend was stopped afterward. No model/software was installed or downloaded and no global setting changed.

## Actual scope and next trials

The [first-trial configuration](../benchmarks/configurations/first-baseline.json) uses one review task, concurrency one, context 1,024, output cap 32 and a 20-second request timeout. The measured run also specified two threads, zero warm-ups and a 25-second dispatch budget. OS-wide RAM/CPU were sampled; model-process memory, power, thermals and GPU utilization were not measured. Backend-reported CPU residency is not proof of broader GPU compatibility. Follow the [methodology](../BENCHMARK_METHODOLOGY.md) and [operating guide](../benchmarks/README.md) for future runs. Linux/AMD/NVIDIA support currently has mocked validation only.

For later comparisons use at least three measured trials after explicitly identified warmups. Separate cold-load runs from resident-model runs. Record OS build, runtime version, backend, model digest and quantization, context/output caps, power mode, AC state, background activity, ambient temperature where available, and instrument sampling interval. Store hostname-free inventory only after reviewing it.
