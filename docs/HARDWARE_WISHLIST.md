# Hardware acquisition priorities

Seek free or donated systems, evaluation loaners, refurbished units and lawfully retired business hardware. Prefer a complete working system. Accept incomplete systems or components when the ownership, missing parts, compatibility and cost to make them usable are clear. Keep mini PCs and laptops in the comparison pool alongside compact systems, desktops and workstations.

| Research tier | Target configuration | Workload and decision |
|---|---|---|
| 1. Immediate development workstation | Modern multicore CPU, 32 GB RAM target with 64 GB preferred, SSD, expandable chassis, reliable cooling and PSU. Dell Precision, HP Z-series, Lenovo ThinkStation and comparable workstations are examples. | Measure clean/incremental builds, test suites and small CPU models during normal multitasking. Establish a repeatable baseline before adding acceleration. |
| 2. Local AI workstation | 64 GB or more system RAM, NVIDIA GPU around 12–24 GB VRAM, SSD, adequate PCIe connectivity, cooling and power, and a supported inference stack. | Compare CPU and GPU execution for the same model and task, and record when models spill out of VRAM. |
| 3. Advanced local AI server | Higher memory capacity, dedicated model hosting, concurrent inference, multiple agent workloads and possible multi-GPU support. | Advance only when repeatable measurements show workstation capacity or client contention limits a defined workload. Compare remote-host overhead and workflow completion first. |

These are research targets. Actual fit depends on model, quantization, context, workload, driver/runtime support and measured headroom.

Before transfer, check model and chassis revision, RAM type and slots, drive bays and SSD interfaces, GPU length/height/slot width, usable PCIe lanes, firmware, PSU capacity and connectors, airflow and vendor restrictions. Confirm driver support and acceleration in the intended OS/runtime. Record missing parts and itemized upgrade, freight and return costs. Compare idle and active wall power, energy per completed task and thermals where instrumentation permits. Record unavailable values as such and document cooling, noise and duty-cycle constraints.

Use the [transfer and disclosure terms](../PARTNERSHIPS.md) and [evaluation criteria](../HARDWARE_EVALUATION.md).
