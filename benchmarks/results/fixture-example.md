# Mini PC AI Lab result

**FIXTURE — SYNTHETIC SOFTWARE TEST; NOT HARDWARE PERFORMANCE.**

| Workload | Clients | Repeat | Success / requests | Quality passes | Batch seconds | Aggregate output tokens/s |
|---|---:|---:|---:|---:|---:|---:|
| defect_review | 1 | 1 | 1/1 | 1 | 2.0000 | 5.00 |
| structured_qa | 1 | 1 | 1/1 | 1 | 2.0000 | 5.00 |
| defect_review | 2 | 1 | 2/2 | 2 | 2.0000 | 10.00 |
| structured_qa | 2 | 1 | 2/2 | 2 | 2.0000 | 10.00 |
| defect_review | 4 | 1 | 4/4 | 4 | 2.0000 | 20.00 |
| structured_qa | 4 | 1 | 4/4 | 4 | 2.0000 | 20.00 |

Per-request TTFT, server timing, throughput and errors are retained in the JSON. Client concurrency does not establish server parallelism or autonomous agent capability.

Unmeasured: peak_ram, gpu_memory, cpu_utilization, gpu_utilization, thermals, power, server_queue_time, agent_coordination
