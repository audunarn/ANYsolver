"""Reuse the existing bounded harness with separate approved slice ledgers."""
from pathlib import Path
import importlib.util
import sys
ROOT=Path(__file__).resolve().parent
number=sys.argv.pop(1)
if number not in ('1','2','3'): raise SystemExit('slice must be 1, 2 or 3')
source=ROOT.parent/'gate-closure-20261019/harness.py'
spec=importlib.util.spec_from_file_location('bounded_beam_shell_delivery', source)
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
h.REPO=ROOT.parents[2]
h.TASK_DIR=ROOT/('slice'+number)
h.EVIDENCE=h.TASK_DIR/'evidence'
h.BUDGET_FILE=h.TASK_DIR/'budget.json'
h.LOCK_FILE=ROOT/'running.lock'
h.ALLOWANCE=1800.;h.RESERVE=300.
h.CHILD_ENV.update(VECLIB_MAXIMUM_THREADS='1', ANYMESHER_DISABLE_NATIVE='1', ANYMESHER_REQUIRE_NATIVE='0')
h.IDENTITY_FILES += ['examples/beam_shell_coupling.py', 'tests/test_beam_shell_workflow.py']
raise SystemExit(h.main())
