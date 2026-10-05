from pathlib import Path
import hashlib,json,shutil
old=Path('C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-ge-fibre-finite-consumer-v1')
root=Path('C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-ge-native-energy-coupled-consumer-v1')
source=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/tests/test_experimental_stiffened_shell_consumer.py')
assert not root.exists()
root.mkdir();(root/'tests').mkdir()
shutil.copyfile(source,root/'tests'/source.name)
shutil.copyfile(old/'pytest.ini',root/'pytest.ini')
runner=(old/'run_installed.py').read_text().replace('r8-ge-fibre-finite-installed-v2','r8-ge-native-energy-coupled-installed-v1')
runner=runner.replace('909f26ce982470dec3c2030ea72f78b227085672855c67b99897579c7872a531','b0f15d3ebc5b261f7baf620f7bcbf6866cd6a090b77760b503cfd20131f9dc87')
runner=runner.replace("'-k','physical_fibre'","'-k','physical_fibre or j2_native_fibre'")
runner=runner.replace("==4","==7").replace("'consumer_tests':4","'consumer_tests':7")
(root/'run_installed.py').write_text(runner)
supervisor=(old/'run_bounded.py').read_text().replace('r8-ge-fibre-finite-installed-v2','r8-ge-native-energy-coupled-installed-v1')
supervisor=supervisor.replace("OMP_NUM_THREADS='1')","OMP_NUM_THREADS='1',NUMBA_NUM_THREADS='1')")
(root/'run_bounded.py').write_text(supervisor)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(root/'manifest.json').write_text(json.dumps({'consumer_source_head':'268001efc9102b46ffeb6ea776472a26205b4152',
    'candidate':'tests-only native-J2 consumer slice; runtime unchanged',
    'source_test_sha256':sha(source),'inputs':{p.relative_to(root).as_posix():sha(p)
        for p in [root/'tests'/source.name,root/'pytest.ini',root/'run_installed.py',root/'run_bounded.py']}},indent=2))
print(root)
