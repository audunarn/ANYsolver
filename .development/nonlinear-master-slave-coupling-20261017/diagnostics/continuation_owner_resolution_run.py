"""Archive the ONE adopted resolution candidate, then run its two target gates."""
import difflib
import hashlib
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[3]
task = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1])
archive = out/'candidate-source'
archive.mkdir(parents=True, exist_ok=False)
base = task/'evidence/dc-resolution-base'
paths = ('src/anysolver/nonlinear_static.py',
         'tests/test_nonlinear_beam_shell_slice3.py',
         'tests/test_nonlinear_beam_shell_slice3_continuation.py')
expected = ('8c545e86969ed8ab7090e586e59b174f67b7448a409d6d8c361c264d23e91e1f',
            '7d9120ffaebc0003c55280aac0b34f77421d01f19dff9d324c4bd3090e3cc174',
            '85a2387f26d40d612c5f0b1d317d56291dd51815910768608cd70e65010a48fe')
patch = []
for relative, wanted in zip(paths, expected):
    old = (base/Path(relative).name).read_bytes()
    if hashlib.sha256(old).hexdigest() != wanted:
        raise RuntimeError('exact resolution base identity changed')
    new = (repo/relative).read_bytes()
    (archive/Path(relative).name).write_bytes(new)
    patch.extend(difflib.unified_diff(old.decode().splitlines(True), new.decode().splitlines(True),
                                    fromfile='a/'+relative, tofile='b/'+relative))
(out/'resolution-candidate.patch').write_text(''.join(patch))
if '--archive-only' in sys.argv:
    raise SystemExit(0)
import pytest
raise SystemExit(pytest.main(['tests/test_nonlinear_beam_shell_slice3_continuation.py',
    '-k', 'dc_full_target', '-vv', '--tb=short', '--basetemp='+str(out/'pytest-tmp')]))
