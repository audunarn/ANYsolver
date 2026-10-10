"""Loaded-x witness and conditional lifecycle using the frozen paired wheel."""
from pathlib import Path
import argparse,json,os,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import r8_f06_paired_displacement_dev as previous
from scripts import r8_f06_fibre_log_domain_dev as infra
from scripts.r8_f06_log_domain_check_dev import runtime,sha,write
DOC=previous.DOC/'loaded-x-v1';PACKAGE=previous.PACKAGE;INPUT=previous.INPUT;INPUT_SHA=previous.INPUT_SHA
WHEEL_SHA='0ed73724bf3c8ccffcc0134628d94720d640840f9592ac8890779f54285ee3d8'
def bindings():
 paths={ROOT/p for p in previous.bindings() if 'AUTHORITY' not in Path(p).name};paths.update((Path(__file__),ROOT/'tests/test_r8_f06_paired_loaded_x_dev.py'))
 paths.update(DOC.glob('*AUTHORITY*.json'));paths.add(DOC/'SLOT_TRANSFER.json')
 for name in ('TARGET_ADOPTION.json','attempt-installed-witness1/witness.json','attempt-installed-history1/accepted.bin','attempt-installed-history1/accepted.npz'):
  if (DOC/name).exists():paths.add(DOC/name)
 return {p.relative_to(ROOT).as_posix():sha(p) for p in paths}
def artifact():
 value=previous.artifact();assert value['wheel_sha256']==WHEEL_SHA;return value

def child(out,stage):
 import psutil
 psutil.Process().cpu_affinity([0]);assert json.loads((out/'bindings.json').read_text())==bindings();assert sha(INPUT)==INPUT_SHA
 write(out/'artifact-before.json',artifact());site=PACKAGE/'site';sys.path[:0]=[str(site),str(ROOT/'tests')]
 os.environ.update(F06_LOADED_X_OUTPUT=str(out),F06_LOADED_X_STAGE=stage,F06_PAIRED_DISPLACEMENT_OUTPUT=str(out))
 runtime(out,'runtime-before',site)
 import pytest
 names={'source-controls':'source','installed-witness':'witness','installed-history':'history','installed-controls':'durability'}
 try:return int(pytest.main([str(ROOT/'tests/test_r8_f06_paired_loaded_x_dev.py'),'-q','-x','-k',names[stage],'-o','pythonpath=','-p','no:cacheprovider','--junitxml',str(out/'junit.xml'),'--basetemp',str(out/'tmp')]))
 finally:
  rt=runtime(out,'runtime-after',site);frozen=json.loads((PACKAGE/'snapshot-bindings.json').read_text())
  for n,p in rt['imports'].items():assert rt['import_sha256'][n]==frozen['src/'+Path(p).relative_to(site).as_posix()]
  write(out/'artifact-after.json',artifact())
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',required=True,choices=('source-controls','installed-witness','installed-history','installed-controls'));p.add_argument('--child',action='store_true');p.add_argument('--out');a=p.parse_args()
 if a.child:raise SystemExit(child(Path(a.out),a.stage))
 assert (DOC/'SLOT_TRANSFER.json').exists()
 if a.stage in ('installed-witness','installed-history'):assert not list(DOC.glob('attempt-'+a.stage+'*')),'one witness/physical attempt only'
 requirements={'source-controls':(),'installed-witness':('source-controls',),'installed-history':('source-controls','installed-witness'),'installed-controls':('installed-history',)}
 for name in requirements[a.stage]:
  attempts=sorted(DOC.glob('attempt-'+name+'*/receipt.json'));assert attempts and json.loads(attempts[-1].read_text())['status']=='PASS'
 if a.stage=='installed-history':
  w=json.loads((DOC/'attempt-installed-witness1/witness.json').read_text());adopt=json.loads((DOC/'TARGET_ADOPTION.json').read_text());assert adopt['target']==w['target'] and adopt['witness_sha256']==sha(DOC/'attempt-installed-witness1/witness.json') and w['eligible']
 authority={'source-controls':'AUTHORITY.json','installed-witness':'WITNESS_AUTHORITY.json','installed-history':'HISTORY_AUTHORITY.json','installed-controls':'CONTROLS_AUTHORITY.json'}[a.stage]
 raise SystemExit(infra.run(a.stage,doc=DOC,entry=__file__,bind=bindings,authority_file=authority))
