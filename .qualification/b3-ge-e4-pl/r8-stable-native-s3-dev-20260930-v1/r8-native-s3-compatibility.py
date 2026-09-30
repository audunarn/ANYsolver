from pathlib import Path
import json,sys,hashlib
import anysolver
from test_stiffened_shell_ge_physical_fibre_linear import _definition
from anysolver._stiffened_shell_ge_experimental import NodalAction
payload=Path(sys.argv[1]).read_bytes()
a=anysolver.stiffened_shell.create_analysis(definition=_definition(False,True))
try:
 result=a.restore(payload);assert a.checkpoint()==payload
 status='completed';failure=None
 try:a.solve((NodalAction('beam',105,(0.,0.,1000.,0.,0.,0.)),),targets=(.5,))
 except RuntimeError as e:
  if str(e) not in ('finite mixed backtrack budget exhausted','finite mixed Newton iteration limit'):raise
  status='nonconverged';failure=str(e)
 out={'source':anysolver.__file__,'restored_residual':result.free_equilibrium_ratio,'continuation_status':status,'failure':failure,'accepted_factors':a.recover().accepted_factors,'checkpoint_sha256':hashlib.sha256(a.checkpoint()).hexdigest(),'legacy_policy':not getattr(a._finite_driver,'_stable_s3',False)}
 Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
finally:a.close()
