import copy
import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import time
import urllib.error
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lab', ROOT / 'scripts/lab.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class Handler(BaseHTTPRequestHandler):
    mode = 'ok'
    payloads = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.send_response(200); self.end_headers()
        if self.path == '/api/tags':
            value = {'models': [{'name': 'test:fixture', 'digest': 'synthetic', 'size': 1, 'details': {'quantization_level': 'TEST'}}]}
        else:
            value = {'version': 'mock-only'}
        self.wfile.write(json.dumps(value).encode())

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.payloads.append(payload)
        if self.mode == 'http_error':
            self.send_response(503); self.end_headers(); return
        if self.mode == 'redirect':
            self.send_response(307); self.send_header('Location', 'http://example.invalid/'); self.end_headers(); return
        self.send_response(200); self.end_headers()
        if self.mode == 'timeout':
            time.sleep(1.2)
            return
        if self.mode == 'malformed':
            self.wfile.write(b'not-json\n'); return
        self.wfile.write(json.dumps({'response': '{"defect_line":2,"fix":"x >= 18"}', 'done': False}).encode() + b'\n')
        if self.mode == 'truncated': return
        final = {'done': True, 'total_duration': 2000000000, 'load_duration': 0, 'prompt_eval_count': 30, 'prompt_eval_cached_count': 10, 'prompt_eval_duration': 1000000000, 'eval_count': 10, 'eval_duration': 500000000}
        if self.mode == 'negative': final['eval_duration'] = -1
        if self.mode == 'zero': final['eval_duration'] = 0
        self.wfile.write(json.dumps(final).encode() + b'\n')


class ToolkitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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

    def test_stream_metrics_and_quality(self):
        r = lab.generate(self.endpoint, self.config, 'defect_review', 'synthetic')
        self.assertEqual(r['metrics']['generation_tokens_per_second'], 20)
        self.assertEqual(r['metrics']['prompt_tokens_per_second'], 20)
        self.assertTrue(r['quality']['passed'])
        self.assertLessEqual(r['ttft_seconds'], r['wall_seconds'])
        self.assertTrue(Handler.payloads[0]['stream'])
        self.assertEqual(Handler.payloads[0]['options']['num_predict'], 128)

    def test_zero_duration_is_null(self):
        Handler.mode = 'zero'
        self.assertIsNone(lab.generate(self.endpoint, self.config, 'defect_review', 'x')['metrics']['generation_tokens_per_second'])

    def test_stream_failures(self):
        for mode, error in (('malformed', ValueError), ('truncated', ValueError), ('negative', ValueError), ('http_error', urllib.error.HTTPError), ('redirect', ValueError)):
            with self.subTest(mode=mode):
                Handler.mode = mode
                with self.assertRaises(error): lab.generate(self.endpoint, self.config, 'defect_review', 'x')

    def test_read_timeout(self):
        Handler.mode = 'timeout'
        self.config['timeout_seconds'] = 1
        with self.assertRaises(TimeoutError): lab.generate(self.endpoint, self.config, 'defect_review', 'x')

    def test_concurrency_and_metadata(self):
        self.config['concurrency'] = [1, 2, 4]
        self.config['workloads'] = ['defect_review']
        r = lab.run(self.config, self.endpoint)
        self.assertEqual([len(b['requests']) for b in r['batches']], [1, 2, 4])
        self.assertEqual(len(Handler.payloads), 7)
        self.assertEqual(r['model_metadata']['digest'], 'synthetic')
        self.assertTrue(lab.validate(r))

    def test_missing_model_never_generates(self):
        self.config['model'] = 'not-installed'
        with self.assertRaises(ValueError): lab.run(self.config, self.endpoint)
        self.assertEqual(Handler.payloads, [])

    def test_failures_retained(self):
        Handler.mode = 'http_error'
        r = lab.run(self.config, self.endpoint)
        self.assertTrue(all(q['status'] == 'error' for b in r['batches'] for q in b['requests']))
        self.assertTrue(all(b['aggregate_output_tokens_per_second'] == 0 for b in r['batches']))

    def test_fixture_never_contacts_server(self):
        r = lab.run(self.config, 'http://127.0.0.1:1', fixture=True)
        self.assertEqual(r['mode'], 'fixture')
        self.assertIn('NOT HARDWARE PERFORMANCE', lab.report(r))

    def test_result_validation(self):
        r = lab.run(self.config, self.endpoint, fixture=True)
        for mutation in ('negative', 'missing_batch', 'nan', 'bool', 'ttft', 'rate', 'aggregate'):
            v = copy.deepcopy(r)
            if mutation == 'negative': v['batches'][0]['wall_seconds'] = -1
            if mutation == 'missing_batch': v['batches'].pop()
            if mutation == 'nan': v['batches'][0]['aggregate_output_tokens_per_second'] = float('nan')
            if mutation == 'bool': v['batches'][0]['requests'][0]['metrics']['eval_count'] = True
            if mutation == 'ttft': v['batches'][0]['requests'][0]['ttft_seconds'] = 99
            if mutation == 'rate': v['batches'][0]['requests'][0]['metrics']['generation_tokens_per_second'] = 999
            if mutation == 'aggregate': v['batches'][0]['aggregate_output_tokens_per_second'] = 999
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): lab.validate(v)

    def test_config_bounds(self):
        for key, value in [('num_predict', 513), ('context_length', 9000), ('repeats', 4), ('timeout_seconds', 121), ('concurrency', [8]), ('seed', True), ('workloads', ['unknown'])]:
            v = copy.deepcopy(self.config); v[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): lab.config_check(v)

    def test_endpoint_privacy(self):
        for value in ('https://localhost', 'http://192.0.2.1', 'http://user:pass@localhost', 'http://localhost/path', 'http://localhost?secret=x'):
            with self.subTest(value=value), self.assertRaises(ValueError): lab.endpoint_check(value)

    def test_graders_never_execute(self):
        self.assertFalse(lab.grade('defect_review', '__import__("os").system("echo unsafe")')['passed'])
        self.assertFalse(lab.grade('defect_review', '{"defect_line":2,"fix":"wrong"}')['passed'])
        self.assertTrue(lab.grade('structured_qa', '{"valid_count":1,"invalid_ids":["B","C"]}')['passed'])

    def test_grading_rejects_boolean_and_float_integer_substitutes(self):
        for value in ('true', '1.0'):
            self.assertFalse(lab.grade('structured_qa', '{"valid_count":' + value + ',"invalid_ids":["B","C"]}')['passed'])
        self.assertFalse(lab.grade('defect_review', '{"defect_line":2.0,"fix":"x >= 18"}')['passed'])

    def test_unhashable_config_values_are_rejected_cleanly(self):
        for key, value in (('concurrency', [[1]]), ('concurrency', [{}]), ('workloads', [['defect_review']]), ('workloads', [{}])):
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                lab.config_check(config)

    def test_required_result_provenance(self):
        result = lab.run(self.config, self.endpoint, fixture=True)
        for key in ('created_utc', 'model_metadata', 'unmeasured', 'config', 'batches'):
            changed = copy.deepcopy(result)
            del changed[key]
            with self.subTest(key=key), self.assertRaises(ValueError): lab.validate(changed)
        for timestamp in ('not-a-date', '2026-10-20T12:00:00', '2026-10-20T12:00:00+01:00'):
            changed = copy.deepcopy(result); changed['created_utc'] = timestamp
            with self.subTest(timestamp=timestamp), self.assertRaises(ValueError): lab.validate(changed)
        changed = copy.deepcopy(result); changed['schema_version'] = True
        with self.assertRaises(ValueError): lab.validate(changed)
        changed = copy.deepcopy(result); changed['unmeasured'] = []
        with self.assertRaises(ValueError): lab.validate(changed)

    def test_fixture_cannot_be_relabelled_as_measured(self):
        result = lab.run(self.config, self.endpoint, fixture=True)
        result['mode'] = 'measured'
        with self.assertRaises(ValueError): lab.validate(result)
        result['model_metadata'] = {'name': self.config['model'], 'digest': 'synthetic', 'size': 1, 'details': dict.fromkeys(('format', 'family', 'parameter_size', 'quantization_level'))}
        result['ollama_version'] = 'mock-only'
        with self.assertRaises(ValueError): lab.validate(result)

    def test_measured_metadata_is_mandatory(self):
        result = lab.run(self.config, self.endpoint)
        for mutation in ('version', 'digest', 'name', 'size', 'details'):
            changed = copy.deepcopy(result)
            if mutation == 'version': del changed['ollama_version']
            if mutation == 'digest': changed['model_metadata']['digest'] = ''
            if mutation == 'name': changed['model_metadata']['name'] = 'other-model'
            if mutation == 'size': changed['model_metadata']['size'] = True
            if mutation == 'details': del changed['model_metadata']['details']['quantization_level']
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): lab.validate(changed)

    def test_malformed_result_containers_are_rejected_cleanly(self):
        result = lab.run(self.config, self.endpoint, fixture=True)
        for mutation in ('batch', 'request', 'requests', 'metrics', 'quality', 'concurrency', 'repeat'):
            changed = copy.deepcopy(result)
            batch = changed['batches'][0]
            if mutation == 'batch': changed['batches'][0] = None
            if mutation == 'request': batch['requests'][0] = []
            if mutation == 'requests': batch['requests'] = {}
            if mutation == 'metrics': batch['requests'][0]['metrics'] = []
            if mutation == 'quality': batch['requests'][0]['quality'] = None
            if mutation == 'concurrency': batch['concurrency'] = True
            if mutation == 'repeat': batch['repeat'] = []
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): lab.validate(changed)

    def test_shipped_v1_fixture_remains_valid(self):
        self.assertTrue(lab.validate(lab.read_json(ROOT / 'benchmarks/results/fixture-example.json')))


if __name__ == '__main__': unittest.main()
