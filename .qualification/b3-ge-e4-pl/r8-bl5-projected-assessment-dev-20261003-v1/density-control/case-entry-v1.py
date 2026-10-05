"""Freeze the successfully prepared pair without replaying its producer."""
from pathlib import Path
import hashlib,json,runpy,sys
ROOT=Path(__file__).resolve().parent
pins={'probe-v1.py':'71974b719f26c9d2a6e9a12e139baf2ae41d6a38a9ff0ea3521633fda5fb902d',
 'prepared-v1.json':'25a956ee13cf2a36a9dbd6c3e93a06e4db5537cc8a00d78926bf8e9db62028e2',
 'prepared-v1.npz':'423b4171ed678275345340140f34714dc8c76e6f421a081dca4ece3cc65f8ab9'}
def check():
 for name,digest in pins.items():
  if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError('frozen successful preparation differs: '+name)
 execution=json.loads((ROOT/'prepare-v1/execution.json').read_text())
 if execution['status']!='completed' or execution['exit_code']!=0:raise ValueError('successful terminal preparation required')
check()
sys.argv=[str(ROOT/'probe-v1.py'),'case']
try:runpy.run_path(str(ROOT/'probe-v1.py'),run_name='__main__')
finally:check()
