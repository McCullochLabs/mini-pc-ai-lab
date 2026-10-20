"""Static grading regression and rejection tests; generated snippets are never run."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('coding', ROOT / 'scripts/coding.py')
coding = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coding)


class CodingTests(unittest.TestCase):
    def test_all_five_categories_have_complete_contracts(self):
        self.assertEqual(len(coding.WORKLOADS), 5)
        self.assertEqual(len({x['category'] for x in coding.WORKLOADS.values()}), 5)
        for record in coding.WORKLOADS.values():
            for key in ('prompt', 'category', 'description', 'expected', 'staticcriterion'):
                self.assertTrue(record[key])

    def test_trusted_samples(self):
        for workload, samples in coding.TRUSTED_SAMPLES.items():
            for kind, answer in samples.items():
                with self.subTest(workload=workload, kind=kind):
                    self.assertEqual(coding.grade(workload, answer)['passed'], kind == 'pass')

    def test_dangerous_python_rejected_without_execution(self):
        snippets = [
            'import os', 'from os import system',
            '__import__("os").system("echo forbidden")',
            'while True:\n    pass',
            'def clamp(value, low, high):\n    return eval(value)',
            '@dangerous()\ndef clamp(value, low, high):\n    return value',
            'def clamp(value, low, high):\n    return value.__class__',
            'def clamp(value, low, high):\n    return "untrusted private text"',
        ]
        for source in snippets:
            with self.subTest(source=source):
                result = coding.grade('feature_clamp', json.dumps({'code': source}))
                self.assertFalse(result['passed'])
                self.assertNotIn(source, json.dumps(result))

    def test_tests_allow_only_required_helper_call(self):
        source = 'def test_is_adult():\n    assert print(18) is True'
        self.assertEqual(coding.grade('unit_tests_adult', json.dumps({'code': source}))['details'], 'unsafe_ast')

    def test_oversized_and_deep_answers_rejected(self):
        self.assertEqual(coding.grade('bugfix_adult', 'x' * 8193)['details'], 'answer_limit')
        self.assertEqual(coding.grade('bugfix_adult', '[' * 30 + '0' + ']' * 30)['details'], 'nesting_limit')
        deep = 'def is_adult(age):\n    return ' + '(' * 30 + 'age' + ')' * 30
        self.assertEqual(coding.grade('bugfix_adult', json.dumps({'code': deep}))['details'], 'nesting_limit')
        huge = '\n'.join('x' for _ in range(80))
        self.assertEqual(coding.grade('bugfix_adult', json.dumps({'code': huge}))['details'], 'code_limit')
        complex_source = 'def clamp(value, low, high):\n    return ' + ' * '.join(['value'] * 80)
        self.assertEqual(coding.grade('feature_clamp', json.dumps({'code': complex_source}))['details'], 'ast_limit')

    def test_exact_types_keys_and_invalid_json(self):
        answers = [None, '{}', '[]', 'null', 'not json', '{"code":"x","code":"y"}',
                   '{"code":3}', '{"code":"x","extra":1}', '{"code":NaN}']
        for answer in answers:
            self.assertFalse(coding.grade('bugfix_adult', answer)['passed'])
        self.assertFalse(coding.grade('code_review_boundary', '{"defect_line":true,"fix":"age >= 18"}')['passed'])
        self.assertFalse(coding.grade('code_review_boundary', '{"defect_line":2.0,"fix":"age >= 18"}')['passed'])
        self.assertEqual(coding.grade('missing', '{}')['details'], 'unknown_workload')

    def test_equivalent_implementation_is_documented_strict_failure(self):
        code = 'def is_adult(age):\n    return not age < 18'
        self.assertFalse(coding.grade('bugfix_adult', json.dumps({'code': code}))['passed'])

    def test_comments_and_whitespace_do_not_change_ast(self):
        source = '# original fixture\ndef is_adult( age ):\n    return age>=18 # boundary\n'
        self.assertTrue(coding.grade('bugfix_adult', json.dumps({'code': source}))['passed'])


if __name__ == '__main__':
    unittest.main()
