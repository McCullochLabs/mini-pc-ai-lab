"""Mocked platform fixtures; these do not establish live OS/driver compatibility."""
import importlib.util
import copy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('hardware', Path(__file__).resolve().parents[1] / 'scripts/hardware.py')
hardware = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hardware)


class HardwareTests(unittest.TestCase):
    def test_linux_memory_uses_available_not_free(self):
        with patch.object(hardware, '_read', return_value='MemTotal: 1000 kB\nMemFree: 900 kB\nMemAvailable: 700 kB\n'):
            self.assertEqual(hardware._linux_memory(), (1024000, 716800))
        with patch.object(hardware, '_read', return_value='MemTotal: 1000 kB\nMemFree: 900 kB\n'):
            self.assertEqual(hardware._linux_memory(), (1024000, None))
        with patch.object(hardware, '_read', return_value='MemTotal: 1000 kB\nMemAvailable: 0 kB\n'):
            self.assertEqual(hardware._linux_memory(), (1024000, 0))

    def test_cpu_guest_ticks_are_not_double_counted(self):
        with patch.object(hardware, '_read', return_value='cpu 10 20 30 40 5 6 7 8 1000 1000\ncpu0 1 2 3 4\n'):
            self.assertEqual(hardware._linux_cpu(), (45, 126))
        self.assertEqual(hardware._cpu_delta((30, 100), (50, 200)), 80.0)
        self.assertIsNone(hardware._cpu_delta((30, 100), (20, 200)))
        self.assertIsNone(hardware._cpu_delta((30, 100), (30, 100)))

    def test_linux_gpu_fixture_preserves_unknown_dedicated_memory(self):
        output = ('00:02.0 "VGA compatible controller" "Intel Corporation" "UHD Graphics"\n'
                  '03:00.0 "Display controller" "Advanced Micro Devices, Inc. [AMD/ATI]" "Radeon Graphics"\n'
                  '00:14.0 "USB controller" "Intel" "USB"\n')
        with patch.object(hardware.shutil, 'which', return_value='lspci'), patch.object(hardware, '_run', return_value=output):
            result = hardware._linux_gpus()
        self.assertEqual([gpu['vendor'] for gpu in result], ['Intel', 'AMD'])
        self.assertTrue(all(gpu['dedicated_memory_bytes'] is None for gpu in result))
        self.assertNotIn('00:02.0', json.dumps(result))

    def test_linux_drm_fallback_reports_vendor_without_identifiers(self):
        with patch.object(hardware.shutil, 'which', return_value=None), \
                patch.object(hardware.Path, 'glob', return_value=[Path('card0'), Path('card0-HDMI-A-1')]), \
                patch.object(hardware, '_read', return_value='0x1002\n'):
            result = hardware._linux_gpus()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['vendor'], 'AMD')
        self.assertEqual(result[0]['name'], 'AMD graphics adapter (model unavailable)')
        self.assertIsNone(result[0]['dedicated_memory_bytes'])

    def test_nvidia_fixture_units_and_unavailable_values(self):
        output = 'NVIDIA Fixture, 8192, 2048, 25, 555.1\nNVIDIA Other, N/A, N/A, N/A, 555.1\n'
        with patch.object(hardware.shutil, 'which', return_value='nvidia-smi'), patch.object(hardware, '_run', return_value=output) as run:
            result = hardware._nvidia_sample()
        self.assertEqual(result[0]['dedicated_memory_bytes'], 8192 * 1024**2)
        self.assertEqual(result[0]['memory_used_bytes'], 2048 * 1024**2)
        self.assertEqual(result[0]['utilization_percent'], 25)
        self.assertIsNone(result[1]['memory_used_bytes'])
        command = run.call_args.args[0]
        self.assertNotIn('uuid', ' '.join(command))
        self.assertNotIn('serial', ' '.join(command))

    def test_windows_missing_api_memory_can_use_allowlisted_cim(self):
        details = {'cpu': ['Fixture CPU'], 'gpus': ['Intel UHD'],
                   'memory': {'TotalVisibleMemorySize': 16000, 'FreePhysicalMemory': 8000},
                   'SerialNumber': 'never-return-this'}
        with patch.object(hardware.platform, 'system', return_value='Windows'), \
                patch.object(hardware, '_memory', return_value=(None, None)), \
                patch.object(hardware, '_windows_details', return_value=details), \
                patch.object(hardware, '_nvidia_sample', return_value=[]):
            result = hardware.collect_inventory()
        self.assertEqual(result['total_ram_bytes'], 16000 * 1024)
        self.assertEqual(result['available_ram_bytes'], 8000 * 1024)
        self.assertIsNone(result['gpus'][0]['dedicated_memory_bytes'])
        self.assertNotIn('never-return-this', json.dumps(result))
        self.assertEqual(len(result['fingerprint']), 64)

    def test_unavailable_inventory_is_not_zero_or_gpu_absence(self):
        with patch.object(hardware.platform, 'system', return_value='Unsupported'), \
                patch.object(hardware, '_nvidia_sample', return_value=[]):
            result = hardware.collect_inventory()
        self.assertIsNone(result['total_ram_bytes'])
        self.assertIsNone(result['available_ram_bytes'])
        self.assertTrue(any('fail closed' in warning for warning in result['warnings']))
        self.assertTrue(any('no GPU absence' in warning for warning in result['warnings']))

    def test_linux_inventory_normalized_and_fingerprint_not_available_ram(self):
        with patch.object(hardware.platform, 'system', return_value='Linux'), \
                patch.object(hardware, '_read', return_value='model name : Fixture CPU\n'), \
                patch.object(hardware, '_memory', side_effect=[(10000, 7000), (10000, 5000)]), \
                patch.object(hardware, '_linux_gpus', return_value=[]), \
                patch.object(hardware, '_nvidia_sample', return_value=[]):
            first, second = hardware.collect_inventory(), hardware.collect_inventory()
        self.assertEqual(first['cpu_model'], 'Fixture CPU')
        self.assertEqual(first['fingerprint'], second['fingerprint'])
        self.assertNotIn('hostname', first)
        self.assertNotIn('username', first)

    def test_cli_timeout_and_errors_do_not_disclose_stderr(self):
        with patch.object(hardware.subprocess, 'run', side_effect=subprocess.TimeoutExpired(['private/path'], 2)):
            self.assertIsNone(hardware._run(['anything']))
        with patch.object(hardware.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'secret')):
            self.assertIsNone(hardware._run(['anything']))

    def test_monitor_samples_and_summarizes_system_values(self):
        monitor = hardware.ResourceMonitor(0.1)
        monitor._system = 'Linux'
        monitor._started = hardware.time.monotonic()
        gpu = {'name': 'Fixture', 'memory_used_bytes': 100, 'utilization_percent': 20}
        with patch.object(hardware, '_memory', side_effect=[(1000, 700), (1000, 500)]), \
                patch.object(hardware, '_linux_cpu', side_effect=[(30, 100), (50, 200)]), \
                patch.object(hardware, '_nvidia_sample', return_value=[gpu]):
            monitor._sample()
            monitor._sample()
        result = monitor.stop()
        self.assertEqual(result['sample_count'], 2)
        self.assertIsNone(result['samples'][0]['system_cpu_percent'])
        self.assertEqual(result['mean_system_cpu_percent'], 80)
        self.assertEqual(result['peak_system_used_ram_bytes'], 500)
        self.assertEqual(result['min_available_ram_bytes'], 500)
        self.assertEqual(result['peak_nvidia_memory_used_bytes'], 100)
        self.assertEqual(result['sources']['cpu'], '/proc/stat delta')
        self.assertIsNone(result['power'])
        self.assertIsNone(result['thermals'])
        self.assertEqual(monitor.stop()['sample_count'], 2)

    def test_monitor_missing_observations_remain_null(self):
        monitor = hardware.ResourceMonitor()
        result = monitor.stop()
        self.assertIsNone(result['min_available_ram_bytes'])
        self.assertIsNone(result['mean_system_cpu_percent'])
        self.assertIsNone(result['peak_nvidia_memory_used_bytes'])
        for value in (True, 0, float('nan'), 100):
            with self.assertRaises(ValueError):
                hardware.ResourceMonitor(value)

    def test_quick_ram_refresh_is_fail_closed_without_inventory(self):
        with patch.object(hardware, '_memory', return_value=(1000, 0)), \
                patch.object(hardware, '_windows_details') as cim, \
                patch.object(hardware, '_nvidia_sample') as gpu:
            self.assertEqual(hardware.available_ram_bytes(), 0)
            cim.assert_not_called()
            gpu.assert_not_called()
        for value in ((None, 500), (100, 200), (True, 1), (100, None)):
            with patch.object(hardware, '_memory', return_value=value):
                self.assertIsNone(hardware.available_ram_bytes())

    def test_resource_validator_rejects_invalid_numbers_counts_and_sources(self):
        valid = hardware.ResourceMonitor().stop()
        hardware.validate_resources(valid)
        for key, value in [('sample_count', 1), ('mean_system_cpu_percent', 101),
                           ('peak_system_used_ram_bytes', -1),
                           ('peak_nvidia_memory_used_bytes', float('nan')),
                           ('min_available_ram_bytes', True), ('sources', {}),
                           ('power', 12)]:
            invalid = copy.deepcopy(valid)
            invalid[key] = value
            with self.assertRaises(ValueError, msg=key):
                hardware.validate_resources(invalid)
        fixture = copy.deepcopy(valid)
        fixture.update(source='synthetic-fixture', clock='synthetic-fixture',
                       sources={'collector': 'synthetic-fixture'})
        hardware.validate_resources(fixture, fixture=True)
        with self.assertRaises(ValueError):
            hardware.validate_resources(fixture)
        with self.assertRaises(ValueError):
            hardware.validate_resources(valid, fixture=True)
        self.assertIsNone(hardware.validate_resources(None))

    def test_resource_validator_ram_cpu_gpu_sample_bounds(self):
        valid = hardware.ResourceMonitor().stop()
        sample = {'elapsed_seconds': 0.1, 'total_ram_bytes': 1000,
                  'available_ram_bytes': 400, 'system_used_ram_bytes': 600,
                  'system_cpu_percent': 20, 'nvidia_gpus': [
                      {'dedicated_memory_bytes': 100, 'memory_used_bytes': 40,
                       'utilization_percent': 20, 'source': 'nvidia-smi'}]}
        valid.update(sample_count=1, samples=[sample])
        hardware.validate_resources(valid)
        for key, value in [('available_ram_bytes', 1001),
                           ('system_used_ram_bytes', 500),
                           ('elapsed_seconds', float('inf')),
                           ('system_cpu_percent', -1)]:
            invalid = copy.deepcopy(valid)
            invalid['samples'][0][key] = value
            with self.assertRaises(ValueError, msg=key):
                hardware.validate_resources(invalid)
        for key, value in [('memory_used_bytes', 101), ('utilization_percent', 101),
                           ('source', '')]:
            invalid = copy.deepcopy(valid)
            invalid['samples'][0]['nvidia_gpus'][0][key] = value
            with self.assertRaises(ValueError, msg=key):
                hardware.validate_resources(invalid)

    def test_monitor_context_stops_on_exception_without_hardware_reads(self):
        monitor = hardware.ResourceMonitor(0.1)
        with patch.object(monitor, '_sample'):
            with self.assertRaisesRegex(RuntimeError, 'fixture failure'):
                with monitor:
                    raise RuntimeError('fixture failure')
        self.assertTrue(monitor._event.is_set())
        self.assertFalse(monitor._thread.is_alive())


if __name__ == '__main__':
    unittest.main()
