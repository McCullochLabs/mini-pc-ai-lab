"""Mini PC AI Lab: Python 3.10+ standard-library-only, opt-in local benchmark."""
import argparse
import concurrent.futures
import datetime
import json
import math
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
METRICS = ('total_duration', 'load_duration', 'prompt_eval_count', 'prompt_eval_duration', 'eval_count', 'eval_duration')
UNMEASURED = ['peak_ram', 'gpu_memory', 'cpu_utilization', 'gpu_utilization', 'thermals', 'power', 'server_queue_time', 'agent_coordination']


def read_json(path):
    def reject(value):
        raise ValueError('non-finite JSON number')
    return json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=reject)


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an integer in {low}..{high}')
    return value


def config_check(config):
    keys = {'model', 'context_length', 'num_predict', 'seed', 'concurrency', 'repeats', 'timeout_seconds', 'workloads'}
    if not isinstance(config, dict) or set(config) != keys:
        raise ValueError('configuration must contain exactly: ' + ', '.join(sorted(keys)))
    if not isinstance(config['model'], str) or not config['model'] or len(config['model']) > 200 or any(c.isspace() for c in config['model']):
        raise ValueError('invalid model name')
    for name, low, high in [('context_length', 256, 8192), ('num_predict', 1, 512), ('seed', 0, 2147483647), ('repeats', 1, 3), ('timeout_seconds', 1, 120)]:
        integer(config[name], low, high, name)
    if not isinstance(config['concurrency'], list) or not config['concurrency'] or any(type(c) is not int or c not in (1, 2, 4) for c in config['concurrency']) or len(set(config['concurrency'])) != len(config['concurrency']):
        raise ValueError('concurrency must be unique entries from 1, 2, 4')
    if not isinstance(config['workloads'], list) or not config['workloads'] or any(type(w) is not str or w not in ('defect_review', 'structured_qa') for w in config['workloads']) or len(set(config['workloads'])) != len(config['workloads']):
        raise ValueError('unknown or duplicate workload')
    return config


def endpoint_check(endpoint):
    u = urlsplit(endpoint)
    if u.scheme != 'http' or u.hostname not in ('127.0.0.1', 'localhost', '::1') or u.username or u.password or u.path not in ('', '/') or u.query or u.fragment:
        raise ValueError('endpoint must be an HTTP loopback origin without credentials or path')
    _ = u.port
    return endpoint.rstrip('/')


def opener():
    # Never send local model prompts through environment HTTP proxies.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise ValueError('redirect refused')
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())


def get_json(endpoint, route, timeout=5):
    with opener().open(endpoint + route, timeout=timeout) as r:
        raw = r.read(1048577)
    if len(raw) > 1048576:
        raise ValueError('metadata response too large')
    return json.loads(raw)


def grade(workload, answer):
    """Exact synthetic JSON contracts; never execute or import model output."""
    expected = {'defect_review': {'defect_line': 2, 'fix': 'x >= 18'}, 'structured_qa': {'invalid_ids': ['B', 'C'], 'valid_count': 1}}[workload]
    try:
        actual = json.loads(answer)
        def exact(a, b):
            if type(a) is not type(b):
                return False
            if isinstance(b, dict):
                return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in b)
            if isinstance(b, list):
                return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
            return a == b
        return {'passed': exact(actual, expected), 'grader': 'exact-json-v1'}
    except (ValueError, TypeError):
        return {'passed': False, 'grader': 'exact-json-v1'}


def generate(endpoint, config, workload, prompt):
    payload = {'model': config['model'], 'prompt': prompt, 'stream': True, 'format': 'json', 'keep_alive': '1m', 'options': {'temperature': 0, 'seed': config['seed'], 'num_ctx': config['context_length'], 'num_predict': config['num_predict']}}
    req = urllib.request.Request(endpoint + '/api/generate', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    started = time.perf_counter()
    first = None
    answer = ''
    final = None
    size = 0
    with opener().open(req, timeout=config['timeout_seconds']) as response:
        while True:
            if time.perf_counter() - started > config['timeout_seconds']:
                raise TimeoutError('request wall-clock limit exceeded')
            line = response.readline(1048577)
            if not line:
                break
            size += len(line)
            if size > 1048576:
                raise ValueError('stream exceeds 1 MiB limit')
            obj = json.loads(line)
            if not isinstance(obj, dict) or 'error' in obj:
                raise ValueError('server returned invalid/error stream')
            piece = obj.get('response', '')
            if not isinstance(piece, str):
                raise ValueError('invalid response fragment')
            if piece and first is None:
                first = time.perf_counter() - started
            answer += piece
            if obj.get('done') is True:
                final = obj
                break
    if final is None:
        raise ValueError('stream ended without done=true')
    metrics = {k: integer(final.get(k), 0, 10**18, k) for k in METRICS}
    cached = integer(final.get('prompt_eval_cached_count', 0), 0, metrics['prompt_eval_count'], 'prompt_eval_cached_count')
    metrics['prompt_eval_cached_count'] = cached
    metrics['generation_tokens_per_second'] = metrics['eval_count'] * 1e9 / metrics['eval_duration'] if metrics['eval_duration'] else None
    metrics['prompt_tokens_per_second'] = (metrics['prompt_eval_count'] - cached) * 1e9 / metrics['prompt_eval_duration'] if metrics['prompt_eval_duration'] else None
    return {'workload': workload, 'status': 'ok', 'wall_seconds': time.perf_counter() - started, 'ttft_seconds': first, 'metrics': metrics, 'quality': grade(workload, answer)}


def inventory():
    data = {'schema_version': 1, 'os': platform.system(), 'os_release': platform.release(), 'architecture': platform.machine(), 'python': platform.python_version(), 'collection': 'allowlisted; no hostname, serial, UUID, username, network or paths'}
    if platform.system() == 'Windows':
        command = "$ErrorActionPreference='Stop'; @{cpu=@(Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors);system=@(Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model,TotalPhysicalMemory);gpu=@(Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM);os=@(Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber)} | ConvertTo-Json -Depth 4 -Compress"
        try:
            raw = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', command], capture_output=True, text=True, timeout=20, check=True)
            data['windows'] = json.loads(raw.stdout)
        except (OSError, subprocess.SubprocessError, ValueError):
            data['windows'] = None
            data['note'] = 'CIM collection unavailable; no raw error retained'
    return data


def run(config, endpoint, fixture=False):
    config_check(config)
    workloads = read_json(ROOT / 'benchmarks/workloads/synthetic.json')
    result = {'schema_version': 1, 'mode': 'fixture' if fixture else 'measured', 'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'config': config, 'model_metadata': None, 'batches': [], 'unmeasured': list(UNMEASURED)}
    if not fixture:
        tags = get_json(endpoint, '/api/tags')
        model = next((m for m in tags['models'] if m.get('name') == config['model']), None)
        if model is None:
            raise ValueError('exact configured model not installed; select a listed name (no automatic pull)')
        result['model_metadata'] = {k: model.get(k) for k in ('name', 'digest', 'size')}
        result['model_metadata']['details'] = {k: model.get('details', {}).get(k) for k in ('format', 'family', 'parameter_size', 'quantization_level')}
        result['ollama_version'] = get_json(endpoint, '/api/version').get('version')
    for concurrency in config['concurrency']:
        for repeat in range(config['repeats']):
            for workload in config['workloads']:
                start = time.perf_counter()
                def request(_):
                    if fixture:
                        return read_json(ROOT / 'benchmarks/fixtures/request.json') | {'workload': workload}
                    try:
                        return generate(endpoint, config, workload, workloads[workload]['prompt'])
                    except Exception as e:
                        return {'workload': workload, 'status': 'error', 'error_type': type(e).__name__}
                with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
                    requests = list(pool.map(request, range(concurrency)))
                elapsed = 2.0 if fixture else time.perf_counter() - start
                count = sum(r.get('metrics', {}).get('eval_count', 0) for r in requests)
                result['batches'].append({'concurrency': concurrency, 'repeat': repeat, 'workload': workload, 'wall_seconds': elapsed, 'aggregate_output_tokens_per_second': count / elapsed, 'requests': requests})
    validate(result)
    return result


def validate(result):
    try:
        return _validate(result)
    except (KeyError, TypeError, AttributeError, OverflowError) as error:
        raise ValueError('malformed result structure') from error


def _validate(result):
    if not isinstance(result, dict) or type(result.get('schema_version')) is not int or result['schema_version'] != 1 or result.get('mode') not in ('fixture', 'measured'):
        raise ValueError('invalid result schema/mode')
    mandatory = {'schema_version', 'mode', 'created_utc', 'config', 'model_metadata', 'batches', 'unmeasured'}
    if not mandatory <= result.keys():
        raise ValueError('missing required result provenance')
    if not isinstance(result['created_utc'], str):
        raise ValueError('invalid creation timestamp')
    stamp = datetime.datetime.fromisoformat(result['created_utc'].replace('Z', '+00:00'))
    if stamp.tzinfo is None or stamp.utcoffset() != datetime.timedelta(0):
        raise ValueError('creation timestamp must explicitly use UTC')
    if type(result['unmeasured']) is not list or len(result['unmeasured']) != len(UNMEASURED) or any(type(v) is not str for v in result['unmeasured']) or set(result['unmeasured']) != set(UNMEASURED):
        raise ValueError('required unmeasured limitations missing')
    config_check(result['config'])
    if result['mode'] == 'fixture':
        if result['model_metadata'] is not None:
            raise ValueError('fixture cannot claim model metadata')
    else:
        metadata = result['model_metadata']
        if not isinstance(metadata, dict) or not {'name', 'digest', 'size', 'details'} <= metadata.keys() or metadata['name'] != result['config']['model']:
            raise ValueError('missing or inconsistent model metadata')
        if not isinstance(metadata['digest'], str) or not metadata['digest'].strip():
            raise ValueError('missing model digest')
        integer(metadata['size'], 1, 10**18, 'model size')
        if not isinstance(metadata['details'], dict):
            raise ValueError('invalid model details')
        for name in ('format', 'family', 'parameter_size', 'quantization_level'):
            value = metadata['details'][name]
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError('invalid model detail')
        if not isinstance(result.get('ollama_version'), str) or not result['ollama_version'].strip():
            raise ValueError('missing Ollama version')
    expected = len(result['config']['concurrency']) * result['config']['repeats'] * len(result['config']['workloads'])
    if not isinstance(result.get('batches'), list) or len(result['batches']) != expected:
        raise ValueError('incomplete batch set')
    seen = set()
    def finite(v, nullable=False):
        if nullable and v is None:
            return
        if type(v) not in (int, float) or not math.isfinite(v) or v < 0:
            raise ValueError('invalid non-negative finite metric')
    for batch in result['batches']:
        if not isinstance(batch, dict):
            raise ValueError('invalid batch object')
        integer(batch['concurrency'], 1, 4, 'batch concurrency')
        if type(batch['workload']) is not str:
            raise ValueError('invalid batch workload')
        key = (batch['concurrency'], batch['repeat'], batch['workload'])
        if key in seen or key[0] not in result['config']['concurrency'] or type(key[1]) is not int or not 0 <= key[1] < result['config']['repeats'] or key[2] not in result['config']['workloads']:
            raise ValueError('invalid/duplicate batch')
        seen.add(key)
        finite(batch['wall_seconds'])
        if batch['wall_seconds'] == 0:
            raise ValueError('zero batch wall time')
        finite(batch['aggregate_output_tokens_per_second'])
        if type(batch['requests']) is not list or len(batch['requests']) != batch['concurrency']:
            raise ValueError('request count differs from concurrency')
        for request in batch['requests']:
            if not isinstance(request, dict):
                raise ValueError('invalid request object')
            if request.get('status') not in ('ok', 'error') or request.get('workload') != key[2]:
                raise ValueError('invalid request')
            if request['status'] == 'ok':
                finite(request['wall_seconds'])
                finite(request['ttft_seconds'], True)
                if request['ttft_seconds'] is not None and request['ttft_seconds'] > request['wall_seconds']:
                    raise ValueError('TTFT exceeds request duration')
                for metric in METRICS:
                    integer(request['metrics'][metric], 0, 10**18, metric)
                for metric in ('generation_tokens_per_second', 'prompt_tokens_per_second'):
                    finite(request['metrics'][metric], True)
                cached = integer(request['metrics'].get('prompt_eval_cached_count', 0), 0, request['metrics']['prompt_eval_count'], 'prompt_eval_cached_count')
                for count, duration, rate in ((request['metrics']['eval_count'], request['metrics']['eval_duration'], 'generation_tokens_per_second'), (request['metrics']['prompt_eval_count'] - cached, request['metrics']['prompt_eval_duration'], 'prompt_tokens_per_second')):
                    expected_rate = count * 1e9 / duration if duration else None
                    actual_rate = request['metrics'][rate]
                    if (expected_rate is None) != (actual_rate is None) or expected_rate is not None and not math.isclose(expected_rate, actual_rate, rel_tol=1e-9):
                        raise ValueError('inconsistent token rate')
                if type(request['quality'].get('passed')) is not bool:
                    raise ValueError('invalid grade')
                expected_grader = 'fixture-synthetic-not-model-output' if result['mode'] == 'fixture' else 'exact-json-v1'
                if request['quality'].get('grader') != expected_grader:
                    raise ValueError('grader provenance does not match result mode')
            elif not isinstance(request.get('error_type'), str):
                raise ValueError('missing error classification')
        expected_aggregate = sum(r.get('metrics', {}).get('eval_count', 0) for r in batch['requests'] if r['status'] == 'ok') / batch['wall_seconds']
        if not math.isclose(batch['aggregate_output_tokens_per_second'], expected_aggregate, rel_tol=1e-9):
            raise ValueError('inconsistent batch throughput')
    return True


def report(result):
    validate(result)
    lines = ['# Mini PC AI Lab result', '', '**FIXTURE — SYNTHETIC SOFTWARE TEST; NOT HARDWARE PERFORMANCE.**' if result['mode'] == 'fixture' else '**Measured local inference; review environment and limits before publication.**', '', '| Workload | Clients | Repeat | Success / requests | Quality passes | Batch seconds | Aggregate output tokens/s |', '|---|---:|---:|---:|---:|---:|---:|']
    for b in result['batches']:
        ok = sum(r['status'] == 'ok' for r in b['requests'])
        passed = sum(r.get('quality', {}).get('passed', False) for r in b['requests'])
        lines.append(f"| {b['workload']} | {b['concurrency']} | {b['repeat'] + 1} | {ok}/{len(b['requests'])} | {passed} | {b['wall_seconds']:.4f} | {b['aggregate_output_tokens_per_second']:.2f} |")
    lines += ['', 'Per-request TTFT, server timing, throughput and errors are retained in the JSON. Client concurrency does not establish server parallelism or autonomous agent capability.', '', 'Unmeasured: ' + ', '.join(result.get('unmeasured', [])), '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    inv = sub.add_parser('inventory'); inv.add_argument('--output', required=True)
    check = sub.add_parser('check'); check.add_argument('--probe-server', action='store_true'); check.add_argument('--endpoint', default='http://127.0.0.1:11434')
    bench = sub.add_parser('run'); bench.add_argument('--config', default=str(ROOT / 'benchmarks/configurations/smoke.json')); bench.add_argument('--output', required=True); bench.add_argument('--fixture', action='store_true'); bench.add_argument('--allow-inference', action='store_true'); bench.add_argument('--endpoint', default='http://127.0.0.1:11434')
    for command in ('validate', 'report'):
        p = sub.add_parser(command); p.add_argument('result')
        if command == 'report': p.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'inventory': save(args.output, inventory())
        elif args.command == 'check':
            info = {'python_supported': sys.version_info >= (3, 10), 'python': platform.python_version(), 'ollama_cli_present': shutil.which('ollama') is not None, 'server_probed': args.probe_server}
            if args.probe_server: info['server_version'] = get_json(endpoint_check(args.endpoint), '/api/version').get('version')
            print(json.dumps(info, indent=2))
        elif args.command == 'run':
            if not args.fixture and not args.allow_inference: raise ValueError('real inference requires --allow-inference; review bounded configuration first')
            save(args.output, run(read_json(args.config), endpoint_check(args.endpoint), args.fixture))
        elif args.command == 'validate': validate(read_json(args.result)); print('Result valid')
        elif args.command == 'report': Path(args.output).write_text(report(read_json(args.result)), encoding='utf-8')
        return 0
    except (ValueError, KeyError, TypeError, OSError) as e:
        print('Operation failed: ' + type(e).__name__ + '; inspect inputs and local server (raw error omitted for privacy).', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
