from pathlib import Path
import hashlib, importlib, importlib.metadata, json, os, sys
import anysolver, pytest, threadpoolctl
root=Path(__file__).resolve().parent
contract=json.loads((root/'inputs.json').read_text())
site=Path(contract['installed_site']).resolve()
assert Path(anysolver.__file__).resolve().is_relative_to(site),anysolver.__file__
deps={}
for name,expected in contract['baseline_dependencies'].items():
    m=importlib.import_module(name)
    item={'version':importlib.metadata.version(name),'import':str(Path(m.__file__).resolve())}
    assert item['version']==expected['version'],(name,item,expected)
    assert Path(item['import']).resolve()==Path(expected['import']).resolve(),(name,item,expected)
    if name=='anymaterial':
        item['curves_sha256']=hashlib.sha256((Path(m.__file__).parent/'curves.py').read_bytes()).hexdigest()
        assert item['curves_sha256']==expected['curves_sha256']
    deps[name]=item
(root/'dependencies.json').write_text(json.dumps(deps,indent=2))
pools=threadpoolctl.threadpool_info()
assert all(p['num_threads']==1 for p in pools),pools
assert os.environ['NUMBA_DISABLE_JIT']=='1'
print(json.dumps({'anysolver':anysolver.__file__,'threadpools':pools,'python':sys.version,'numba_disable_jit':os.environ['NUMBA_DISABLE_JIT']}),flush=True)
status=pytest.main(['-q','-c',str(root/'pytest.ini'),'--basetemp',str(root/'pytest-tmp'),'--junitxml',str(root/'junit.xml')]+['tests/'+p for p in contract['selected']])
loaded={name:str(Path(module.__file__).resolve()) for name,module in list(sys.modules.items()) if name.split('.')[0] in ('anysolver','anyfem') and getattr(module,'__file__',None)}
assert all(Path(path).is_relative_to(site) for path in loaded.values()),loaded
pools=threadpoolctl.threadpool_info();assert all(p['num_threads']==1 for p in pools),pools
(root/'imports.json').write_text(json.dumps(loaded,indent=2))
(root/'settings.json').write_text(json.dumps({'python':sys.version,'threadpools':pools,'numba_disable_jit':os.environ['NUMBA_DISABLE_JIT']},indent=2))
sys.exit(status)
