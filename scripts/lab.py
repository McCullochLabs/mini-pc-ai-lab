"""Mini PC AI Lab: Python 3.10+ standard-library-only, opt-in local benchmark."""
import argparse
import concurrent.futures
import datetime
import json
import math
import hashlib
import html
import importlib.util
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
METRICS = ('total_duration', 'load_duration', 'prompt_eval_count', 'prompt_eval_duration', 'eval_count', 'eval_duration')
UNMEASURED = ['peak_ram', 'gpu_memory', 'cpu_utilization', 'gpu_utilization', 'thermals', 'power', 'server_queue_time', 'agent_coordination']
VERSION = '1.0.0'


def sibling(name):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def workloads():
    return read_json(ROOT / 'benchmarks/workloads/synthetic.json') | sibling('coding').WORKLOADS


def read_json(path):
    def reject(value):
        raise ValueError('non-finite JSON number')
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=reject)
    except RecursionError as error:
        raise ValueError('JSON nesting limit exceeded') from error


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


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
    if workload not in ('defect_review', 'structured_qa'):
        return sibling('coding').grade(workload, answer)
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
    if 'threads' in config:
        payload['options']['num_thread'] = config['threads']
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
        return validate_v2(result) if isinstance(result, dict) and result.get('schema_version') == 2 else _validate(result)
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


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def config_v2(config):
    value = dict(config)
    warmups = value.pop('warmups', 0)
    budget = value.pop('run_budget_seconds', 120)
    threads = value.pop('threads', 2)
    integer(threads, 1, 4, 'threads')
    integer(warmups, 0, 1, 'warmups')
    integer(budget, 1, 900, 'run budget')
    ids = value.get('workloads')
    if not isinstance(ids, list) or not ids or any(type(w) is not str or w not in workloads() for w in ids) or len(set(ids)) != len(ids):
        raise ValueError('unsupported workload selection')
    proxy = dict(value, workloads=['defect_review'])
    config_check(proxy)
    return value | {'warmups': warmups, 'run_budget_seconds': budget, 'threads': threads}


def models(endpoint):
    data = get_json(endpoint_check(endpoint), '/api/tags')
    if not isinstance(data, dict) or not isinstance(data.get('models'), list):
        raise ValueError('invalid installed model list')
    output = []
    for model in data['models']:
        if not isinstance(model, dict) or not isinstance(model.get('name'), str):
            raise ValueError('invalid model metadata')
        details = model.get('details') or {}
        if not isinstance(details, dict):
            raise ValueError('invalid model details')
        if not model['name'] or len(model['name']) > 200 or any(c.isspace() for c in model['name']):
            raise ValueError('invalid installed model name')
        integer(model.get('size'), 1, 10**18, 'model size')
        if not isinstance(model.get('digest'), str) or not model['digest'] or len(model['digest']) > 200:
            raise ValueError('invalid model digest')
        for key in ('format', 'family', 'parameter_size', 'quantization_level'):
            if details.get(key) is not None and (type(details[key]) is not str or len(details[key]) > 200):
                raise ValueError('invalid model details')
        output.append({k: model.get(k) for k in ('name', 'digest', 'size')} | {'details': {k: details.get(k) for k in ('format', 'family', 'parameter_size', 'quantization_level')}})
    return output


def capacity_check(config, model, hardware, allow_heavy=False):
    total = hardware.get('total_ram_bytes')
    available = hardware.get('available_ram_bytes')
    if type(total) is not int or type(available) is not int or total <= 0 or available <= 0:
        raise ValueError('RAM capacity unavailable; real inference refused')
    size = integer(model.get('size'), 1, 10**18, 'installed model size')
    # This conservative heuristic is an admission guard, not a memory prediction.
    reserve = 2 * 1024**3 + config['context_length'] * 1024**2 // 2
    if size * 2 + reserve > available or size * 2 + reserve > total:
        raise ValueError('insufficient RAM headroom under conservative model-size guard')
    heavy = max(config['concurrency']) > 1 or config['num_predict'] > 128 or config['context_length'] > 2048 or config['threads'] > 2 or config['repeats'] > 1 or config['warmups'] > 0 or config['run_budget_seconds'] > 120 or size > 2 * 1024**3
    if heavy and not allow_heavy:
        raise ValueError('configuration requires explicit --allow-heavy as well as inference permission')
    return {'source': 'conservative-file-size-heuristic-v1', 'model_size_bytes': size, 'required_available_bytes': size * 2 + reserve, 'available_ram_bytes': available, 'allow_heavy': allow_heavy, 'warning': 'not a guarantee against OOM; GPU placement and KV cache vary'}


def backend(endpoint, model):
    try:
        entries = get_json(endpoint, '/api/ps').get('models', [])
        item = next((m for m in entries if m.get('name') == model), None)
        if item is None:
            return {'source': 'ollama-api-ps', 'placement': 'unknown', 'size_vram_bytes': None, 'note': 'model not listed at observation time'}
        size = item.get('size'); vram = item.get('size_vram')
        if type(size) is not int or type(vram) is not int or size <= 0 or vram < 0:
            raise ValueError('invalid residency metrics')
        return {'source': 'ollama-api-ps', 'placement': 'cpu-reported' if vram == 0 else 'gpu-resident-or-mixed', 'size_vram_bytes': vram, 'reported_size_bytes': size, 'note': 'residency report does not prove utilization or identify iGPU versus dGPU'}
    except (OSError, ValueError, TypeError, KeyError):
        return {'source': 'ollama-api-ps', 'placement': 'unknown', 'size_vram_bytes': None, 'note': 'residency query unavailable'}


def run_v2(config, endpoint, fixture=False, allow_heavy=False, output=None, model_override=None, sponsor='unknown / not supplied'):
    endpoint = endpoint_check(endpoint)
    config = config_v2(config)
    if model_override:
        config['model'] = model_override
    selected = None
    if fixture:
        hardware = {'source': 'synthetic-fixture', 'os': 'FixtureOS', 'os_release': 'test', 'architecture': 'synthetic', 'cpu_model': 'synthetic CPU', 'logical_cpus': 4, 'total_ram_bytes': 16 * 1024**3, 'available_ram_bytes': 12 * 1024**3, 'gpus': [], 'warnings': ['Fixture; not current hardware']}
        version = 'fixture-only'
        guard = {'source': 'fixture-no-inference'}
    else:
        hardware = sibling('hardware').collect_inventory()
        installed = models(endpoint)
        name = config['model']
        if name.startswith('REPLACE_') or name == 'auto':
            candidates = sorted((m for m in installed if type(m.get('size')) is int and m['size'] > 0), key=lambda m: (m['size'], m['name']))
            for candidate in candidates:
                try:
                    capacity_check(config, candidate, hardware, allow_heavy)
                    selected = candidate
                    break
                except ValueError:
                    pass
            if selected is None:
                raise ValueError('no installed model fits known RAM and selected safety limits')
            config['model'] = selected['name']
        else:
            selected = next((m for m in installed if m['name'] == name), None)
        if selected is None:
            raise ValueError('exact model not installed; no model will be pulled')
        config = config_v2(config)
        guard = capacity_check(config, selected, hardware, allow_heavy)
        version = get_json(endpoint, '/api/version').get('version')
        if not isinstance(version, str) or not version:
            raise ValueError('server version unavailable')
    specs = {k: hardware.get(k) for k in ('os', 'os_release', 'architecture', 'cpu_model', 'logical_cpus', 'total_ram_bytes', 'gpus')}
    hardware_id = digest(specs)
    tasks = workloads()
    result = {'schema_version': 2, 'toolkit_version': VERSION, 'run_id': str(uuid.uuid4()), 'created_utc': utc(), 'completed_utc': None, 'mode': 'fixture' if fixture else 'measured', 'status': 'running', 'config': config, 'hardware_id': hardware_id, 'hardware': hardware, 'model_metadata': selected, 'ollama_version': version, 'capacity_guard': guard, 'workload_digest': digest({w: tasks[w]['prompt'] for w in config['workloads']}), 'batches': [], 'warmups': [], 'warnings': ['TTFT is first nonempty output fragment, not exact token timing.', 'Client dispatch delay is not server queue time.', 'Timeout is per blocking read with an elapsed guard; in-flight requests are drained before exit.', 'Power, thermals, server queue time and autonomous agent coordination are unmeasured.'], 'disclosure': {'hardware_sponsorship': sponsor}, 'resources': None, 'backend': {'source': 'fixture' if fixture else 'not-yet-observed', 'placement': 'unknown'}}
    monitor = None
    started = time.perf_counter()
    def checkpoint():
        if output:
            save(output, result)
    checkpoint()
    try:
        if not fixture:
            monitor = sibling('hardware').ResourceMonitor(interval_seconds=0.5)
            monitor.start()
        for phase in ('warmup', 'measured'):
            repeats = config['warmups'] if phase == 'warmup' else config['repeats']
            for concurrency in ([1] if phase == 'warmup' else config['concurrency']):
                for repeat in range(repeats):
                    for workload in config['workloads']:
                        if not fixture and time.perf_counter() - started >= config['run_budget_seconds']:
                            result['status'] = 'budget_exhausted'
                            raise StopIteration
                        if not fixture:
                            free_ram = sibling('hardware').available_ram_bytes()
                            if type(free_ram) is not int or free_ram < 1024**3:
                                result['status'] = 'failed'
                                result['warnings'].append('Available RAM unknown or below 1 GiB; memory pressure safety stop prevents further dispatch.')
                                raise StopIteration
                        batch_started = time.perf_counter()
                        def request(index):
                            dispatched = time.perf_counter()
                            if fixture:
                                item = read_json(ROOT / 'benchmarks/fixtures/request.json') | {'workload': workload}
                            else:
                                try:
                                    item = generate(endpoint, config, workload, tasks[workload]['prompt'])
                                except Exception as error:
                                    item = {'workload': workload, 'status': 'error', 'error_type': type(error).__name__, 'wall_seconds': time.perf_counter() - dispatched}
                            return item | {'request_id': str(uuid.uuid4()), 'client_index': index, 'client_dispatch_delay_seconds': 0.0 if fixture else dispatched - batch_started}
                        # The context manager drains every in-flight worker, including after interrupt.
                        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
                            requests = list(pool.map(request, range(concurrency)))
                        elapsed = 2.0 if fixture else time.perf_counter() - batch_started
                        count = sum(q.get('metrics', {}).get('eval_count', 0) for q in requests if q['status'] == 'ok')
                        batch = {'phase': phase, 'concurrency': concurrency, 'repeat': repeat, 'workload': workload, 'wall_seconds': elapsed, 'aggregate_output_tokens_per_second': count / elapsed, 'requests': requests}
                        result['warmups' if phase == 'warmup' else 'batches'].append(batch)
                        checkpoint()
        result['status'] = 'completed_with_errors' if any(q['status'] == 'error' for b in result['batches'] for q in b['requests']) else 'completed'
    except StopIteration:
        if result['status'] == 'budget_exhausted':
            result['warnings'].append('Run budget stopped further batch dispatch; completed batches retained.')
    except KeyboardInterrupt:
        result['status'] = 'interrupted'
        result['warnings'].append('Operator interruption; completed batches retained. In-flight workers drained before return.')
    except Exception as error:
        result['status'] = 'failed'
        result['warnings'].append('Run failed: ' + type(error).__name__ + '; raw error omitted.')
    finally:
        if monitor is not None:
            try:
                result['resources'] = monitor.stop()
            except Exception as error:
                result['warnings'].append('Resource monitor unavailable: ' + type(error).__name__)
        elif fixture:
            result['resources'] = {'source': 'synthetic-fixture', 'scope': 'local_system', 'sample_count': 0, 'samples': [], 'sources': {'collector': 'synthetic-fixture'}, 'sampling_interval_seconds': 0.5, 'clock': 'synthetic-fixture', 'peak_system_used_ram_bytes': None, 'min_available_ram_bytes': None, 'mean_system_cpu_percent': None, 'peak_nvidia_memory_used_bytes': None, 'warnings': ['Synthetic; no hardware sampled'], 'thermals': None, 'power': None}
        result['backend'] = {'source': 'synthetic-fixture', 'placement': 'unknown'} if fixture else backend(endpoint, config['model'])
        result['completed_utc'] = utc()
        result['warnings'].extend(hardware.get('warnings', []))
        checkpoint()
    validate(result)
    return result


def validate_v2(result):
    mandatory = {'schema_version', 'toolkit_version', 'run_id', 'created_utc', 'completed_utc', 'mode', 'status', 'config', 'hardware_id', 'hardware', 'model_metadata', 'ollama_version', 'capacity_guard', 'workload_digest', 'batches', 'warmups', 'warnings', 'disclosure', 'resources', 'backend'}
    if type(result['schema_version']) is not int or result['schema_version'] != 2 or not mandatory <= result.keys():
        raise ValueError('invalid v2 schema')
    if result['toolkit_version'] != VERSION or result['mode'] not in ('fixture', 'measured') or result['status'] not in ('running', 'completed', 'completed_with_errors', 'budget_exhausted', 'interrupted', 'failed'):
        raise ValueError('invalid run provenance')
    uuid.UUID(result['run_id'])
    for key in ('created_utc', 'completed_utc'):
        if key == 'completed_utc' and result[key] is None and result['status'] == 'running':
            continue
        stamp = datetime.datetime.fromisoformat(result[key].replace('Z', '+00:00'))
        if stamp.tzinfo is None or stamp.utcoffset() != datetime.timedelta(0):
            raise ValueError('timestamp must use explicit UTC')
    if result['completed_utc'] is not None and datetime.datetime.fromisoformat(result['completed_utc'].replace('Z', '+00:00')) < datetime.datetime.fromisoformat(result['created_utc'].replace('Z', '+00:00')):
        raise ValueError('completion predates creation')
    config = config_v2(result['config'])
    specs = {k: result['hardware'].get(k) for k in ('os', 'os_release', 'architecture', 'cpu_model', 'logical_cpus', 'total_ram_bytes', 'gpus')}
    if result['hardware_id'] != digest(specs):
        raise ValueError('hardware fingerprint inconsistent')
    expected_digest = digest({w: workloads()[w]['prompt'] for w in config['workloads']})
    if result['workload_digest'] != expected_digest:
        raise ValueError('workload revision differs from installed toolkit')
    if not isinstance(result['warnings'], list) or any(type(w) is not str for w in result['warnings']) or not isinstance(result['disclosure'].get('hardware_sponsorship'), str):
        raise ValueError('missing warnings/disclosure')
    if result['backend'].get('source') not in ('synthetic-fixture', 'ollama-api-ps', 'not-yet-observed') or result['backend'].get('placement') not in ('unknown', 'cpu-reported', 'gpu-resident-or-mixed'):
        raise ValueError('missing backend provenance')
    vram = result['backend'].get('size_vram_bytes')
    if vram is not None:
        integer(vram, 0, 10**18, 'backend VRAM')
    if result['resources'] is not None and not isinstance(result['resources'], dict):
        raise ValueError('invalid resource summary')
    if result['resources'] is None and result['status'] in ('completed', 'completed_with_errors') and not any(w.startswith('Resource monitor unavailable:') for w in result['warnings']):
        raise ValueError('completed run missing resource observation record')
    if result['resources'] is not None and hasattr(sibling('hardware'), 'validate_resources'):
        sibling('hardware').validate_resources(result['resources'], fixture=result['mode'] == 'fixture')
    if result['mode'] == 'fixture' and result['model_metadata'] is not None:
        raise ValueError('fixture model metadata must be null')
    if result['mode'] == 'measured':
        metadata = result['model_metadata']
        if metadata['name'] != config['model'] or not isinstance(metadata['digest'], str) or not metadata['digest'] or not isinstance(result['ollama_version'], str) or not result['ollama_version']:
            raise ValueError('missing model provenance')
        integer(metadata['size'], 1, 10**18, 'model size')
        if not isinstance(metadata['details'], dict) or not isinstance(result['capacity_guard'], dict):
            raise ValueError('invalid model or capacity provenance')
        for key in ('format', 'family', 'parameter_size', 'quantization_level'):
            detail = metadata['details'][key]
            if detail is not None and (type(detail) is not str or len(detail) > 200):
                raise ValueError('invalid model detail')
        capacity = result['capacity_guard']
        if capacity.get('source') != 'conservative-file-size-heuristic-v1' or type(capacity.get('allow_heavy')) is not bool:
            raise ValueError('invalid admission guard provenance')
        for key in ('model_size_bytes', 'required_available_bytes', 'available_ram_bytes'):
            integer(capacity[key], 1, 10**18, key)
        if capacity['model_size_bytes'] != metadata['size'] or capacity['required_available_bytes'] > capacity['available_ram_bytes']:
            raise ValueError('inconsistent admission guard')
        if result['backend']['source'] == 'synthetic-fixture':
            raise ValueError('measured result claims synthetic backend')
    request_ids = set()
    for phase, field in (('measured', 'batches'), ('warmup', 'warmups')):
        if type(result[field]) is not list:
            raise ValueError('invalid batch list')
        repeats = config['repeats'] if phase == 'measured' else config['warmups']
        expected = [(c, r, w) for c in (config['concurrency'] if phase == 'measured' else [1]) for r in range(repeats) for w in config['workloads']]
        actual = []
        for batch in result[field]:
            key = (batch['concurrency'], batch['repeat'], batch['workload'])
            if batch['phase'] != phase or any(type(x) is not int for x in key[:2]) or key not in expected or key in actual:
                raise ValueError('invalid batch identity')
            actual.append(key)
            if type(batch['requests']) is not list or len(batch['requests']) != key[0]:
                raise ValueError('invalid request count')
            if type(batch['wall_seconds']) not in (int, float) or not math.isfinite(batch['wall_seconds']) or batch['wall_seconds'] <= 0:
                raise ValueError('invalid batch duration')
            for index, request in enumerate(batch['requests']):
                if request['workload'] != key[2]:
                    raise ValueError('request workload differs from batch')
                uuid.UUID(request['request_id'])
                if request['request_id'] in request_ids:
                    raise ValueError('duplicate request ID')
                request_ids.add(request['request_id'])
                delay = request['client_dispatch_delay_seconds']
                if type(request['client_index']) is not int or request['client_index'] != index or type(delay) not in (float, int) or not math.isfinite(delay) or delay < 0:
                    raise ValueError('invalid client dispatch timing')
                # Reuse v1 numeric validation on one self-contained observation.
                proxy = dict(config)
                proxy.pop('warmups'); proxy.pop('run_budget_seconds')
                proxy.pop('threads')
                proxy.update(workloads=['defect_review'], concurrency=[1], repeats=1)
                q = dict(request, workload='defect_review')
                if q['status'] == 'ok':
                    expected_grader = 'fixture-synthetic-not-model-output' if result['mode'] == 'fixture' else ('exact-json-v1' if key[2] in ('defect_review', 'structured_qa') else 'static-ast-v1')
                    if q['quality']['grader'] != expected_grader:
                        raise ValueError('invalid grader provenance')
                    q['quality'] = dict(q['quality'], grader='fixture-synthetic-not-model-output')
                small = {'schema_version': 1, 'mode': 'fixture', 'created_utc': result['created_utc'], 'config': proxy, 'model_metadata': None, 'unmeasured': list(UNMEASURED), 'batches': [{'concurrency': 1, 'repeat': 0, 'workload': 'defect_review', 'wall_seconds': batch['wall_seconds'], 'aggregate_output_tokens_per_second': q.get('metrics', {}).get('eval_count', 0) / batch['wall_seconds'] if q['status'] == 'ok' else 0, 'requests': [q]}]}
                _validate(small)
            rate = sum(q.get('metrics', {}).get('eval_count', 0) for q in batch['requests'] if q['status'] == 'ok') / batch['wall_seconds']
            if type(batch['aggregate_output_tokens_per_second']) not in (float, int) or not math.isfinite(batch['aggregate_output_tokens_per_second']) or not math.isclose(batch['aggregate_output_tokens_per_second'], rate, rel_tol=1e-9):
                raise ValueError('invalid aggregate throughput')
        if actual != expected[:len(actual)] or result['status'] in ('completed', 'completed_with_errors') and actual != expected:
            raise ValueError('incomplete/out-of-order batches')
    errors = any(q['status'] == 'error' for b in result['batches'] for q in b['requests'])
    if result['status'] == 'completed' and errors or result['status'] == 'completed_with_errors' and not errors:
        raise ValueError('completion status contradicts request outcomes')
    return True


def report_v2(result):
    validate(result)
    escape = lambda x: html.escape(str(x)).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')
    lines = ['# Mini PC AI Lab evaluation', '', '**FIXTURE — SYNTHETIC; NOT HARDWARE PERFORMANCE.**' if result['mode'] == 'fixture' else '**Measured local inference; independently review provenance before publication.**', '', f"Run: {result['run_id']} · toolkit {VERSION} · status {result['status']}", f"Started: {result['created_utc']} · ended: {result['completed_utc']}", '', '## Hardware and backend', '', f"Specification fingerprint: `{result['hardware_id']}` (not a device serial; identical specs can match).", '', '| Field | Recorded value |', '|---|---|']
    for key in ('os', 'os_release', 'architecture', 'cpu_model', 'logical_cpus', 'total_ram_bytes', 'gpus'):
        lines.append(f'| {key} | {escape(result["hardware"].get(key))} |')
    lines += ['', 'Backend observation: ' + escape(json.dumps(result['backend'], sort_keys=True)), '', '## Model and reproducibility', '', '```json', json.dumps({'model': result['model_metadata'], 'ollama_version': result['ollama_version'], 'config': result['config'], 'workload_digest': result['workload_digest']}, indent=2), '```', '', 'Warm-up batches excluded from measured tables: ' + str(len(result['warmups'])), '', '## Task outcomes and inference', '', '| Task | Clients | Repeat | Success / requests | Quality passes | Wall s | Aggregate tokens/s |', '|---|---:|---:|---:|---:|---:|---:|']
    for batch in result['batches']:
        ok = sum(q['status'] == 'ok' for q in batch['requests'])
        passes = sum(q.get('quality', {}).get('passed', False) for q in batch['requests'])
        lines.append(f"| {batch['workload']} | {batch['concurrency']} | {batch['repeat']+1} | {ok}/{len(batch['requests'])} | {passes} | {batch['wall_seconds']:.4f} | {batch['aggregate_output_tokens_per_second']:.2f} |")
    lines += ['', '| Task / client | Client latency incl. load s | Server load s | Output-fragment TTFT s | Generation tokens/s | Prompt tokens/s | Client dispatch delay s | Error |', '|---|---:|---:|---:|---:|---:|---:|---|']
    for batch in result['batches']:
        for q in batch['requests']:
            m = q.get('metrics', {})
            load = m['load_duration'] / 1e9 if 'load_duration' in m else 'unavailable'
            lines.append(f"| {batch['workload']} / {q['client_index']} | {q.get('wall_seconds', 'unavailable')} | {load} | {q.get('ttft_seconds', 'unavailable')} | {m.get('generation_tokens_per_second', 'unavailable')} | {m.get('prompt_tokens_per_second', 'unavailable')} | {q['client_dispatch_delay_seconds']:.4f} | {q.get('error_type', '—')} |")
    resource_summary = {key: value for key, value in (result['resources'] or {}).items() if key != 'samples'}
    lines += ['', '## System resource observations', '', 'Samples describe the whole system, not isolated model process usage. Sampled peaks are lower bounds. No power or thermal inference is made. Full samples remain in raw JSON.', '', '```json', json.dumps(resource_summary, indent=2), '```', '', '## Warnings and disclosure', '']
    lines.extend('- ' + escape(w) for w in result['warnings'])
    lines += ['', 'Hardware sponsorship: ' + escape(result['disclosure']['hardware_sponsorship']), '', 'API clients share one model. This does not establish autonomous agents, server parallelism or several independent models. Static grading never executes generated code; task success is separate from token speed.', '']
    lines += ['## Reproduce', '', 'Save the exact config object above as `config.json`; retain raw JSON and hardware evidence. The model must already be installed. Review safety limits and authorize inference before running.', '', '```powershell', 'python scripts/lab.py check --probe-server', 'python scripts/lab.py models', 'python scripts/lab.py run --config config.json --allow-inference --output result.json' + (' --allow-heavy' if result['capacity_guard'].get('allow_heavy') else ''), 'python scripts/lab.py validate result.json', 'python scripts/lab.py report result.json --output result.md', '```', '', 'For synthetic reproduction add `--fixture`; fixture numbers do not characterize hardware. Cache/ambient conditions and backend placement require independent review.', '']
    return '\n'.join(lines)


def compare(left, right):
    for value in (left, right):
        validate(value)
        if value['schema_version'] != 2 or value['mode'] != 'measured' or value['status'] != 'completed':
            raise ValueError('comparison requires complete successful v2 measured runs')
    for field in ('toolkit_version', 'config', 'workload_digest', 'ollama_version'):
        if left[field] != right[field]:
            raise ValueError('incompatible comparison: ' + field)
    if left['model_metadata']['digest'] != right['model_metadata']['digest'] or left['model_metadata']['details'] != right['model_metadata']['details']:
        raise ValueError('incompatible model revision/quantization')
    if left['backend']['placement'] != right['backend']['placement']:
        raise ValueError('incompatible backend placement category')
    return {'compatible': True, 'left_run': left['run_id'], 'right_run': right['run_id'], 'left_hardware': left['hardware_id'], 'right_hardware': right['hardware_id'], 'matched_config': left['config'], 'matched_model_digest': left['model_metadata']['digest'], 'matched_backend_category': left['backend']['placement'], 'conditions': {'left_os': left['hardware'].get('os'), 'right_os': right['hardware'].get('os'), 'left_os_release': left['hardware'].get('os_release'), 'right_os_release': right['hardware'].get('os_release'), 'ambient_temperature': 'unmeasured', 'cold_warm_state': 'mixed unless independently documented; warmups recorded', 'sampling': 'whole-system; unrelated load can differ'}, 'note': 'Compatibility is protocol matching, not a claim of controlled ambient/cache conditions. Hardware and OS differences must be disclosed.', 'batches': [{'workload': a['workload'], 'concurrency': a['concurrency'], 'repeat': a['repeat'], 'left_tokens_per_second': a['aggregate_output_tokens_per_second'], 'right_tokens_per_second': b['aggregate_output_tokens_per_second'], 'left_quality_passes': sum(q.get('quality', {}).get('passed', False) for q in a['requests']), 'right_quality_passes': sum(q.get('quality', {}).get('passed', False) for q in b['requests'])} for a, b in zip(left['batches'], right['batches'])]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    parser.add_argument('--version', action='version', version=VERSION)
    inv = sub.add_parser('inventory'); inv.add_argument('--output', required=True)
    check = sub.add_parser('check'); check.add_argument('--probe-server', action='store_true'); check.add_argument('--endpoint', default='http://127.0.0.1:11434')
    bench = sub.add_parser('run'); bench.add_argument('--config', default=str(ROOT / 'benchmarks/configurations/smoke.json')); bench.add_argument('--output', required=True); bench.add_argument('--fixture', action='store_true'); bench.add_argument('--allow-inference', action='store_true'); bench.add_argument('--endpoint', default='http://127.0.0.1:11434')
    bench.add_argument('--model'); bench.add_argument('--allow-heavy', action='store_true'); bench.add_argument('--sponsorship', default='unknown / not supplied')
    bench.add_argument('--threads', type=int); bench.add_argument('--warmups', type=int); bench.add_argument('--repeats', type=int); bench.add_argument('--run-budget', type=int)
    listing = sub.add_parser('models'); listing.add_argument('--endpoint', default='http://127.0.0.1:11434')
    comparison = sub.add_parser('compare'); comparison.add_argument('left'); comparison.add_argument('right'); comparison.add_argument('--output', required=True)
    for command in ('validate', 'report'):
        p = sub.add_parser(command); p.add_argument('result')
        if command == 'report': p.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'inventory': save(args.output, sibling('hardware').collect_inventory())
        elif args.command == 'check':
            info = {'python_supported': sys.version_info >= (3, 10), 'python': platform.python_version(), 'ollama_cli_present': shutil.which('ollama') is not None, 'server_probed': args.probe_server}
            if args.probe_server:
                info['server_version'] = get_json(endpoint_check(args.endpoint), '/api/version').get('version')
                info['installed_model_count'] = len(models(args.endpoint))
                detected = sibling('hardware').collect_inventory()
                info['ram'] = {key: detected.get(key) for key in ('total_ram_bytes', 'available_ram_bytes')}
                info['inference_ready'] = info['installed_model_count'] > 0 and all(type(value) is int and value > 0 for value in info['ram'].values())
                info['next_step'] = 'Select an installed model; run only after reviewing RAM and settings.' if info['inference_ready'] else 'No installed model or RAM unknown: resolve inventory/model availability before inference; nothing is downloaded automatically.'
            print(json.dumps(info, indent=2))
        elif args.command == 'run':
            if not args.fixture and not args.allow_inference: raise ValueError('real inference requires --allow-inference; review bounded configuration first')
            config = read_json(args.config)
            for key, value in (('threads', args.threads), ('warmups', args.warmups), ('repeats', args.repeats), ('run_budget_seconds', args.run_budget)):
                if value is not None:
                    config[key] = value
            result = run_v2(config, endpoint_check(args.endpoint), args.fixture, args.allow_heavy, args.output, args.model, args.sponsorship)
            if result['status'] not in ('completed',):
                return 3
        elif args.command == 'models': print(json.dumps(models(args.endpoint), indent=2))
        elif args.command == 'compare': save(args.output, compare(read_json(args.left), read_json(args.right)))
        elif args.command == 'validate': validate(read_json(args.result)); print('Result valid')
        elif args.command == 'report':
            result = read_json(args.result)
            Path(args.output).write_text(report_v2(result) if result.get('schema_version') == 2 else report(result), encoding='utf-8')
        return 0
    except (ValueError, KeyError, TypeError, OSError, RecursionError) as e:
        if isinstance(e, OSError) and args.command in ('models', 'check', 'run'):
            message = 'Local Ollama API unavailable or request failed. Check the installed Ollama app/service manually and the loopback endpoint; no service is started automatically.'
        elif args.command == 'run':
            message = 'Run refused or inputs invalid. Confirm --allow-inference, known available RAM, exact installed model, bounded configuration, and --allow-heavy for elevated settings. Use check --probe-server and models to inspect readiness.'
        else:
            message = 'Inputs or result provenance invalid. Check configuration keys, schema version, metric types, and the requested operation.'
        print(message + ' Error class: ' + type(e).__name__ + '; raw details omitted for privacy.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
