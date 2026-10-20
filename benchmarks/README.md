# Benchmark toolkit

Requires Python 3.10+; no third-party package, dashboard, installer or model downloader. Run from the repository root:

```powershell
python -m unittest discover -s tests -v
python scripts/lab.py check
python scripts/lab.py inventory --output .local/inventory.json
python scripts/lab.py run --fixture --output benchmarks/results/fixture-example.json
python scripts/lab.py validate benchmarks/results/fixture-example.json
python scripts/lab.py report benchmarks/results/fixture-example.json --output benchmarks/results/fixture-example.md
```

Fixture runs do not contact Ollama. Their numbers are invented software fixtures, never hardware evidence. Inventory does not run inference and intentionally excludes hostnames, serials, UUIDs, usernames, addresses, paths and process lists. Windows CIM selects only processor name/core counts, system manufacturer/model/RAM, graphics name/advertised AdapterRAM, and OS version/build. AdapterRAM can be inaccurate, especially on integrated graphics, and is not usable GPU memory. Review inventory before public disclosure. Failed collection retains no raw errors.

`check --probe-server` explicitly performs a read-only local API version query. Other checks only inspect the Python version and whether the Ollama executable is discoverable; no service is started.

For a future authorized smoke run, edit `benchmarks/configurations/smoke.json` to an exact installed model name, close other heavy applications, and explicitly opt in:

```powershell
python scripts/lab.py run --config benchmarks/configurations/smoke.json --allow-inference --output .local/smoke.json
```

Do not run this command during initial setup without owner authorization. The flag is a technical guard, not a substitute for authorization. No real inference was run to prepare this foundation. The concurrency configuration supports 1/2/4 simultaneous clients; it is a separate, heavier proposal requiring approval. It makes 14 requests with two workloads and one repeat. Maximum accepted settings are 3 repeats, 512 output tokens, 8192 context tokens, 120 seconds per request, and four clients. These are safety bounds, not guaranteed low resource use. A request can occupy a socket read for up to the socket timeout beyond the wall-clock check; server work may continue after client disconnect. There is no background stress runner.

Only loopback HTTP endpoints are accepted; credentials, nonlocal addresses and environment proxies are rejected/bypassed. No endpoint is stored in results. No generated text, thinking output, raw server errors or private prompts are saved. The bundled prompts are synthetic and public. Redirects are disabled. Model metadata comes from `/api/tags`, including digest and quantization where available; this does not prove CPU/GPU placement. All results need an accompanying reviewed environment record.

Quality grading accepts exact JSON objects for a deliberately small defect-review and structured QA task. It never executes model-generated code. This is a narrow regression workload, not a general coding ability score; feature implementation, test generation, repair loops, Android builds, document rendering and image/video generation remain proposed extensions.

Results record individual errors, batch duration, per-request output-fragment TTFT and server metrics. All-failed batches remain valid observations with zero successful throughput; inspect reliability before drawing speed conclusions. CLI validation returns nonzero on invalid inputs. Report generation validates first. See [methodology](../BENCHMARK_METHODOLOGY.md) and [results template](../RESULTS_TEMPLATE.md).

