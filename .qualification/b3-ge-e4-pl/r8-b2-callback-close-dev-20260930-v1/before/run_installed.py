from pathlib import Path
import sys,json,pytest,anysolver
import anysolver._b2_physical_linear_definition,anysolver._b2_physical_flexibility_linear
r=Path(__file__).resolve().parent
site=Path('C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-f10-f11-point-installed-v1/site').resolve()
assert Path(anysolver.__file__).resolve().is_relative_to(site)
code=pytest.main(['-q','-c',str(r/'pytest.ini'),'--basetemp='+str(r/'pytest-tmp'),'--junitxml='+str(r/'inventory.xml'),'tests/test_stiffened_shell_b2_q4_panel_experimental.py::test_point_panel_batch_callback_close_preserves_complete_prefix[False-5]'])
imports={n:str(Path(m.__file__).resolve()) for n,m in list(sys.modules.items()) if n.split('.')[0]=='anysolver' and getattr(m,'__file__',None)}
assert all(Path(p).is_relative_to(site) for p in imports.values())
(r/'imports.json').write_text(json.dumps(imports,indent=2))
sys.exit(code)
