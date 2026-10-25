# Project-derived benchmark lessons

Reviewed 2026-10-25. This is a sanitized translation of engineering patterns into original lab workloads. It does not copy private source, prompts, product data, commercial assets, device evidence, repository paths or internal architecture. Repository access demonstrates that a pattern exists; it does not prove that a local model created it or that another machine can reproduce its results.

## What the other projects add to the lab

| Observed project class | General engineering lesson | Lab response | Current status |
|---|---|---|---|
| Public Python publishing application | Exact runtime compatibility, preflight checks, recoverable work and prompt release of database/file handles matter alongside model speed. | Added a resource-lifecycle review fixture; retain document generation, preflight and recovery as future isolated end-to-end workloads. | Static review implemented; end-to-end workload planned |
| Private offline Android trial application | A useful result includes unit checks, device/emulator behavior, persistent-data migration, responsive/accessibility checks and artifact identity—not merely a successful compile. | Add Android build/device stages and checksum verification to the proposed disposable Android fixture. | Planned |
| Private Android creator application | Drafts must survive process death; imports must not overwrite stored work; older/future data needs explicit handling; test and review gates must cover the same frozen change set. | Added synthetic persistence, import-collision and release-gate review fixtures. Add recovery, migration and frozen-snapshot receipts to the advanced repair loop. | Static reviews implemented; behavioral loop planned |

## New bounded review profile

Run eight original synthetic cases: four defective snippets and four matched clean controls with:

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

## Follow-up evidence and grading correction (2026-10-25)

The earlier four prompts supplied the expected line and repair. They could establish response-format compliance, not independent defect detection. Historical results from that protocol must retain that limitation and must not be pooled with the revised protocol.

The revised workflow-review-v2 prompts provide numbered source, policy and API contracts without the expected response. Four matched clean controls require null/null to measure false positives. Release expressions are checked by a finite Boolean interpreter across all four input pairs. Other repairs accept a finite set of equivalent AST forms; valid alternatives outside that set can still fail. Generated code is never executed. The broader coding profile contains 13 cases across nine categories; its older five constrained tasks remain structural instruction-following checks. Fixture-mode CLI success demonstrates pipeline operation, not model quality.

Local source inspection adds these sanitized references; exact source paths and SHA-256 digests are retained only in the ignored private audit record:

| ID | Evidence inspected | What may be concluded | Limit |
|---|---|---|---|
| L01 | Creator application draft storage and UI save scheduling | Durable-write and lifecycle recovery are relevant test questions | UI saves are delayed; this is not proof every edit survives arbitrary process death |
| L02 | Stored-record hardening test source | Collision handling and unsupported-record preservation deserve isolated cases | Tests were read, not executed in this audit |
| L03 | Historical review-packet document | Review conclusions must identify the same source/artifact snapshot | A packet is not a verdict; historical blocked/recovered states do not certify today's tree |
| L04 | Separate local development prototype: documentation, intake source and tests | Bounded requests, overload behavior and receipt integrity motivate future lab tests | Source presence does not demonstrate deployment, security certification or measured agent orchestration |

No private project names, source code, internal service details or artifacts are published here. Other projects remained read-only. The earlier public publishing/offline-app derivations are retained as historical rationale, not promoted to newly verified source findings in this audit.
