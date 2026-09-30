from pathlib import Path
import json,os,subprocess,sys
import numpy as np
r=Path.cwd().resolve();temp=Path(os.environ['TEMP'])
fixtures=temp/'r8-staged-load-installed-v1'/'fixtures'
for label,name in (("old","r8-accepted-observer-installed-v3"),("new","r8-staged-load-installed-v1")):
 site=(temp/name/'site').resolve();env=os.environ.copy();env['PYTHONPATH']=str(site)+os.pathsep+str(fixtures)
 subprocess.run([sys.executable,str(r/'run_legacy.py'),str(r/label),str(site)],env=env,check=True)
a=np.load(r/'old.npz');b=np.load(r/'new.npz')
assert a.files==b.files and all(np.array_equal(a[k],b[k]) for k in a.files)
assert (r/'old.checkpoint').read_bytes()==(r/'new.checkpoint').read_bytes()
(r/'comparison.json').write_text(json.dumps(dict(status="passed",checkpoint_bytes_identical=True,physical_array_fields_identical=a.files,old_wheel_sha256="243b2d8a2f1b03a6f08c49624f449e6e282749203b77b37b4be7817cd8758317",new_wheel_sha256="0c45666609355e654cb726a0e4e0780d386bccfaafef1209ffd994bdd3b9d09c"),indent=2))
print('legacy arrays and checkpoint bytes identical')
