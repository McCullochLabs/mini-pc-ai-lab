# Hardware evaluation framework

Evaluate a whole system against an identified workload, not an advertised processor rank. Record verified RAM capacity and upgrade path, usable memory under load, storage, cooling, OS/backend support, warranty, acquisition terms, and total system cost including RAM, storage, GPU, enclosure, power supply, and shipping when relevant.

| Class | Research question | Main limit to measure |
|---|---|---|
| Existing integrated graphics computer | Can a small quantized coding model help with bounded tasks? | Available RAM and CPU fallback latency |
| Expandable Ryzen or Intel mini PC | Does more RAM improve context and queue reliability? | Backend compatibility, bandwidth, sustained cooling |
| Ryzen AI system | Is the GPU/backend useful for this exact model? | Shared memory and software support; NPU TOPS is not Ollama throughput |
| Refurbished business desktop | Is upgradeable memory a better value? | Age, noise, power, GPU clearance and supply |
| GPU workstation | Can dedicated VRAM improve coding inference or creative AI? | Usable VRAM, compatible runtime, total power and cost |
| Barebones or eGPU system | Does expansion offer a viable upgrade path? | Complete-system cost, interface bottleneck, firmware and driver compatibility |

Do not infer usable GPU acceleration from its presence. Confirm the serving backend and offload allocation during the trial. Memory fit is not proof of acceptable speed. A model file size is not its total runtime memory requirement. Record quality separately from speed and report each workload separately.

Use the [methodology](BENCHMARK_METHODOLOGY.md), [wishlist](docs/HARDWARE_WISHLIST.md), and [test environment record](docs/TEST_ENVIRONMENT.md).
