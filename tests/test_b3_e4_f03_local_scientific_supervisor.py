from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import _b3_e4_f03_local_scientific_supervisor as supervisor


class FakePsutilProcess:
    def __init__(self, pid, rss, children=()):
        self.pid = pid
        self._rss = rss
        self._children = list(children)
        self.alive = True
        self.killed = 0

    def children(self, recursive=True):
        assert recursive is True
        result = []
        pending = list(self._children)
        while pending:
            child = pending.pop(0)
            result.append(child)
            pending.extend(child._children)
        return result

    def memory_info(self):
        return SimpleNamespace(rss=self._rss)

    def is_running(self):
        return self.alive

    def status(self):
        return "running" if self.alive else "stopped"

    def kill(self):
        self.killed += 1
        self.alive = False


class InterruptingProcess(FakePsutilProcess):
    def memory_info(self):
        raise KeyboardInterrupt()


class DeniedChildrenProcess(FakePsutilProcess):
    def children(self, recursive=True):
        raise supervisor.psutil.AccessDenied(self.pid)


class FakePopen:
    def __init__(self, pid=10, polls=(None, 0)):
        self.pid = pid
        self._polls = list(polls)
        self._last = None
        self.kwargs = None
        self.killed = 0

    def launch(self, *args, **kwargs):
        self.kwargs = kwargs
        return self

    def poll(self):
        if self._polls:
            self._last = self._polls.pop(0)
        return self._last

    def wait(self, timeout=None):
        assert timeout == 10.0
        return -9 if self.killed else (0 if self._last is None else self._last)

    def kill(self):
        self.killed += 1
        self._last = -9


class Clock:
    def __init__(self, values):
        self.values = iter(values)

    def __call__(self):
        return next(self.values)


def _run(tmp_path, root, fake, *, limits, clock):
    output = (tmp_path / "out").open("x")
    error = (tmp_path / "err").open("x")
    try:
        return supervisor.supervise(
            ("python", "child.py"),
            cwd=tmp_path,
            environment=supervisor.frozen_thread_environment({"A": "B"}),
            stdout=output,
            stderr=error,
            limits=limits,
            popen=fake.launch,
            process_factory=lambda pid: root,
            monotonic=clock,
            sleep=lambda seconds: None,
        )
    finally:
        output.close()
        error.close()


def test_completed_tree_accounts_root_and_descendant_rss(tmp_path, monkeypatch):
    child = FakePsutilProcess(11, 200)
    root = FakePsutilProcess(10, 300, (child,))
    fake = FakePopen(polls=(None, 0))
    monkeypatch.setattr(supervisor.psutil, "wait_procs", lambda *a, **k: ([], []))
    receipt = _run(
        tmp_path, root, fake,
        limits=supervisor.SupervisorLimits(10, 1_000),
        clock=Clock((0.0, 0.1, 0.2, 0.3)),
    )
    assert receipt.reason == "orphaned_descendants"
    assert receipt.sampled_peak_tree_rss_bytes == 500
    assert receipt.observed_pids == (10, 11)
    assert receipt.terminated_pids == (11,)
    assert child.killed == 1 and root.killed == 0
    assert all(fake.kwargs["env"][name] == "1" for name in supervisor.THREADS)


def test_rss_limit_terminates_complete_observed_tree(tmp_path, monkeypatch):
    grandchild = FakePsutilProcess(12, 400)
    child = FakePsutilProcess(11, 300, (grandchild,))
    root = FakePsutilProcess(10, 500, (child,))
    fake = FakePopen(polls=(None,))
    monkeypatch.setattr(supervisor.psutil, "wait_procs", lambda *a, **k: ([], []))
    receipt = _run(
        tmp_path, root, fake,
        limits=supervisor.SupervisorLimits(10, 1_000),
        clock=Clock((0.0, 0.1, 0.2)),
    )
    assert receipt.reason == "rss_limit"
    assert receipt.sampled_peak_tree_rss_bytes == 1_200
    assert receipt.terminated_pids == (10, 11, 12)
    assert all(process.killed == 1 for process in (root, child, grandchild))


def test_detached_observed_descendant_remains_in_rss_accounting():
    grandchild = FakePsutilProcess(12, 400)
    child = FakePsutilProcess(11, 100, (grandchild,))
    root = FakePsutilProcess(10, 100, (child,))
    tracked = {}
    assert supervisor._tree_sample(root, tracked) == 600
    root._children.clear()
    child.alive = False
    grandchild._rss = 1_200
    assert supervisor._tree_sample(root, tracked) == 1_300
    assert tuple(tracked) == (10, 11, 12)


def test_cancellation_during_live_sampling_retains_and_kills_discovered_tree(
    tmp_path, monkeypatch,
):
    grandchild = FakePsutilProcess(12, 100)
    child = InterruptingProcess(11, 100, (grandchild,))
    root = FakePsutilProcess(10, 100, (child,))
    fake = FakePopen(polls=(None,))
    monkeypatch.setattr(supervisor.psutil, "wait_procs", lambda *a, **k: ([], []))
    with pytest.raises(supervisor.SupervisionCancelled) as caught:
        _run(
            tmp_path, root, fake,
            limits=supervisor.SupervisorLimits(10, 1_000),
            clock=Clock((0.0, 0.1)),
        )
    receipt = caught.value.receipt
    assert receipt.reason == "cancelled"
    assert receipt.root_pid == 10
    assert receipt.observed_pids == (10, 11, 12)
    assert receipt.terminated_pids == (10, 11, 12)
    assert receipt.failure == "KeyboardInterrupt"
    assert fake.killed == child.killed == grandchild.killed == 1


def test_cancellation_kills_observed_descendant_after_root_exit(tmp_path, monkeypatch):
    child = InterruptingProcess(11, 100)
    root = FakePsutilProcess(10, 100, (child,))
    root.alive = False
    fake = FakePopen(polls=(0,))
    monkeypatch.setattr(supervisor.psutil, "wait_procs", lambda *a, **k: ([], []))
    with pytest.raises(supervisor.SupervisionCancelled) as caught:
        _run(
            tmp_path, root, fake,
            limits=supervisor.SupervisorLimits(10, 1_000),
            clock=Clock((0.0, 0.1)),
        )
    assert caught.value.receipt.terminated_pids == (11,)
    assert child.killed == 1


def test_second_interrupt_during_cleanup_retries_owned_tree(tmp_path, monkeypatch):
    child = InterruptingProcess(11, 100)
    root = FakePsutilProcess(10, 100, (child,))
    fake = FakePopen(polls=(None,))
    monkeypatch.setattr(supervisor.psutil, "wait_procs", lambda *a, **k: ([], []))
    original = supervisor._terminate
    calls = 0

    def interrupt_once(processes, *, record=None):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise KeyboardInterrupt()
        return original(processes, record=record)

    monkeypatch.setattr(supervisor, "_terminate", interrupt_once)
    with pytest.raises(supervisor.SupervisionCancelled) as caught:
        _run(
            tmp_path, root, fake,
            limits=supervisor.SupervisorLimits(10, 1_000),
            clock=Clock((0.0, 0.1)),
        )
    assert calls >= 2
    assert caught.value.receipt.terminated_pids == (10, 11)
    assert caught.value.receipt.failure == "KeyboardInterrupt; cleanup KeyboardInterrupt"
    assert child.killed == fake.killed == 1


def test_second_interrupt_after_descendant_kills_retains_pid_accounting(
    tmp_path, monkeypatch,
):
    child = InterruptingProcess(11, 100)
    root = FakePsutilProcess(10, 100, (child,))
    fake = FakePopen(polls=(None,))
    waits = 0

    def interrupt_wait_once(*args, **kwargs):
        nonlocal waits
        waits += 1
        if waits == 1:
            raise KeyboardInterrupt()
        return ([], [])

    monkeypatch.setattr(supervisor.psutil, "wait_procs", interrupt_wait_once)
    with pytest.raises(supervisor.SupervisionCancelled) as caught:
        _run(
            tmp_path, root, fake,
            limits=supervisor.SupervisorLimits(10, 1_000),
            clock=Clock((0.0, 0.1)),
        )
    assert caught.value.receipt.terminated_pids == (10, 11)
    assert waits == 2
    assert child.killed == fake.killed == 1


def test_cancellation_before_process_factory_returns_reacquires_tree(tmp_path, monkeypatch):
    child = FakePsutilProcess(11, 100)
    root = FakePsutilProcess(10, 100, (child,))
    fake = FakePopen(polls=(None,))
    monkeypatch.setattr(supervisor.psutil, "wait_procs", lambda *a, **k: ([], []))
    calls = 0

    def factory(pid):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise KeyboardInterrupt()
        return root

    output = (tmp_path / "out").open("x")
    error = (tmp_path / "err").open("x")
    try:
        with pytest.raises(supervisor.SupervisionCancelled) as caught:
            supervisor.supervise(
                ("python", "child.py"), cwd=tmp_path, environment={},
                stdout=output, stderr=error,
                popen=fake.launch, process_factory=factory,
                monotonic=Clock((0.0, 0.1)), sleep=lambda seconds: None,
            )
    finally:
        output.close(); error.close()
    assert calls == 2
    assert caught.value.receipt.observed_pids == (10, 11)
    assert caught.value.receipt.terminated_pids == (10, 11)
    assert fake.killed == child.killed == 1


def test_direct_root_kill_is_counted_when_psutil_root_unavailable(tmp_path):
    fake = FakePopen(polls=(None,))
    calls = 0

    def factory(pid):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise KeyboardInterrupt()
        raise supervisor.psutil.NoSuchProcess(pid)

    output = (tmp_path / "out").open("x")
    error = (tmp_path / "err").open("x")
    try:
        with pytest.raises(supervisor.SupervisionCancelled) as caught:
            supervisor.supervise(
                ("python", "child.py"), cwd=tmp_path, environment={},
                stdout=output, stderr=error,
                popen=fake.launch, process_factory=factory,
                monotonic=Clock((0.0, 0.1)), sleep=lambda seconds: None,
            )
    finally:
        output.close(); error.close()
    assert caught.value.receipt.root_pid == 10
    assert caught.value.receipt.terminated_pids == (10,)
    assert fake.killed == 1


def test_cleanup_discovery_denial_still_kills_and_waits_for_owned_root(tmp_path):
    root = DeniedChildrenProcess(10, 100)
    fake = FakePopen(polls=(None,))
    calls = 0

    def factory(pid):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise KeyboardInterrupt()
        return root

    output = (tmp_path / "out").open("x")
    error = (tmp_path / "err").open("x")
    try:
        with pytest.raises(supervisor.SupervisionCancelled) as caught:
            supervisor.supervise(
                ("python", "child.py"), cwd=tmp_path, environment={},
                stdout=output, stderr=error,
                popen=fake.launch, process_factory=factory,
                monotonic=Clock((0.0, 0.1)), sleep=lambda seconds: None,
            )
    finally:
        output.close(); error.close()
    assert caught.value.receipt.reason == "cancelled"
    assert caught.value.receipt.terminated_pids == (10,)
    assert "AccessDenied" in caught.value.receipt.failure
    assert fake.killed == 1


def test_exited_root_is_not_reacquired_by_reused_pid(tmp_path):
    fake = FakePopen(polls=(0,))
    calls = 0

    def factory(pid):
        nonlocal calls
        calls += 1
        raise KeyboardInterrupt()

    output = (tmp_path / "out").open("x")
    error = (tmp_path / "err").open("x")
    try:
        with pytest.raises(supervisor.SupervisionCancelled) as caught:
            supervisor.supervise(
                ("python", "child.py"), cwd=tmp_path, environment={},
                stdout=output, stderr=error,
                popen=fake.launch, process_factory=factory,
                monotonic=Clock((0.0, 0.1)), sleep=lambda seconds: None,
            )
    finally:
        output.close(); error.close()
    assert calls == 1
    assert fake.killed == 0
    assert caught.value.receipt.terminated_pids == ()


def test_poll_error_does_not_authorize_pid_reacquisition(tmp_path):
    fake = FakePopen(polls=(None,))
    factory_calls = 0

    def factory(pid):
        nonlocal factory_calls
        factory_calls += 1
        if factory_calls == 1:
            raise KeyboardInterrupt()
        raise AssertionError("replacement process must not be acquired")

    def broken_poll():
        raise OSError("ownership status unavailable")

    fake.poll = broken_poll
    output = (tmp_path / "out").open("x")
    error = (tmp_path / "err").open("x")
    try:
        with pytest.raises(supervisor.SupervisionCancelled) as caught:
            supervisor.supervise(
                ("python", "child.py"), cwd=tmp_path, environment={},
                stdout=output, stderr=error,
                popen=fake.launch, process_factory=factory,
                monotonic=Clock((0.0, 0.1)), sleep=lambda seconds: None,
            )
    finally:
        output.close(); error.close()
    assert factory_calls == 1
    assert fake.killed == 1
    assert caught.value.receipt.terminated_pids == (10,)
    assert "OSError" in caught.value.receipt.failure


def test_time_limit_terminates_tree_and_preserves_reason(tmp_path, monkeypatch):
    child = FakePsutilProcess(11, 1)
    root = FakePsutilProcess(10, 1, (child,))
    fake = FakePopen(polls=(None,))
    monkeypatch.setattr(supervisor.psutil, "wait_procs", lambda *a, **k: ([], []))
    receipt = _run(
        tmp_path, root, fake,
        limits=supervisor.SupervisorLimits(1, 1_000),
        clock=Clock((0.0, 2.0, 3.0)),
    )
    assert receipt.reason == "time_limit"
    assert receipt.terminated_pids == (10, 11)


def test_launch_failure_has_no_started_process(tmp_path):
    output = (tmp_path / "out").open("x")
    error = (tmp_path / "err").open("x")
    try:
        receipt = supervisor.supervise(
            ("python", "child.py"), cwd=tmp_path, environment={},
            stdout=output, stderr=error,
            popen=lambda *a, **k: (_ for _ in ()).throw(OSError("no launch")),
            monotonic=Clock((0.0, 0.1)), sleep=lambda seconds: None,
        )
    finally:
        output.close(); error.close()
    assert receipt.reason == "launch_failure"
    assert receipt.exit_code is None
    assert receipt.observed_pids == receipt.terminated_pids == ()
    assert receipt.failure == "OSError: no launch"


def test_programming_failure_is_not_a_receipt_failure(tmp_path):
    for failure in (AssertionError("bug"),):
        output = (tmp_path / f"out-{type(failure).__name__}").open("x")
        error = (tmp_path / f"err-{type(failure).__name__}").open("x")
        try:
            with pytest.raises(type(failure)):
                supervisor.supervise(
                    ("python", "child.py"), cwd=tmp_path, environment={},
                    stdout=output, stderr=error,
                    popen=lambda *a, _failure=failure, **k: (_ for _ in ()).throw(_failure),
                    monotonic=Clock((0.0,)), sleep=lambda seconds: None,
                )
        finally:
            output.close(); error.close()


def test_prelaunch_cancellation_has_typed_receipt_and_no_process(tmp_path):
    output = (tmp_path / "out").open("x")
    error = (tmp_path / "err").open("x")
    try:
        with pytest.raises(supervisor.SupervisionCancelled) as caught:
            supervisor.supervise(
                ("python", "child.py"), cwd=tmp_path, environment={},
                stdout=output, stderr=error,
                popen=lambda *a, **k: (_ for _ in ()).throw(KeyboardInterrupt()),
                monotonic=Clock((0.0, 0.1)), sleep=lambda seconds: None,
            )
    finally:
        output.close(); error.close()
    receipt = caught.value.receipt
    assert receipt.reason == "cancelled"
    assert receipt.root_pid is receipt.exit_code is None
    assert receipt.observed_pids == receipt.terminated_pids == ()
    assert receipt.failure == "KeyboardInterrupt"


@pytest.mark.parametrize("seconds,rss,poll", [
    (0, 1, 0.1), (1, 0, 0.1), (1, 1, 0), (float("nan"), 1, 0.1),
])
def test_invalid_limits_rejected(seconds, rss, poll):
    with pytest.raises(ValueError):
        supervisor.SupervisorLimits(seconds, rss, poll)
