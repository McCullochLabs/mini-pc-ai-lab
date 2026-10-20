# Hardware wishlist and acquisition strategy

Planning date: 2026-10-20. These are desired evaluation configurations, not validated performance claims, available inventory or purchase recommendations. No prices or free-equipment entitlements are asserted. See [partnership information](../PARTNERSHIPS.md).

| Category | Preferred evaluation configuration | Realistic research question | Main limitation / acquisition route |
|---|---|---|---|
| Existing Windows baseline | Inspected i5-8250U / approximately 16 GB / UHD 620 host; runtime and memory readiness needed | What can the current computer do with a deliberately small model? | [Hardware/readiness observations](../benchmarks/results/readiness-2026-10-20.md) available; inference pending; no acquisition cost |
| AMD Ryzen mini PC | 32 GB minimum preferred, 64 GB desirable; dual-channel memory where supported; 1 TB SSD desirable | Small coding models, CPU/iGPU comparison, serving one model under concurrent requests | Runtime/driver support and shared memory must be checked per configuration; seek previous-generation evaluation sample |
| Ryzen AI / high-memory compact system | 64 GB+ where feasible; exact shared-memory allocation and bandwidth recorded | Does usable memory improve model/context capacity and request reliability? | NPU TOPS does not establish Ollama acceleration; seek loaner rather than costly purchase |
| Intel NUC-style PC | 32–64 GB supported RAM, SSD; complete system or fully costed barebones | CPU baseline, compact server usability, supported GPU paths | Verify exact acceleration support; ask ASUS/SNUC/Shuttle about demo or previous-generation unit |
| Refurbished business desktop | 32–64 GB upgradeable RAM, SSD, documented power supply and expansion | CPU inference and memory upgrades versus total system cost | Tiny/SFF chassis may block GPU installation; ask refurbisher about open-box/retired hardware |
| NVIDIA GPU workstation | 64 GB host RAM desired; 12–24 GB VRAM preferred for a separate GPU track; SSD | GPU coding inference and optional supported creative AI workloads | Actual model/context fit depends on weights, KV cache, overhead and offload; PSU/cooling costs; donated retired tower or loaner |
| Expandable barebones | Document supported CPU/RAM, case volume, power supply and required components | Incremental upgrade and maintenance costs | Free barebones can still need costly CPU/RAM/SSD/OS; request matched parts or complete loaner |
| eGPU-capable PC | Verified OCuLink/Thunderbolt/USB4 PCIe support, compatible dock, GPU and PSU | How host link and offload affect latency/throughput | Port label alone does not establish compatibility; record full dock/cable/GPU cost; supplier demonstration loaner |
| Used enterprise workstation | Upgradeable RAM, compatible GPU power/connectors, supported OS | Larger memory/VRAM capacity from reused hardware | Idle power, noise, age and driver support may offset acquisition savings; corporate donor/refurbisher |

## Workload selection

Start with one small quantized coding model and short fixed contexts. Larger quantized models require measured memory headroom; avoid fixed promises that a parameter count will fit. Log swap use, failures and model residency. Two/four clients to one model do not demonstrate independent multi-model or autonomous-agent capacity. Distinguish successful requests from correct coding-task completion.

Generative image/video workloads need their own compatible implementation, model, license and hardware budget. Conventional media encoding/rendering remains a separately labeled workload. Do not request an expensive GPU on the strength of an unimplemented creative benchmark.

## Acquisition order

1. Establish a safe baseline using verified current hardware and fixture tests. Seek approval before model downloads or resource-intensive runs.
2. Seek one previous-generation complete mini PC through an appropriate evaluation contact. Preserve independent conclusions and treat unfavorable results as useful evidence. Correspondence and contact history stay private.
3. Approach SNUC, ASRock and BOSGAME with the independent test plan. General sales contacts are routing requests, not existing sample programs.
4. Seek open-box/refurbished systems and retired corporate workstations. Ask for lawful transfer and data sanitization; avoid acquiring private user data.
5. Community donations and open-source/developer hardware support are possible routes. No eligible award or guaranteed mini-PC hardware grant was verified; program terms and applicant eligibility must be checked independently. Do not advertise eligibility or expected donations.

Compare total configured cost including RAM, SSD, GPU/dock, power supply, OS if required, shipping, import charges, return costs and measured energy where available. Prefer upgradeability, supported runtime paths, memory capacity/bandwidth and practical maintenance over processor novelty. Nothing is purchased or accepted automatically.
