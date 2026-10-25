"""Original MIT-licensed synthetic coding fixtures; structural checks, never execution.

Passing certifies one narrow AST contract, not dynamic correctness or general coding
ability. Equivalent correct implementations can fail. Untrusted text is never echoed.
"""
import ast
import json

GRADER = 'static-ast-v1'
REVIEW_GRADER = 'workflow-review-v2'
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
        'description': 'Review a release decision against a two-gate approval policy.',
        'expected': {'defect_line': 3, 'fix': 'tests_passed and build_passed'}},
    'review_draft_persistence': {
        'category': 'persistence_review',
        'description': 'Review edit acknowledgement against a durability policy.',
        'expected': {'defect_line': 3, 'fix': 'store.write(draft); acknowledge()'}},
    'review_import_collision': {
        'category': 'data_integrity_review',
        'description': 'Review a record merge against append-only identity rules.',
        'expected': {'defect_line': 2, 'fix': 'incoming = {**incoming, "id": fresh_id(records)}'}},
    'review_resource_cleanup': {
        'category': 'resource_lifecycle_review',
        'description': 'Review a database operation against handle lifetime requirements.',
        'expected': {'defect_line': 3, 'fix': 'try:\n    with connection: run_operation(connection)\nfinally:\n    connection.close()'}},
}

_REVIEW_CASES = {
    'review_release_gate': {
        'policy': 'tests_passed and build_passed are arbitrary Boolean inputs. A release may be approved exactly when both checks pass. Replace only the expression after return if needed.',
        'bug': 'def approve(tests_passed, build_passed):\n    # Release decision\n    return tests_passed or build_passed',
        'clean': 'def approve(tests_passed, build_passed):\n    # Release decision\n    return tests_passed and build_passed',
        'alternatives': ['tests_passed and build_passed', 'not (not tests_passed or not build_passed)', 'tests_passed == True and build_passed == True']},
    'review_draft_persistence': {
        'policy': 'apply_edit mutates draft in memory. store.write(draft) and store.checkpoint(draft) are two synchronous atomic durable-write APIs: both return None on success and raise on failure. acknowledge() tells the caller that an edit was accepted. Every acknowledged edit must survive process death, and a failed write must not be acknowledged. Replace one faulty line with one or more statements if needed.',
        'bug': 'def accept_edit(draft, edit, store):\n    apply_edit(draft, edit)\n    acknowledge()\n    return draft',
        'clean': 'def accept_edit(draft, edit, store):\n    apply_edit(draft, edit)\n    store.write(draft)\n    acknowledge()\n    return draft',
        'alternatives': ['store.write(draft); acknowledge()', 'store.checkpoint(draft); acknowledge()']},
    'review_import_collision': {
        'policy': 'records is a list of saved dictionaries with unique string id fields. incoming is a caller-owned dictionary with an id that may collide. fresh_id(records) returns an id different from every saved id and the incoming id. Imports must append one shallow copy with that fresh id, preserve all saved records and their order, and leave the caller-owned incoming unchanged. Replace one faulty line with one or more statements if needed; the return line stays unchanged.',
        'bug': 'def merge(records, incoming):\n    records = [r for r in records if r["id"] != incoming["id"]]\n    return records + [incoming]',
        'clean': 'def merge(records, incoming):\n    incoming = {**incoming, "id": fresh_id(records)}\n    return records + [incoming]',
        'alternatives': ['incoming = {**incoming, "id": fresh_id(records)}', 'incoming = dict(incoming, id=fresh_id(records))', 'incoming = incoming.copy(); incoming["id"] = fresh_id(records)']},
    'review_resource_cleanup': {
        'policy': 'open_database(path) returns an open connection. Its context manager commits or rolls back but never closes it. run_operation(connection) may succeed or raise. connection.close() releases the handle. closing(connection) is the already-imported contextlib.closing helper. The handle must close on both operation success and failure; transaction handling and the success return must be preserved. Replace one faulty line with one or more statements if needed.',
        'bug': 'def operate(path):\n    connection = open_database(path)\n    with connection: run_operation(connection)\n    return True',
        'clean': 'def operate(path):\n    connection = open_database(path)\n    with closing(connection):\n        with connection: run_operation(connection)\n    return True',
        'alternatives': ['try:\n    with connection: run_operation(connection)\nfinally:\n    connection.close()', 'with closing(connection):\n    with connection: run_operation(connection)']},
}

for _key, _case in _REVIEW_CASES.items():
    for _clean in (False, True):
        _id = _key + ('_clean' if _clean else '')
        _record = dict(WORKLOADS[_key])
        _record.update(
            prompt='Review this synthetic Python code against its API contract and policy. ' + _case['policy'] + '\n' +
                   '\n'.join(f'{i}: {line}' for i, line in enumerate(_case['clean' if _clean else 'bug'].splitlines(), 1)) +
                   '\nReturn only JSON with exactly defect_line and fix. If a defect exists, defect_line is the integer source line to replace and fix is the replacement Python expression or statements, without line numbers or code fences. If there is no defect, both values must be null.',
            expected={'defect_line': None, 'fix': None} if _clean else _record['expected'],
            grader=REVIEW_GRADER,
            protocol_version='workflow-review-v2',
            staticcriterion='Bounded AST inspection. Gate expressions are evaluated by a Boolean-only interpreter on all four inputs. Other repairs accept the documented equivalent API/AST forms; clean controls require null/null. No generated code executes.')
        WORKLOADS[_id] = _record

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


def _review_tree(code, mode):
    if len(code) > MAX_CODE or code.count('\n') > 60 or not _bounded_nesting(code, MAX_DEPTH):
        raise ValueError('repair limit')
    tree = ast.parse(code, mode=mode)
    pending = [(tree, 0)]
    count = 0
    while pending:
        node, depth = pending.pop()
        count += 1
        if count > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError('repair AST limit')
        pending.extend((child, depth + 1) for child in ast.iter_child_nodes(node))
    return tree


def _boolean(node, inputs):
    """Interpret only a finite Boolean expression language, never Python code."""
    if type(node) is ast.Name and node.id in inputs:
        return inputs[node.id]
    if type(node) is ast.Constant and type(node.value) is bool:
        return node.value
    if type(node) is ast.UnaryOp and type(node.op) is ast.Not:
        return not _boolean(node.operand, inputs)
    if type(node) is ast.BoolOp and type(node.op) in (ast.And, ast.Or):
        # Inspect all operands, so a forbidden AST cannot hide after a short circuit.
        values = [_boolean(value, inputs) for value in node.values]
        return all(values) if type(node.op) is ast.And else any(values)
    if type(node) is ast.IfExp:
        condition = _boolean(node.test, inputs)
        yes = _boolean(node.body, inputs)
        no = _boolean(node.orelse, inputs)
        return yes if condition else no
    if type(node) is ast.Compare:
        left = _boolean(node.left, inputs)
        comparisons = []
        for operation, expression in zip(node.ops, node.comparators):
            right = _boolean(expression, inputs)
            if type(operation) in (ast.Eq, ast.Is):
                comparisons.append(left == right)
            elif type(operation) in (ast.NotEq, ast.IsNot):
                comparisons.append(left != right)
            else:
                raise ValueError('unsupported Boolean comparison')
            left = right
        return all(comparisons)
    raise ValueError('unsupported Boolean expression')


def _workflow_review(workload, data):
    if set(data) != {'defect_line', 'fix'}:
        return False
    if workload.endswith('_clean'):
        return data['defect_line'] is None and data['fix'] is None
    expected = WORKLOADS[workload]['expected']
    if type(data['defect_line']) is not int or data['defect_line'] != expected['defect_line'] or type(data['fix']) is not str:
        return False
    if workload == 'review_release_gate':
        expression = _review_tree(data['fix'], 'eval').body
        return all(_boolean(expression, {'tests_passed': tests, 'build_passed': build}) == (tests and build)
                   for tests in (False, True) for build in (False, True))
    # These three one-line-replacement contracts deliberately recognize finite
    # equivalent statement forms, rather than claim general Python equivalence.
    # Parsing and comparing syntax never calls methods or executes a repair.
    tree = _review_tree(data['fix'], 'exec')
    actual = ast.dump(tree, include_attributes=False)
    return any(actual == ast.dump(ast.parse(form, mode='exec'), include_attributes=False)
               for form in _REVIEW_CASES[workload]['alternatives'])


def grade(workload, answer):
    """Bounded, deterministic inspection returning only a safe fixed detail enum."""
    def result(passed, details):
        return {'passed': passed, 'grader': WORKLOADS.get(workload, {}).get('grader', GRADER), 'details': details}
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
    if WORKLOADS[workload].get('grader') == REVIEW_GRADER:
        try:
            correct = _workflow_review(workload, data)
        except (SyntaxError, ValueError, TypeError, RecursionError, MemoryError):
            correct = False
        return result(correct, 'contract_match' if correct else 'contract_mismatch')
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
