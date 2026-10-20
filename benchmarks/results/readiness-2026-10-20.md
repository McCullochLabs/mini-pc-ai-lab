# First host readiness observation — 2026-10-20

**Actual hardware and readiness readings; no AI inference benchmark was run.**

| Item | Observed value |
|---|---|
| System family | HP Pavilion Laptop 15-cs0xxx |
| Processor | Intel Core i5-8250U, 4 cores / 8 logical processors |
| Physical memory reported by Windows | 17,043,787,776 bytes, 15.87 GiB (approximately 16 GB class) |
| Graphics | Intel UHD Graphics 620; usable GPU memory and acceleration unverified |
| OS | Windows 11 Home, version 10.0.26300 / build 26300 |
| Ollama installed client | 0.40.6 |
| Default local Ollama service | Not reachable during check; server version unavailable |
| Existing model files | `qwen2.5:3b` and `llama3.2:3b` manifests; referenced files present and declared sizes matched |
| Inference requests submitted | **0** |

Model-file presence is not content-hash verification or proof of runtime loading. A separate 1,117,320,736-byte small Qwen GGUF file was also found in existing development tooling; it was not imported, loaded or modified.

Three short Windows CIM/performance-provider readings during existing background work:

| UTC observation | Free physical memory, GiB | Physical-used proxy | CPU counter |
|---|---:|---:|---:|
| 13:11:09.656 | 0.907 | 94.29% | 33% |
| 13:11:11.105 | 0.847 | 94.66% | 44% |
| 13:11:12.529 | 0.894 | 94.37% | 17% |

These are readiness snapshots, not idle averages or inference telemetry. Physical-used proxy is `(total visible - free physical) / total visible`; it includes other applications and system memory and does not identify peak or process usage. An earlier discovery snapshot had approximately 0.83 GiB free. Sensor limitations and full integer readings are retained in the [sanitized JSON](readiness-2026-10-20.json).

**Decision:** defer model loading, inference and concurrency. Loading an approximately 2 GB-class model into a host with less than 1 GiB currently free would risk disrupting existing work. The unavailable service independently prevents this toolkit's inference trial. No throughput, TTFT, model quality, thermal, power or GPU result is claimed.

Follow the [methodology](../../BENCHMARK_METHODOLOGY.md) and [first-trial configuration](../configurations/first-baseline.json) after the host is quiet, memory headroom is sufficient and the installed service is available. No download is needed if existing models are accepted by the runtime. A pending inference result is the honest launch state.

Inference throughput, TTFT, quality, peak inference memory and concurrency: **Pending — not yet measured**.
