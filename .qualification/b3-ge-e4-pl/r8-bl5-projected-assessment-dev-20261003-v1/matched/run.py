from pathlib import Path
import hashlib,importlib.util,json,sys,shutil
ROOT=Path(__file__).resolve().parent;REPO=Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
INSTALLED=ROOT.parent/'r8-bl5-projected-integration-v1'
RUNTIME=Path('C:/Users/AudunArnesenNyhus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
EXTERNAL_SITE=Path('C:/Python/Python314/Lib/site-packages')
spec=importlib.util.spec_from_file_location('owned_supervisor',ROOT.parent/'r8-bl5-affine-flexible-v1/run.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=ROOT;m.ENV['PYTHONPATH']=''
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
BASIS='discontinuous_p1_cell_average'
mode=sys.argv[1]
if mode=='stage':
 (ROOT/'fixtures').mkdir()
 # Explicit previously reviewed safe helper graph, no archive/history scanning.
 names=('b3_e4_bl5_coherent_aggregation_dev.py','b3_e4_bl5_external_p0_enforcement_dev.py',
 'b3_e4_bl5_external_p0_refinement_dev.py','b3_e4_bl5_matched_mz_native_dev.py','b3_e4_bl5_matched_mz_reference_dev.py',
 'b3_e4_bl5_matched_p0_native_refinement_dev.py','b3_e4_bl5_matched_reference_actions.py',
 'b3_e4_f03_bl5_opensees_line_reference.py','r8_bl5_affine_flexible_native_dev.py','r8_bl5_external_affine_reference_dev.py')
 for name in names:shutil.copyfile(REPO/'scripts'/name,ROOT/'fixtures'/name)
 shutil.copyfile(REPO/'tests/test_stiffened_shell_l1_assembly_experimental.py',ROOT/'fixtures/test_stiffened_shell_l1_assembly_experimental.py')
 wheel=next((INSTALLED/'dist').glob('*.whl'));binding=json.loads((INSTALLED/'binding.json').read_text())
 assert sha(wheel)==binding['wheel_sha256']=='a47e518fe36050e1a2d5a93d9d8c9802138e46c0cc9d8c1c840cc5efdd8650d3'
 (ROOT/'binding.json').write_text(json.dumps(dict(basis=BASIS,wheel_sha256=sha(wheel),source_parent='d5653ec69d62a19ddf2aa1194ae8a1872de2aab5',
 fixtures={p.name:sha(p) for p in (ROOT/'fixtures').iterdir()},external_binary_sha256=sha(EXTERNAL_SITE/'openseespywin/opensees.pyd'),
 cases=['fy','mx','mz'],geometry=dict(nx=16,ny=4,native_members=16,halfcells=32,supports=8),
 question='Does removing the verified torsion density inconsistency improve physical transfer at unchanged resolution?',
 outcomes='Physical/matching control failure: repair. Valid poor transfer: withhold. Improved transfer: justify next assessment, no automatic refinement/F03 acceptance.',
 resources=dict(rows=100000,seconds_per_run=600,process_tree_bytes=8*1024**3,numerical_threads=8,heavy_jobs=1),
 scope='One ordinary development comparison, supplementary OpenSees, not mandatory CalculiX/F03 evidence'),indent=2)+'\n')
elif mode=='external':
 for case in ('fy','mx','mz'):
  m.supervise([str(RUNTIME),'-u',str(ROOT/'fixtures/r8_bl5_external_affine_reference_dev.py'),
   '--site',str(EXTERNAL_SITE),'--output-dir',str(ROOT/'external'/case),'--case',case,'--basis',BASIS], 'external-'+case,8*1024**3)
elif mode=='native':
 wheel=next((INSTALLED/'dist').glob('*.whl'));binding=json.loads((ROOT/'binding.json').read_text())
 m.supervise([sys.executable,'-u',str(ROOT/'fixtures/r8_bl5_affine_flexible_native_dev.py'),
 '--site',str(INSTALLED/'site'),'--wheel',str(wheel),'--source',str(REPO),'--fixtures',str(ROOT/'fixtures'),
 '--external',str(ROOT/'external'),'--output',str(ROOT/'native'),'--basis',BASIS,'--wheel-sha',binding['wheel_sha256']], 'native-run',1024**3)
else:raise ValueError(mode)
