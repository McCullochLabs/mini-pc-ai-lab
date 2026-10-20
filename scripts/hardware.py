"""Allowlisted, non-admin hardware inventory and sampled system telemetry.

No host/user names, device IDs, process lists, environment or command errors are
returned. System memory is not process memory; sampled peaks are lower bounds.
"""
import ctypes
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import threading
import time
from pathlib import Path


VERSION = '1'


def _run(args, timeout=2):
    try:
        result = subprocess.run(args, capture_output=True, text=True,
                                timeout=timeout, check=False)
        return result.stdout[:65536] if result.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return None


def _read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')[:262144]
    except OSError:
        return ''


def _positive(value, allow_zero=False):
    try:
        number = int(value)
        return number if number > 0 or allow_zero and number == 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def _vendor(name):
    value = name.lower()
    if 'nvidia' in value:
        return 'NVIDIA'
    if 'intel' in value:
        return 'Intel'
    if 'amd' in value or 'radeon' in value or 'advanced micro devices' in value:
        return 'AMD'
    return 'Unknown'


def _windows_memory():
    class MemoryStatus(ctypes.Structure):
        _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
            (name, ctypes.c_ulonglong) for name in (
                'total_physical', 'available_physical', 'total_page',
                'available_page', 'total_virtual', 'available_virtual', 'extended')]
    try:
        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return None, None
        return int(status.total_physical), int(status.available_physical)
    except (AttributeError, OSError):
        return None, None


def _windows_cpu():
    class FileTime(ctypes.Structure):
        _fields_ = [('low', ctypes.c_uint32), ('high', ctypes.c_uint32)]
    try:
        idle, kernel, user = FileTime(), FileTime(), FileTime()
        if not ctypes.windll.kernel32.GetSystemTimes(
                ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            return None
        def ticks(value):
            return (value.high << 32) | value.low
        # Windows kernel ticks include idle ticks.
        return ticks(idle), ticks(kernel) + ticks(user)
    except (AttributeError, OSError):
        return None


def _windows_details():
    # Fixed allowlist: never serialize complete CIM objects or diagnostic stderr.
    executable = shutil.which('powershell.exe')
    if not executable:
        return {}
    command = ("$ErrorActionPreference='Stop'; "
               "[ordered]@{cpu=@(Get-CimInstance Win32_Processor | "
               "Select-Object -ExpandProperty Name); "
               "gpus=@(Get-CimInstance Win32_VideoController | "
               "Select-Object -ExpandProperty Name); "
               "memory=Get-CimInstance Win32_OperatingSystem | "
               "Select-Object TotalVisibleMemorySize,FreePhysicalMemory} | "
               "ConvertTo-Json -Compress -Depth 3")
    output = _run([executable, '-NoProfile', '-NonInteractive', '-Command', command])
    try:
        data = json.loads(output) if output else {}
        return data if isinstance(data, dict) else {}
    except (TypeError, ValueError):
        return {}


def _linux_memory():
    values = {}
    for line in _read('/proc/meminfo').splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[0] in ('MemTotal:', 'MemAvailable:') and fields[2] == 'kB':
            amount = _positive(fields[1], allow_zero=fields[0] == 'MemAvailable:')
            if amount is not None:
                values[fields[0]] = amount * 1024
    # MemFree is not a substitute for MemAvailable.
    return values.get('MemTotal:'), values.get('MemAvailable:')


def _linux_cpu():
    line = next((line for line in _read('/proc/stat').splitlines()
                 if line.startswith('cpu ')), '')
    try:
        values = [int(value) for value in line.split()[1:9]]
        if len(values) < 4 or any(value < 0 for value in values):
            return None
        return values[3] + (values[4] if len(values) > 4 else 0), sum(values)
    except ValueError:
        return None


def _linux_gpus():
    # lspci without -v/-k exposes controller descriptions, not serials or paths.
    executable = shutil.which('lspci')
    output = _run([executable, '-mm']) if executable else None
    result = []
    if output:
        import shlex
        for line in output.splitlines():
            try:
                fields = shlex.split(line)
            except ValueError:
                continue
            if len(fields) >= 4 and fields[1] in (
                    'VGA compatible controller', '3D controller', 'Display controller'):
                name = (' '.join(fields[2:4]))[:200]
                result.append({'name': name, 'vendor': _vendor(name),
                               'dedicated_memory_bytes': None, 'source': 'lspci -mm'})
    if not result:
        # Read only vendor fields under numeric DRM cards, not serials/uevents.
        try:
            cards = sorted(Path('/sys/class/drm').glob('card[0-9]*'))
        except OSError:
            cards = []
        for card in cards:
            if not card.name[4:].isdigit():
                continue
            vendor = {'0x8086': 'Intel', '0x1002': 'AMD', '0x10de': 'NVIDIA'}.get(
                _read(card / 'device/vendor').strip().lower())
            if vendor:
                result.append({'name': vendor + ' graphics adapter (model unavailable)',
                               'vendor': vendor, 'dedicated_memory_bytes': None,
                               'source': 'Linux DRM vendor field'})
    return result


def _nvidia_sample():
    executable = shutil.which('nvidia-smi')
    if not executable:
        return []
    output = _run([executable, '--query-gpu=name,memory.total,memory.used,utilization.gpu,driver_version',
                   '--format=csv,noheader,nounits'])
    samples = []
    for line in (output or '').splitlines():
        fields = [field.strip() for field in line.split(',')]
        if len(fields) != 5:
            continue
        def number(value, scale=1, maximum=None):
            try:
                parsed = float(value)
                if not math.isfinite(parsed) or parsed < 0 or (maximum is not None and parsed > maximum):
                    return None
                return int(parsed * scale) if scale != 1 else parsed
            except ValueError:
                return None
        samples.append({'name': fields[0][:200], 'vendor': 'NVIDIA',
                        'dedicated_memory_bytes': number(fields[1], 1024 * 1024),
                        'memory_used_bytes': number(fields[2], 1024 * 1024),
                        'utilization_percent': number(fields[3], maximum=100),
                        'driver_version': fields[4][:80], 'source': 'nvidia-smi'})
    return samples


def _memory(system):
    if system == 'Windows':
        return _windows_memory()
    if system == 'Linux':
        return _linux_memory()
    return None, None


def available_ram_bytes():
    """Quick physical-memory refresh, without CIM, GPU probes or inventory."""
    total, available = _memory(platform.system())
    if (type(total) is not int or type(available) is not int or total <= 0
            or not 0 <= available <= total):
        return None
    return available


def validate_resources(record, fixture=False):
    """Reject malformed/non-finite telemetry; never fill missing observations."""
    if record is None:
        return None
    if not isinstance(record, dict):
        raise ValueError('resources must be an object or null')
    required = {'sampling_interval_seconds', 'scope', 'clock', 'sample_count',
                'samples', 'peak_system_used_ram_bytes', 'min_available_ram_bytes',
                'mean_system_cpu_percent', 'peak_nvidia_memory_used_bytes',
                'sources', 'warnings', 'thermals', 'power'}
    if not required.issubset(record):
        raise ValueError('resources missing required fields')
    if record['scope'] != 'local_system':
        raise ValueError('resources scope must be local_system')
    if not isinstance(record['clock'], str) or not record['clock']:
        raise ValueError('resource clock label missing')
    sources = record['sources']
    if (not isinstance(sources, dict) or not sources or
            any(not isinstance(key, str) or not key or
                value is not None and (not isinstance(value, str) or not value)
                for key, value in sources.items())):
        raise ValueError('resource source labels invalid')
    if fixture and ('synthetic-fixture' not in sources.values() or
                    record.get('source') != 'synthetic-fixture'):
        raise ValueError('fixture telemetry must be explicitly synthetic')
    if not fixture and (record.get('source') == 'synthetic-fixture' or
                        'synthetic-fixture' in sources.values()):
        raise ValueError('synthetic telemetry cannot be a real measurement')
    if (not isinstance(record['warnings'], list) or
            any(not isinstance(item, str) for item in record['warnings'])):
        raise ValueError('resource warnings must be strings')
    def number(value, name, maximum=None, integer=False):
        if value is None:
            return
        if (isinstance(value, bool) or not isinstance(value, (int, float)) or
                not math.isfinite(value) or value < 0 or
                integer and type(value) is not int or
                maximum is not None and value > maximum):
            raise ValueError('invalid resource metric: ' + name)
    interval = record['sampling_interval_seconds']
    number(interval, 'sampling_interval_seconds', 60)
    if interval is None or interval < 0.1:
        raise ValueError('invalid resource sampling interval')
    samples = record['samples']
    count = record['sample_count']
    if type(count) is not int or count < 0 or not isinstance(samples, list) or len(samples) != count:
        raise ValueError('resource sample count inconsistent')
    for key in ('peak_system_used_ram_bytes', 'min_available_ram_bytes', 'peak_nvidia_memory_used_bytes'):
        number(record[key], key, integer=True)
    number(record['mean_system_cpu_percent'], 'mean_system_cpu_percent', 100)
    if record['thermals'] is not None or record['power'] is not None:
        raise ValueError('thermal and power measurements unsupported by this collector')
    previous_time = -1
    for sample in samples:
        keys = {'elapsed_seconds', 'total_ram_bytes', 'available_ram_bytes',
                'system_used_ram_bytes', 'system_cpu_percent', 'nvidia_gpus'}
        if not isinstance(sample, dict) or not keys.issubset(sample):
            raise ValueError('invalid resource sample')
        elapsed = sample['elapsed_seconds']
        number(elapsed, 'elapsed_seconds')
        if elapsed is None or elapsed < previous_time:
            raise ValueError('resource timestamps must be ordered')
        previous_time = elapsed
        for key in ('total_ram_bytes', 'available_ram_bytes', 'system_used_ram_bytes'):
            number(sample[key], key, integer=True)
        total, available, used = (sample[key] for key in (
            'total_ram_bytes', 'available_ram_bytes', 'system_used_ram_bytes'))
        if total is not None and (total == 0 or available is not None and available > total):
            raise ValueError('resource RAM bounds inconsistent')
        if total is not None and available is not None and used != total - available:
            raise ValueError('resource used RAM inconsistent')
        if (total is None or available is None) and used is not None:
            raise ValueError('resource used RAM requires measured total and available')
        number(sample['system_cpu_percent'], 'system_cpu_percent', 100)
        if not isinstance(sample['nvidia_gpus'], list):
            raise ValueError('GPU samples must be a list')
        for gpu in sample['nvidia_gpus']:
            if not isinstance(gpu, dict):
                raise ValueError('GPU sample must be an object')
            for key in ('dedicated_memory_bytes', 'memory_used_bytes', 'utilization_percent'):
                if key not in gpu:
                    raise ValueError('GPU sample missing metrics')
                number(gpu[key], key, 100 if key == 'utilization_percent' else None,
                       integer=key != 'utilization_percent')
            if (gpu['dedicated_memory_bytes'] is not None and gpu['memory_used_bytes'] is not None
                    and gpu['memory_used_bytes'] > gpu['dedicated_memory_bytes']):
                raise ValueError('GPU memory exceeds total')
            if not isinstance(gpu.get('source'), str) or not gpu['source']:
                raise ValueError('GPU source label missing')
    return record


def collect_inventory():
    system = platform.system()
    total, available = _memory(system)
    cpu = None
    gpus = []
    memory_source = {'Windows': 'GlobalMemoryStatusEx', 'Linux': '/proc/meminfo'}.get(system)
    cpu_source = None
    if system == 'Windows':
        details = _windows_details()
        names = details.get('cpu', [])
        if isinstance(names, str):
            names = [names]
        if not isinstance(names, list):
            names = []
        cpu = '; '.join(str(name)[:200] for name in names if isinstance(name, str)) or None
        cpu_source = 'CIM Win32_Processor.Name' if cpu else None
        gpu_names = details.get('gpus', [])
        if isinstance(gpu_names, str):
            gpu_names = [gpu_names]
        for name in gpu_names if isinstance(gpu_names, list) else []:
            if isinstance(name, str):
                gpus.append({'name': name[:200], 'vendor': _vendor(name),
                             'dedicated_memory_bytes': None, 'source': 'CIM Win32_VideoController.Name'})
        if total is None or available is None:
            mem = details.get('memory', {})
            if isinstance(mem, dict):
                fallback_total = _positive(mem.get('TotalVisibleMemorySize'))
                fallback_available = _positive(mem.get('FreePhysicalMemory'), allow_zero=True)
                if fallback_total is not None and fallback_available is not None:
                    total, available = fallback_total * 1024, fallback_available * 1024
                    memory_source = 'CIM Win32_OperatingSystem memory (KiB)'
    elif system == 'Linux':
        for line in _read('/proc/cpuinfo').splitlines():
            if line.split(':', 1)[0].strip() in ('model name', 'Hardware') and ':' in line:
                cpu = line.split(':', 1)[1].strip()[:200] or None
                break
        cpu_source = '/proc/cpuinfo' if cpu else None
        gpus = _linux_gpus()
    nvidia = _nvidia_sample()
    # NVIDIA total is explicit device framebuffer memory, never AdapterRAM/shared RAM.
    if nvidia:
        gpus = [gpu for gpu in gpus if gpu['vendor'] != 'NVIDIA'] + [
            {key: gpu[key] for key in ('name', 'vendor', 'dedicated_memory_bytes', 'source')}
            for gpu in nvidia]
    if total is not None and (total <= 0 or available is not None and not 0 <= available <= total):
        total, available = None, None
    warnings = []
    if total is None or available is None:
        warnings.append('RAM inventory unavailable; inference guard must fail closed.')
    if cpu is None:
        warnings.append('CPU model unavailable.')
    if not gpus:
        warnings.append('GPU inventory unavailable; no GPU absence or backend inference is implied.')
    inventory = {'os': system, 'os_release': platform.release(),
                 'architecture': platform.machine(), 'python': platform.python_version(),
                 'cpu_model': cpu, 'logical_cpus': os.cpu_count(),
                 'total_ram_bytes': total, 'available_ram_bytes': available,
                 'gpus': gpus, 'warnings': warnings,
                 'sources': {'ram': memory_source, 'cpu_model': cpu_source,
                             'collector_version': VERSION}}
    stable = {key: inventory[key] for key in (
        'os', 'os_release', 'architecture', 'cpu_model', 'logical_cpus', 'total_ram_bytes', 'gpus')}
    inventory['fingerprint'] = hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()
    return inventory


def _cpu_delta(previous, current):
    if previous is None or current is None:
        return None
    idle, total = current[0] - previous[0], current[1] - previous[1]
    if total <= 0 or idle < 0 or idle > total:
        return None
    return 100.0 * (total - idle) / total


class ResourceMonitor:
    """Sample local system resources, never attribute them to a remote server."""
    def __init__(self, interval_seconds=0.5):
        if isinstance(interval_seconds, bool) or not isinstance(interval_seconds, (int, float)) or not math.isfinite(interval_seconds) or not 0.1 <= interval_seconds <= 60:
            raise ValueError('sampling interval must be 0.1..60 seconds')
        self.interval_seconds = interval_seconds
        self._event = threading.Event()
        self._lock = threading.Lock()
        self._thread = None
        self._samples = []
        self._previous_cpu = None
        self._started = None
        self._system = platform.system()
        self._errors = 0

    def _sample(self):
        total, available = _memory(self._system)
        if total is None or available is None or total <= 0 or not 0 <= available <= total:
            total, available = None, None
        ticks = (_windows_cpu() if self._system == 'Windows' else
                 _linux_cpu() if self._system == 'Linux' else None)
        cpu = _cpu_delta(self._previous_cpu, ticks)
        self._previous_cpu = ticks
        sample = {'elapsed_seconds': time.monotonic() - self._started,
                  'total_ram_bytes': total, 'available_ram_bytes': available,
                  'system_used_ram_bytes': total - available if total is not None else None,
                  'system_cpu_percent': cpu, 'nvidia_gpus': _nvidia_sample()}
        with self._lock:
            self._samples.append(sample)

    def _loop(self):
        while not self._event.is_set():
            try:
                self._sample()
            except Exception:
                # No exception text: OS/CLI failures can include private paths.
                with self._lock:
                    self._errors += 1
            self._event.wait(self.interval_seconds)

    def start(self):
        if self._started is not None:
            raise RuntimeError('monitor instances are single-use')
        self._started = time.monotonic()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._event.set()
        if self._thread:
            # Drain the in-flight sample before returning. Its only subprocess
            # has a two-second timeout; do not leave telemetry work behind.
            self._thread.join()
        with self._lock:
            samples = list(self._samples)
            errors = self._errors
        def values(key):
            return [sample[key] for sample in samples if sample[key] is not None]
        def maximum(items):
            return max(items) if items else None
        available = values('available_ram_bytes')
        cpu = values('system_cpu_percent')
        gpu_totals = [sum(gpu['memory_used_bytes'] for gpu in sample['nvidia_gpus'])
                      for sample in samples if sample['nvidia_gpus'] and
                      all(gpu['memory_used_bytes'] is not None for gpu in sample['nvidia_gpus'])]
        return {'sampling_interval_seconds': self.interval_seconds,
                'scope': 'local_system', 'clock': 'monotonic elapsed seconds',
                'sample_count': len(samples), 'samples': samples,
                'peak_system_used_ram_bytes': maximum(values('system_used_ram_bytes')),
                'min_available_ram_bytes': min(available) if available else None,
                'mean_system_cpu_percent': sum(cpu) / len(cpu) if cpu else None,
                'peak_nvidia_memory_used_bytes': maximum(gpu_totals),
                'sources': {'ram': {'Windows': 'GlobalMemoryStatusEx', 'Linux': '/proc/meminfo'}.get(self._system),
                            'cpu': {'Windows': 'GetSystemTimes delta', 'Linux': '/proc/stat delta'}.get(self._system),
                            'gpu': 'nvidia-smi when available', 'collector_version': VERSION},
                'warnings': (['Sampling failed; some observations unavailable.'] if errors else []) +
                            (['Sampler did not stop within bounded join.'] if self._thread and self._thread.is_alive() else []) +
                            ['System-wide sampled values; not process or model allocation. Peaks may miss short spikes.'],
                'thermals': None, 'power': None}

    def __enter__(self):
        return self.start()

    def __exit__(self, *exception):
        self.stop()
