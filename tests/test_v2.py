import copy
import tempfile
import time
from pathlib import Path
from unittest import mock
import unittest
from test_lab import lab, Handler, ThreadingHTTPServer, threading, ROOT


class Monitor:
    stopped = False
    def __init__(self, **kwargs): pass
    def start(self): pass
    def stop(self):
        Monitor.stopped = True
        return {'scope': 'local_system', 'sampling_interval_seconds': 0.5, 'clock': 'perf_counter', 'sample_count': 0, 'samples': [], 'peak_system_used_ram_bytes': None, 'min_available_ram_bytes': None, 'mean_system_cpu_percent': None, 'peak_nvidia_memory_used_bytes': None, 'sources': {'ram': 'mock-system-telemetry'}, 'warnings': [], 'thermals': None, 'power': None}


class V2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / '.local').mkdir(exist_ok=True)
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.endpoint = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def setUp(self):
        Handler.mode = 'ok'; Handler.payloads = []
        self.config = lab.read_json(ROOT / 'benchmarks/configurations/smoke.json')
        self.config['model'] = 'test:fixture'
        self.hardware = {'source': 'mock-inventory', 'os': 'Synthetic', 'os_release': '1', 'architecture': 'synthetic', 'cpu_model': 'mock', 'logical_cpus': 4, 'total_ram_bytes': 16 * 1024**3, 'available_ram_bytes': 12 * 1024**3, 'gpus': [], 'warnings': []}
        module = lab.sibling('hardware')
        self.patches = [mock.patch.object(module, 'collect_inventory', return_value=self.hardware), mock.patch.object(module, 'ResourceMonitor', Monitor), mock.patch.object(module, 'available_ram_bytes', return_value=12 * 1024**3, create=True)]
        for patch in self.patches: patch.start()
        self.addCleanup(lambda: [patch.stop() for patch in reversed(self.patches)])

    def test_v2_fixture_report_and_v1_compatibility(self):
        result = lab.run_v2(self.config, 'http://127.0.0.1:1', fixture=True)
        self.assertTrue(lab.validate(result))
        self.assertEqual(result['schema_version'], 2)
        self.assertIn('NOT HARDWARE PERFORMANCE', lab.report_v2(result))
        self.assertIn('unknown / not supplied', lab.report_v2(result))
        self.assertTrue(lab.validate(lab.read_json(ROOT / 'benchmarks/results/fixture-example.json')))

    def test_real_path_mock_provenance_and_atomic_checkpoints(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as directory:
            path = Path(directory) / 'result.json'
            result = lab.run_v2(self.config, self.endpoint, output=path)
            self.assertEqual(result['status'], 'completed')
            self.assertEqual(lab.read_json(path), result)
            self.assertFalse(list(Path(directory).glob('*.tmp')))
        self.assertEqual(Handler.payloads[0]['options']['num_thread'], 2)
        self.assertTrue(Monitor.stopped)
        self.assertEqual(result['resources']['sources']['ram'], 'mock-system-telemetry')
        self.assertIsNotNone(result['batches'][0]['requests'][0]['client_dispatch_delay_seconds'])

    def test_workflow_protocol_validates_mock_result(self):
        self.config['workloads'] = ['review_release_gate', 'review_release_gate_clean']
        result = lab.run_v2(self.config, self.endpoint)
        self.assertTrue(lab.validate(result))
        for batch in result['batches']:
            for request in batch['requests']:
                self.assertEqual(request['quality']['grader'], 'workflow-review-v2')
        result['batches'][0]['requests'][0]['quality']['grader'] = 'static-ast-v1'
        with self.assertRaises(ValueError):
            lab.validate(result)

    def test_ram_unknown_and_insufficient_reject_before_inference(self):
        for available in (None, 1):
            self.hardware['available_ram_bytes'] = available
            with self.subTest(available=available), self.assertRaises(ValueError): lab.run_v2(self.config, self.endpoint)
        self.assertEqual(Handler.payloads, [])

    def test_heavy_requires_explicit_flag(self):
        self.config['concurrency'] = [1, 2, 4]
        with self.assertRaises(ValueError): lab.run_v2(self.config, self.endpoint)
        self.assertEqual(Handler.payloads, [])
        self.assertEqual(lab.run_v2(self.config, self.endpoint, allow_heavy=True)['status'], 'completed')

    def test_auto_selection_uses_installed_model(self):
        self.config['model'] = 'auto'
        result = lab.run_v2(self.config, self.endpoint)
        self.assertEqual(result['config']['model'], 'test:fixture')
        self.assertTrue(all(p['model'] == 'test:fixture' for p in Handler.payloads))

    def test_warmups_are_separate(self):
        self.config.update(warmups=1, repeats=2)
        result = lab.run_v2(self.config, self.endpoint, fixture=True)
        self.assertEqual(len(result['warmups']), 2)
        self.assertEqual(len(result['batches']), 4)
        self.assertTrue(lab.validate(result))

    def test_failure_status_and_error_retention(self):
        Handler.mode = 'http_error'
        result = lab.run_v2(self.config, self.endpoint)
        self.assertEqual(result['status'], 'completed_with_errors')
        self.assertTrue(all(q['status'] == 'error' for b in result['batches'] for q in b['requests']))

    def test_budget_stops_dispatch_and_retains_completed_batch(self):
        self.config['run_budget_seconds'] = 1
        original = lab.generate
        def slow(*args):
            time.sleep(1.05)
            return original(*args)
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as directory, mock.patch.object(lab, 'generate', side_effect=slow):
            path = Path(directory) / 'partial.json'
            result = lab.run_v2(self.config, self.endpoint, output=path)
            self.assertEqual(lab.read_json(path), result)
        self.assertEqual(result['status'], 'budget_exhausted')
        self.assertEqual(len(result['batches']), 1)
        self.assertEqual(len(Handler.payloads), 1)
        self.assertTrue(Monitor.stopped)

    def test_interrupt_retains_checkpoint_and_stops_monitor(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as directory, mock.patch.object(lab, 'generate', side_effect=KeyboardInterrupt):
            path = Path(directory) / 'interrupted.json'
            result = lab.run_v2(self.config, self.endpoint, output=path)
            self.assertEqual(lab.read_json(path), result)
        self.assertEqual(result['status'], 'interrupted')
        self.assertEqual(result['batches'], [])
        self.assertTrue(Monitor.stopped)

    def test_comparison_refuses_fixtures_incomplete_and_mismatch(self):
        fixture = lab.run_v2(self.config, self.endpoint, fixture=True)
        with self.assertRaises(ValueError): lab.compare(fixture, fixture)
        left = lab.run_v2(self.config, self.endpoint)
        right = copy.deepcopy(left)
        self.assertTrue(lab.compare(left, right)['compatible'])
        for mutation in ('seed', 'version', 'digest', 'status', 'backend'):
            right = copy.deepcopy(left)
            if mutation == 'seed': right['config']['seed'] += 1
            if mutation == 'version': right['ollama_version'] = 'other'
            if mutation == 'digest': right['model_metadata']['digest'] = 'other'
            if mutation == 'status': right['status'] = 'interrupted'
            if mutation == 'backend': right['backend']['placement'] = 'different'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): lab.compare(left, right)

    def test_v2_schema_rejects_tampering(self):
        original = lab.run_v2(self.config, self.endpoint, fixture=True)
        for mutation in ('fingerprint', 'workload', 'id', 'delay', 'completion', 'nan', 'request_workload', 'backend', 'resources'):
            value = copy.deepcopy(original)
            if mutation == 'fingerprint': value['hardware_id'] = 'wrong'
            if mutation == 'workload': value['workload_digest'] = 'wrong'
            if mutation == 'id': value['run_id'] = 'not-uuid'
            if mutation == 'delay': value['batches'][0]['requests'][0]['client_dispatch_delay_seconds'] = -1
            if mutation == 'completion': value['batches'].pop()
            if mutation == 'nan': value['batches'][0]['aggregate_output_tokens_per_second'] = float('nan')
            if mutation == 'request_workload': value['batches'][0]['requests'][0]['workload'] = 'incorrect'
            if mutation == 'backend': value['backend']['placement'] = 'fabricated'
            if mutation == 'resources': value['resources']['peak_system_used_ram_bytes'] = -1
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): lab.validate(value)

    def test_memory_pressure_stops_further_dispatch(self):
        with mock.patch.object(lab.sibling('hardware'), 'available_ram_bytes', side_effect=[12 * 1024**3, 512 * 1024**2]):
            result = lab.run_v2(self.config, self.endpoint)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(len(result['batches']), 1)
        self.assertEqual(len(Handler.payloads), 1)
        self.assertTrue(any('memory pressure' in w for w in result['warnings']))

    def test_invalid_model_details_rejected_without_traceback(self):
        with mock.patch.object(lab, 'get_json', return_value={'models': [{'name': 'test', 'size': 1, 'digest': 'x', 'details': 123}]}):
            with self.assertRaises(ValueError): lab.models(self.endpoint)


if __name__ == '__main__': unittest.main()
