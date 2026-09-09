import ast
from pathlib import Path
import pytest
from docs.reference_cases.ge_beam3_call_observer import Observer
from docs.reference_cases import ge_beam3_n32_replay_profile as worker


def test_nested_exact_result_count_and_exclusive_time():
    ticks = iter((0., 1., 3., 6.))
    o = Observer(lambda: next(ticks), lambda: 0.)
    marker = object(); calls = []
    child = o.wrap('child', lambda value: (calls.append(value), value)[1])
    parent = o.wrap('parent', lambda value: child(value))
    assert parent(marker) is marker and calls == [marker]
    rows = {r['function']: r for r in o.summary()}
    assert rows['parent']['calls'] == rows['child']['calls'] == 1
    assert rows['parent']['wall_seconds'] == 6.
    assert rows['parent']['self_wall_seconds'] == 4.
    assert rows['child']['wall_seconds'] == rows['child']['self_wall_seconds'] == 2.


@pytest.mark.parametrize('error', [ValueError('sentinel'), KeyboardInterrupt('sentinel')])
def test_exact_exception_preserved_and_stack_unwound(error):
    o = Observer(); calls = []
    def fail():
        calls.append(1)
        with pytest.raises(ValueError, match='still active'):
            o.summary()
        raise error
    with pytest.raises(type(error)) as caught:
        o.wrap('outer', o.wrap('inner', fail))()
    assert caught.value is error and calls == [1] and not o.stack
    assert all(r['calls'] == r['failures'] == 1 for r in o.summary())


def test_phase_separation_and_original_metadata():
    o = Observer()
    def original(*args, **kwargs): return args, kwargs
    wrapped = o.wrap('same', original)
    assert wrapped.__wrapped__ is original
    assert wrapped(1, key=2) == ((1,), dict(key=2))
    o.phase = 'restore'; wrapped()
    assert len(o.summary()) == 2 and {r['calls'] for r in o.summary()} == {1}


def test_worker_has_no_solve_or_timer_reset_and_immutable_input_binding():
    tree = ast.parse(Path(worker.__file__).read_text())
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        and n.func.attr == 'solve' for n in ast.walk(tree))
    assert not any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Attribute)
        and t.attr in ('started', 'targets', 'max_iterations', 'max_backtracks')
        for t in n.targets) for n in ast.walk(tree))
    assert worker.CHECKPOINT == '6d6d4790cff22761f2c04f0fcc9172630eebbf49f386f4b540047984e223b226'
