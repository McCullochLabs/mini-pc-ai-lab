# Operating the benchmark toolkit

Requires Python **3.10+**. Safe fixtures use only its standard library. Real inference needs an already installed local Ollama runtime/model and sufficient memory. No software, model or permanent service is installed automatically.

## Windows PowerShell quick start

Run from the checkout:

```powershell
python scripts/lab.py --version
python scripts/lab.py check --probe-server
python scripts/lab.py models
python scripts/lab.py inventory --output .local/inventory.json
python scripts/lab.py run --fixture --output .local/fixture.json
python scripts/lab.py validate .local/fixture.json
python scripts/lab.py report .local/fixture.json --output .local/fixture.md
```

`check` without `--probe-server` makes no service request. `models` lists metadata, never pulls a model. Installed and reachable are separate states. Windows memory/CPU collection uses non-admin interfaces and bounded allowlisted CIM; a restricted execution environment can deny fields without implying ordinary use requires administrator rights.

## Linux shell

Use the same commands with `python3`:

```sh
python3 scripts/lab.py check --probe-server
python3 scripts/lab.py models
python3 scripts/lab.py run --fixture --output .local/fixture.json
python3 scripts/lab.py report .local/fixture.json --output .local/fixture.md
```

Linux uses `/proc` for CPU/RAM and available `lspci` or limited DRM fields for GPU identity. Optional NVIDIA counters require an existing `nvidia-smi`. Missing fields remain unavailable. Other platforms can use fixtures; real inference fails closed without reliable RAM data.

## Safe first real trial

Let other work finish; do not kill applications to make a benchmark fit. Start the existing local Ollama application normally and confirm a suitable installed model is listed. Substitute its exact name below, or use `--model auto` for the smallest installed candidate passing the resource guard:

```powershell
python scripts/lab.py run --config benchmarks/configurations/first-baseline.json --model qwen2.5:3b --allow-inference --output .local/first.json
python scripts/lab.py validate .local/first.json
python scripts/lab.py report .local/first.json --output .local/first.md
```

This requests one narrow review task, one client, context 1,024, output cap 32 and a 20-second request timeout. CPU threads default to 2. Treat it as a smoke observation, not a statistical comparison. Quality failure remains separate from transport success and token speed.

`--threads`, `--warmups`, `--repeats` and `--run-budget` override settings without editing several files. More clients, repetitions, warm-ups and larger budgets require an additional deliberate `--allow-heavy` opt-in. It does not bypass RAM checks. Use it only with an authorized resource budget. Admission is conservative, not an OOM guarantee. Severe/unknown memory availability stops further batch dispatch; unrelated processes are untouched.

The run budget stops new batches; in-flight calls drain and may exceed it by transport/socket delay. Server work may continue after disconnect. No automatic retry/stress loop or shared-model unload is performed.

## Coding and concurrent traffic

```powershell
python scripts/lab.py run --fixture --config benchmarks/configurations/coding.json --output .local/coding.json
python scripts/lab.py run --fixture --config benchmarks/configurations/concurrency.json --output .local/concurrency.json
```

The five coding categories are feature implementation, bug correction, test generation, review and refactoring. Graders inspect bounded JSON/AST contracts; **generated code is never executed**. Passing verifies specified structure, not general dynamic correctness; equivalent correct solutions may fail. Trusted fixture answers are synthetic, never measured model quality.

Real suites require `--allow-inference`, a listed model and, where settings require it, `--allow-heavy`. One/two/four clients share one model. They do not establish independent agents, several model instances, full OpenCode orchestration or server parallelism. Client dispatch delay is not server queue time.

## Reports, comparison and review

```powershell
python scripts/lab.py compare .local/system-a.json .local/system-b.json --output .local/comparison.json
```

Comparison requires completed measured v2 runs and matching configuration, model/quantization, backend/tool version, prompt digest and placement category. Hardware/conditions still need human interpretation. No universal score is created.

Results include run IDs, completion/error status, provenance, resource sources and disclosure. Checkpoints retain completed batches on interruption; a partial run is not successful. Reports validate first. Sponsorship defaults to unknown/not supplied; `--sponsorship` supplies an operator-reviewed truthful disclosure.

Review JSON/report/device/model names and disclosure before publication. Nothing uploads automatically. Routine records exclude generated text/code, private endpoints, raw server errors, usernames, serials and process lists. Custom metadata may still need sanitization. See [format/interpretation](RESULT_FORMAT.md), [methodology](../BENCHMARK_METHODOLOGY.md) and [release gates](../docs/V1_RELEASE.md).

## Troubleshooting

| Condition | Action |
|---|---|
| CLI absent | Use fixtures; arrange installation separately |
| Installed but unreachable | Open the existing local application/service; check port/permissions; do not download models as a connectivity fix |
| Model absent | Choose an exact listed name or stop; no pull occurs |
| RAM unknown / no model fits | Wait for memory headroom or use another system; do not bypass the guard or kill unrelated work |
| Heavy settings refused | Reduce settings or explicitly authorize the larger budget |
| Truncated/invalid JSON or failed static grade | Retain failure; inspect contract/output cap; transport success is not task success |
| Missing sensor/GPU field | Keep unavailable; support differs by platform/driver |
| Interrupted/budget exhausted | Retain status and completed batches; use a new run for a repeat |
| Comparison refused | Resolve incompatibility rather than treating runs as equivalent |

Safe tests: `python -m unittest discover -s tests -v`. Local mock sockets must be permitted. Mock platform tests do not certify real Linux/AMD/NVIDIA hardware.
