"""Original MIT-licensed synthetic coding fixtures; structural checks, never execution.

Passing certifies one narrow AST contract, not dynamic correctness or general coding
ability. Equivalent correct implementations can fail. Untrusted text is never echoed.
"""
import ast
import json

GRADER = 'static-ast-v1'
MAX_ANSWER = 8192
MAX_CODE = 2048
MAX_NODES = 160
MAX_DEPTH = 24

_SOLUTIONS = {
    'feature_clamp': 'def clamp(value, low, high):\n    return low if value < low else high if value > high else value\n',
    'bugfix_adult': 'def is_adult(age):\n    return age >= 18\n',
    'unit_tests_adult': 'def test_is_adult():\n    assert is_adult(17) is False\n    assert is_adult(18) is True\n    assert is_adult(19) is True\n',
    'refactor_squares': 'def squares(values):\n    return [value * value for value in values]\n',
}

WORKLOADS = {
    'feature_clamp': {
        'category': 'feature_implementation',
        'description': 'Implement a bounded-value helper using a specified conditional expression.',
        'prompt': 'Synthetic Python feature task. Implement clamp(value, low, high), assuming low <= high. Return low if value < low, otherwise high if value > high, otherwise value. Use one function with one return containing nested conditional expressions in precisely that order; no annotations, docstrings, calls, imports or other statements. Return only JSON with one key code containing the Python source.',
        'expected': 'One clamp function; exact nested conditional AST.',
        'staticcriterion': 'AST equals the specified conditional-expression structure; no dynamic execution.'},
    'bugfix_adult': {
        'category': 'bug_fix',
        'description': 'Repair an inclusive age boundary in an original two-line fixture.',
        'prompt': 'Synthetic Python bug fix. Existing fixture:\ndef is_adult(age):\n    return age > 18\nThe specification includes age 18. Change only the comparison operator. Keep one unannotated function, one return, no docstring, imports or other statements. Return only JSON with one key code containing the corrected source.',
        'expected': 'is_adult(age) returns age >= 18.',
        'staticcriterion': 'AST equals one function returning the specified >= comparison.'},
    'unit_tests_adult': {
        'category': 'unit_test_generation',
        'description': 'Generate three explicit boundary assertions for a provided helper.',
        'prompt': 'Synthetic Python test-generation task. Given is_adult(age), whose specification is age >= 18, write only def test_is_adult(): with these three ordered assertions: is_adult(17) is False; is_adult(18) is True; is_adult(19) is True. No imports, annotations, docstring, helper definitions or other statements. Return only JSON with one key code containing the test source. Generated tests will be structurally inspected, not executed.',
        'expected': 'Three exact boundary assertions at 17, 18, 19 in that order.',
        'staticcriterion': 'AST equals the specified three-assertion test function; test behavior is not executed.'},
    'code_review_boundary': {
        'category': 'code_review',
        'description': 'Identify the faulty line and precise inclusive-boundary repair.',
        'prompt': 'Review this original synthetic Python fixture. Line 1: def is_adult(age): Line 2: return age > 18. Specification: age 18 must be accepted. Return only JSON with exactly defect_line (integer 2) and fix (string containing the corrected expression, using variable age).',
        'expected': {'defect_line': 2, 'fix': 'age >= 18'},
        'staticcriterion': 'Exact typed JSON line number and correction; no generated source execution.'},
    'refactor_squares': {
        'category': 'refactor',
        'description': 'Replace an original accumulator loop with one list comprehension.',
        'prompt': 'Refactor this synthetic Python fixture:\ndef squares(values):\n    result = []\n    for value in values:\n        result.append(value * value)\n    return result\nReturn a single unannotated squares(values) function containing one return with one list comprehension [value * value for value in values]. No filters, calls, docstrings, imports or other statements. Return only JSON with one key code containing source.',
        'expected': 'One return of the exact specified list-comprehension AST.',
        'staticcriterion': 'AST equals the specified single-comprehension function; equivalence is not dynamically tested.'},
    'review_release_gate': {
        'category': 'workflow_gate_review',
        'description': 'Find a release decision that accepts one successful gate instead of requiring both.',
        'prompt': 'Review this original synthetic workflow. Line 1: tests_passed = True. Line 2: build_passed = False. Line 3: approved = tests_passed or build_passed. Policy: a release is approved only when tests and the build both pass. Return only JSON with exactly defect_line (integer 3) and fix (string tests_passed and build_passed).',
        'expected': {'defect_line': 3, 'fix': 'tests_passed and build_passed'},
        'staticcriterion': 'Exact typed JSON identifies the permissive gate and its conjunction repair.'},
    'review_draft_persistence': {
        'category': 'persistence_review',
        'description': 'Recognize that saving only during a graceful close loses work on process death.',
        'prompt': 'Review this original synthetic draft flow. Line 1: draft changes remain only in memory. Line 2: on graceful close, write the draft to storage. Requirement: accepted edits must survive force-stop or process death. Return only JSON with exactly defect_line (integer 2) and fix (string checkpoint after each accepted edit).',
        'expected': {'defect_line': 2, 'fix': 'checkpoint after each accepted edit'},
        'staticcriterion': 'Exact typed JSON identifies close-only persistence and the required checkpoint rule.'},
    'review_import_collision': {
        'category': 'data_integrity_review',
        'description': 'Detect an import path that silently replaces an existing record with the same identity.',
        'prompt': 'Review this original synthetic import flow. Line 1: keep every saved record whose id differs from the imported id. Line 2: append the imported record. Requirement: importing must never replace a saved record. Return only JSON with exactly defect_line (integer 1) and fix (string mint a fresh id, then append without filtering).',
        'expected': {'defect_line': 1, 'fix': 'mint a fresh id, then append without filtering'},
        'staticcriterion': 'Exact typed JSON identifies destructive collision handling and the append-only repair.'},
    'review_resource_cleanup': {
        'category': 'resource_lifecycle_review',
        'description': 'Find a completed database operation that commits but leaves its connection open.',
        'prompt': 'Review this original synthetic database flow. Line 1: connection = open_database(path). Line 2: with connection: run_operation(connection). Line 3: return success. The context commits or rolls back but does not close the connection; completed operations must release the file handle. Return only JSON with exactly defect_line (integer 3) and fix (string close the connection before returning).',
        'expected': {'defect_line': 3, 'fix': 'close the connection before returning'},
        'staticcriterion': 'Exact typed JSON identifies the leaked lifecycle and the required close.'},
}

REVIEW_WORKLOADS = {
    key: record['expected'] for key, record in WORKLOADS.items()
    if isinstance(record['expected'], dict)
}


def _bounded_nesting(text, limit):
    """Reject excessive delimiters outside quoted JSON/Python strings before parsing."""
    depth = 0
    quote = None
    escaped = False
    for char in text:
        if quote:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
        elif char in ('"', "'"):
            quote = char
        elif char in '([{':
            depth += 1
            if depth > limit:
                return False
        elif char in ')]}':
            depth -= 1
    return True


def _json_object(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate key')
            result[key] = value
        return result
    def reject_constant(_value):
        raise ValueError('non-finite number')
    return json.loads(text, object_pairs_hook=pairs, parse_constant=reject_constant)


def grade(workload, answer):
    """Bounded, deterministic inspection returning only a safe fixed detail enum."""
    def result(passed, details):
        return {'passed': passed, 'grader': GRADER, 'details': details}
    if workload not in WORKLOADS:
        return result(False, 'unknown_workload')
    if not isinstance(answer, str) or len(answer) > MAX_ANSWER:
        return result(False, 'answer_limit')
    if not _bounded_nesting(answer, MAX_DEPTH):
        return result(False, 'nesting_limit')
    try:
        data = _json_object(answer)
    except (ValueError, TypeError, RecursionError):
        return result(False, 'invalid_json')
    if not isinstance(data, dict):
        return result(False, 'invalid_contract')
    if workload in REVIEW_WORKLOADS:
        expected = REVIEW_WORKLOADS[workload]
        correct = (set(data) == {'defect_line', 'fix'} and
                   type(data['defect_line']) is int and
                   type(data['fix']) is str and data == expected)
        return result(correct, 'contract_match' if correct else 'contract_mismatch')
    if set(data) != {'code'} or type(data['code']) is not str:
        return result(False, 'invalid_contract')
    code = data['code']
    if len(code) > MAX_CODE or code.count('\n') > 60:
        return result(False, 'code_limit')
    if not _bounded_nesting(code, MAX_DEPTH):
        return result(False, 'nesting_limit')
    try:
        tree = ast.parse(code, mode='exec')
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return result(False, 'invalid_syntax')
    # An explicit finite allowlist excludes imports, attributes, loops, decorators,
    # assignments, arbitrary calls, f-strings and all other executable constructs.
    allowed = {ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.Return,
               ast.IfExp, ast.Compare, ast.Name, ast.Load, ast.Store, ast.Constant,
               ast.Lt, ast.Gt, ast.GtE, ast.Assert, ast.Is, ast.Call,
               ast.ListComp, ast.comprehension, ast.BinOp, ast.Mult}
    pending = [(tree, 0)]
    count = 0
    while pending:
        node, depth = pending.pop()
        count += 1
        if count > MAX_NODES or depth > MAX_DEPTH:
            return result(False, 'ast_limit')
        if type(node) not in allowed:
            return result(False, 'unsafe_ast')
        if isinstance(node, ast.Name) and '__' in node.id:
            return result(False, 'unsafe_ast')
        if isinstance(node, ast.FunctionDef) and (node.decorator_list or node.returns):
            return result(False, 'unsafe_ast')
        if isinstance(node, ast.Call) and not (workload == 'unit_tests_adult' and
                isinstance(node.func, ast.Name) and node.func.id == 'is_adult' and
                len(node.args) == 1 and not node.keywords):
            return result(False, 'unsafe_ast')
        pending.extend((child, depth + 1) for child in ast.iter_child_nodes(node))
    expected = ast.parse(_SOLUTIONS[workload], mode='exec')
    correct = ast.dump(tree, include_attributes=False) == ast.dump(expected, include_attributes=False)
    return result(correct, 'contract_match' if correct else 'contract_mismatch')


# Trusted original examples are fixture data only; no example is executed.
TRUSTED_SAMPLES = {
    key: {'pass': json.dumps({'code': value}),
          'fail': json.dumps({'code': value.replace('return ', 'return 0 # ', 1)})
          if key != 'unit_tests_adult' else json.dumps({'code': value.replace('(18)', '(20)')}),
          'unsafe': json.dumps({'code': 'import os\n'})}
    for key, value in _SOLUTIONS.items()
}
TRUSTED_SAMPLES['code_review_boundary'] = {
    'pass': '{"defect_line":2,"fix":"age >= 18"}',
    'fail': '{"defect_line":2,"fix":"age > 18"}',
    'unsafe': '{"defect_line":true,"fix":"age >= 18"}',
}
for key, expected in REVIEW_WORKLOADS.items():
    if key == 'code_review_boundary':
        continue
    TRUSTED_SAMPLES[key] = {
        'pass': json.dumps(expected),
        'fail': json.dumps({'defect_line': expected['defect_line'], 'fix': 'unsafe shortcut'}),
        'unsafe': json.dumps({'defect_line': True, 'fix': expected['fix']}),
    }
