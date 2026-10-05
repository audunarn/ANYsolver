from pathlib import Path
import hashlib,json
import pytest
from anysolver import stiffened_shell as ss
root=Path(__file__).resolve().parent;repo=root.parents[2]
assert Path(ss.__file__).resolve().is_relative_to(root/'site-v3')
test=repo/'tests/test_stiffened_shell_native_displacement_adaptive.py'
assert (repo/'tests/data/native_mixed_j2_displacement/adaptive-midpoint-v1.bin').read_bytes()==(root/'program-accepted-1-v1.checkpoint').read_bytes()
status=pytest.main(['-q',str(test),'-k','actual_mixed_adaptive_midpoint','-p','no:cacheprovider','--basetemp',str(root/'pytest-final-v2'),
                   '--junitxml',str(root/'test-final-v2.xml')])
(root/'test-final-result-v2.json').write_text(json.dumps(dict(
    pytest_exit_code=int(status),test_sha256=hashlib.sha256(test.read_bytes()).hexdigest(),
    scope='Final installed three native adaptive lifecycle cases, including actual mixed midpoint'),indent=2)+'\n',encoding='utf-8')
raise SystemExit(status)
