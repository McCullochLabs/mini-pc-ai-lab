# Roadmap

## Available

- Original synthetic prompts, exact-JSON graders and fixture results.
- Bounded Ollama client, privacy-conscious inventory, environment checks, result validation and Markdown reports.
- 19 passing automated tests with a local mock HTTP service.
- Sanitized technical portfolio and host-readiness observations; no inference performance results yet.
- Independent editorial policy, hardware wishlist and evaluation proposal.

## First measured inference

Restore sufficient memory headroom and a quiet available local runtime. Use the already installed model after checking its digest and server acceptance, one request, a small output cap and a short timeout. Record correctness separately from speed. Publish reviewed raw metrics and environment details, with failures and cache-state limitations. See [methodology](BENCHMARK_METHODOLOGY.md).

## Controlled comparisons

Separate cold/warm runs and collect at least three measured repetitions. Evaluate one/two/four-client demand only when resources permit. Compare another system when access is real. Add independent memory/thermal/power instrumentation and disclose sampling limitations.

## Deferred

End-to-end OpenCode-inspired tasks, Android builds, autonomous agent repair loops, extended reliability, generative image/video tasks and eGPU studies need original fixtures, suitable hardware and an explicit resource budget. Conventional rendering/media processing will remain separate from AI inference. No dashboard, website, paid hosting or CRM is planned.
