# Project-derived benchmark lessons

Reviewed 2026-10-22. This is a sanitized translation of engineering patterns into original lab workloads. It does not copy private source, prompts, product data, commercial assets, device evidence, repository paths or internal architecture. Repository access demonstrates that a pattern exists; it does not prove that a local model created it or that another machine can reproduce its results.

## What the other projects add to the lab

| Observed project class | General engineering lesson | Lab response | Current status |
|---|---|---|---|
| Public Python publishing application | Exact runtime compatibility, preflight checks, recoverable work and prompt release of database/file handles matter alongside model speed. | Added a resource-lifecycle review fixture; retain document generation, preflight and recovery as future isolated end-to-end workloads. | Static review implemented; end-to-end workload planned |
| Private offline Android trial application | A useful result includes unit checks, device/emulator behavior, persistent-data migration, responsive/accessibility checks and artifact identity—not merely a successful compile. | Add Android build/device stages and checksum verification to the proposed disposable Android fixture. | Planned |
| Private Android creator application | Drafts must survive process death; imports must not overwrite stored work; older/future data needs explicit handling; test and review gates must cover the same frozen change set. | Added synthetic persistence, import-collision and release-gate review fixtures. Add recovery, migration and frozen-snapshot receipts to the advanced repair loop. | Static reviews implemented; behavioral loop planned |

## New bounded review profile

Run the four original, project-informed but fully synthetic review tasks with:

```powershell
python scripts/lab.py run --fixture --config benchmarks/configurations/workflow-reliability.json --output .local/workflow-reliability.json
```

The profile checks whether a model follows exact contracts for:

- requiring both test and build gates;
- checkpointing accepted draft edits instead of relying on graceful shutdown;
- minting a fresh identity rather than replacing a colliding saved record; and
- closing a database connection before a completed operation returns.

These are static, narrow recognition tests. They do not execute generated code, simulate Android lifecycle events, prove crash recovery, validate a database migration or establish autonomous agent behavior. An exact-contract failure can still be a semantically useful answer, so preserve the raw pass/fail result without inflating it into a general capability claim.

## Priorities for higher-fidelity measurements

1. **Disposable Android build fixture:** separately time model inference, patch application, unit tests, debug build and emulator/device checks.
2. **Crash-recovery fixture:** kill and relaunch an isolated application after accepted edits; compare recovered state and artifact hashes.
3. **Import/migration fixture:** seed legacy, future, duplicate-key and colliding-identity records; verify that unsupported data is preserved and saved data is not replaced.
4. **Publishing pipeline fixture:** generate a small original document package, run preflight, intentionally interrupt one stage, resume safely and verify outputs by checksum.
5. **Frozen review packet:** bind implementation, tests and independent review to one content hash so a pass cannot silently describe a different snapshot.

Each advanced fixture must remain disposable, license-clean and independent of the source projects. Report model quality, build/tool time, recovery correctness, resource use and review outcome separately.
