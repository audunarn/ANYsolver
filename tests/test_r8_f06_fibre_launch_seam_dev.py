"""Focused supervisor launch-seam control: temp_root construction, refusal, cleanup (mocked)."""
import json
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import r8_f06_fibre_log_domain_dev as dev
from scripts.r8_f06_fibre_log_domain_dev import run

TEMP_ROOT = dev.ROOT / '.development' / 'ge-mi-temp'


class _FakeProcess:
    def __init__(self, hang=False, children=()):
        self.pid = 4242
        self.hang = hang
        self._children = list(children)
        self.killed = 0
        self.affinity = None
        self.rss = 1024

    def poll(self):
        return None if self.hang else 0

    def wait(self):
        return 0

    def cpu_affinity(self, cpus):
        self.affinity = cpus

    def children(self, recursive=True):
        return list(self._children)

    def memory_info(self):
        return types.SimpleNamespace(rss=self.rss)

    def kill(self):
        self.killed += 1


def _mock_launch(monkeypatch, process):
    def Popen(cmd, **kwargs):
        return process

    monkeypatch.setattr(dev, 'subprocess', types.SimpleNamespace(Popen=Popen))
    fake = types.ModuleType('psutil')
    fake.NoSuchProcess = type('NoSuchProcess', (Exception,), {})

    def Process(pid=None):
        assert pid == process.pid
        return process

    fake.Process = Process
    monkeypatch.setitem(sys.modules, 'psutil', fake)


def _doc(tmp_path, name, cap):
    doc = tmp_path / name
    doc.mkdir()
    (doc / 'AUTHORITY.json').write_text(json.dumps(
        dict(status='AUTHORIZED', budget_s=30., reserve_s=5., process_cap_s=cap)))
    return doc


def test_default_temp_construction_and_receipt(tmp_path, monkeypatch):
    process = _FakeProcess()
    _mock_launch(monkeypatch, process)
    doc = _doc(tmp_path, 'doc-default', 10.)
    code = run('stub', doc=doc, entry=Path(__file__), bind=lambda: {},
               authority_file='AUTHORITY.json')
    out = doc / 'attempt-stub1'
    receipt = json.loads((out / 'receipt.json').read_text())
    temp = out / 'temp'
    assert code == 0 and receipt['status'] == 'PASS' and receipt['failure'] is None
    assert receipt['command'] == [sys.executable, str(Path(__file__).resolve()),
                                  '--child', '--out', str(out), '--stage', 'stub']
    assert receipt['environment']['TEMP'] == receipt['environment']['TMP'] == str(temp)
    assert receipt['temp_root'] is None and receipt['temp'] == str(temp)
    assert temp.is_dir() and process.affinity == [0]
    ledger = json.loads((doc / 'ledger.json').read_text())
    assert ledger['attempts'][-1] == dict(stage='stub', path='attempt-stub1',
                                          status='PASS', wall_s=receipt['wall_s'])


def test_selected_temp_root_scratch_and_receipt(tmp_path, monkeypatch):
    process = _FakeProcess()
    _mock_launch(monkeypatch, process)
    doc = _doc(tmp_path, 'doc-selected', 10.)
    code = run('stub-selected', doc=doc, entry=Path(__file__), bind=lambda: {},
               authority_file='AUTHORITY.json', temp_root=TEMP_ROOT)
    out = doc / 'attempt-stub-selected1'
    receipt = json.loads((out / 'receipt.json').read_text())
    scratch = Path(receipt['environment']['TEMP'])
    assert code == 0 and receipt['status'] == 'PASS'
    assert receipt['temp_root'] == str(TEMP_ROOT.resolve())
    assert receipt['temp'] == receipt['environment']['TEMP'] == receipt['environment']['TMP']
    assert scratch.is_dir() and scratch.parent == TEMP_ROOT.resolve()
    assert scratch.name.startswith(out.name + '-tmp')
    assert len(str(scratch)) < len(str(out / 'temp'))
    assert not (out / 'temp').exists()


def test_temp_root_refusal(tmp_path, monkeypatch):
    process = _FakeProcess()
    _mock_launch(monkeypatch, process)
    doc = _doc(tmp_path, 'doc-refuse', 10.)
    common = dict(doc=doc, entry=Path(__file__), bind=lambda: {},
                  authority_file='AUTHORITY.json')
    with pytest.raises(ValueError, match='absolute'):
        run('refuse-relative', temp_root=Path('.development/ge-mi-temp'), **common)
    with pytest.raises(ValueError, match='escapes'):
        run('refuse-escape', temp_root=dev.ROOT.parent / 'ge-mi-escape-probe', **common)
    with pytest.raises(ValueError, match='not a directory'):
        run('refuse-file', temp_root=Path(__file__), **common)
    probe = TEMP_ROOT / 'refusal-unsafe-probe-v1'
    probe.mkdir(parents=True, exist_ok=True)
    (probe / 'attempt-refuse-unsafe1-tmp1').write_text('unsafe')
    with pytest.raises(ValueError, match='unsafe scratch allocation'):
        run('refuse-unsafe', temp_root=probe, **common)
    assert not (doc / 'ledger.json').exists()


def test_timeout_process_tree_cleanup(tmp_path, monkeypatch):
    child = _FakeProcess()
    process = _FakeProcess(hang=True, children=[child])
    _mock_launch(monkeypatch, process)
    doc = _doc(tmp_path, 'doc-timeout', 1.)
    code = run('stub', doc=doc, entry=Path(__file__), bind=lambda: {},
               authority_file='AUTHORITY.json')
    out = doc / 'attempt-stub1'
    receipt = json.loads((out / 'receipt.json').read_text())
    assert code == 1 and receipt['status'] == 'FAIL' and receipt['failure'] == 'TIMEOUT'
    assert child.killed >= 1 and process.killed >= 1
    assert receipt['peak_tree_rss_bytes'] >= 2 * 1024
    assert receipt['wall_s'] >= 1.0
    ledger = json.loads((doc / 'ledger.json').read_text())
    assert ledger['attempts'][-1]['status'] == 'FAIL'
    assert ledger['used_s'] == receipt['cumulative_wall_s']
