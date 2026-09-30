from pathlib import Path
import hashlib,json,os,sys,xml.etree.ElementTree as ET
import anysolver,anyfem,numba,pytest,threadpoolctl
root=Path(__file__).resolve().parent
site=(root.parent/'r8-stable-native-s3-installed-v3/site').resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
identity={'solver_wheel_sha256':'953f20d9a5f0fb7ae0c6c9068d373f7af625c7569ad5962e4e1cf9ea45765555',
    'consumer_wheel_sha256':'ff143e5fece9dd4cec261aa69edbec03acc801d3d0bbfcb90cea7519d814f0c0',
    'test_sha256':sha(root/'tests/test_experimental_stiffened_shell_consumer.py'),
    'source_test_sha256':sha(Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/tests/test_experimental_stiffened_shell_consumer.py')),
    'python':sys.version,'threads':threadpoolctl.threadpool_info()}
assert identity['test_sha256']==identity['source_test_sha256']
assert identity['threads'] and all(pool['num_threads']==1 for pool in identity['threads'])
assert numba.config.DISABLE_JIT and numba.config.NUMBA_NUM_THREADS==1
(root/'identity.json').write_text(json.dumps(identity,indent=2))
code=pytest.main(['-q','-c',str(root/'pytest.ini'),'--junitxml',str(root/'inventory.xml'),
    '--basetemp',str(root/'pytest-tmp'),'-k','elastic_s3_native_fibre',
    str(root/'tests/test_experimental_stiffened_shell_consumer.py')])
assert code==0
suites=ET.parse(root/'inventory.xml').getroot().findall('testsuite')
assert sum(int(s.attrib['tests']) for s in suites)==1
assert all(int(s.attrib['failures'])==int(s.attrib['errors'])==int(s.attrib['skipped'])==0 for s in suites)
loaded={name:str(Path(module.__file__).resolve()) for name,module in list(sys.modules.items())
    if name.split('.')[0] in ('anysolver','anyfem') and getattr(module,'__file__',None)}
assert all(Path(path).is_relative_to(site) for path in loaded.values())
(root/'imports.json').write_text(json.dumps(loaded,indent=2))
print(json.dumps({'loaded_modules':len(loaded),'consumer_tests':1}))
