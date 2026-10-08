from pathlib import Path
import json
import os
import sys

from scripts import r8_bl5_regional_action_dev as action

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[4]
b=json.loads((ROOT/'bindings.json').read_text())
sha=action.hashlib.sha256
action.require(not sys.flags.optimize,'unoptimized execution required')
action.require(sha((REPO/'scripts/r8_bl5_regional_action_dev.py').read_bytes()).hexdigest()==b['source_sha256'],'reviewed regional source differs')
action.require(os.environ.get('NUMBA_DISABLE_JIT')=='1','JIT off required')
output=ROOT/'regional-actions.json'
action.require(not output.exists(),'fresh regional output required')
report=action.compare_saved(REPO,b['inputs'])
output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',newline='\n')
print(json.dumps({'solve_count':report['solve_count'],'native_minus_external':report['native_minus_external']}))
