from pathlib import Path
import hashlib,json,sys
import numpy as np
import anysolver
from test_stiffened_shell_ge_experimental import _panel
from anysolver.stiffened_shell import create_analysis,NodalAction
out=Path(sys.argv[1]);site=Path(sys.argv[2]).resolve()
owner=create_analysis(definition=_panel())
result=owner.solve((NodalAction("beam",105,(0.,0.,10.,0.,0.,0.)),),(.5,1.))
raw=owner.checkpoint();(out.with_suffix(".checkpoint")).write_bytes(raw)
np.savez(out.with_suffix(".npz"),**{n:getattr(result,n) for n in ("shell_displacement","beam_positions","beam_frames","cell_frames","cell_resultants","multipliers","support_reactions")})
imports={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.copy().items() if n.split('.')[0]=='anysolver' and getattr(m,'__file__',None)}
assert all(Path(p).is_relative_to(site) for p in imports.values())
out.with_suffix(".json").write_text(json.dumps(dict(checkpoint_sha256=hashlib.sha256(raw).hexdigest(),imports=imports,identity=owner.preflight()["identity"]),indent=2))
owner.close()
