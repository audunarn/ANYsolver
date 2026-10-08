"""Retain failed v1 and run only changed stable test plus public example."""
from pathlib import Path
raw=Path(__file__).resolve().parent
script=(raw/'installed-v1.py').read_text()
script=script.replace('installed-result-v1.json','installed-result-v2.json')
script=script.replace('installed-junit-v1.xml','installed-junit-v2.xml')
script=script.replace('public-example-v1','public-example-v2')
script=script.replace("str(repo/'tests/test_stiffened_shell_native_arc.py')",
    "str(repo/'tests/test_stiffened_shell_native_arc.py')+'::test_stable_elastic_s3_force_seed_arc_and_historical_rejection'")
assert not (raw/'installed-v2.py').exists()
(raw/'installed-v2.py').write_bytes(script.encode('ascii'))
runner=(raw/'run-bounded-v1.py').read_text()
runner=runner.replace("assert phase in ('build','installed')","assert phase=='installed'")
runner=runner.replace("script='build-installed-v1.py' if phase=='build' else 'installed-v1.py'","script='installed-v2.py'")
runner=runner.replace("phase+'-v1'","phase+'-v2'")
(raw/'run-bounded-v2.py').write_bytes(runner.encode('ascii'))
print('Prepared focused installed-v2 without changing v1 failure evidence or wheel.')
