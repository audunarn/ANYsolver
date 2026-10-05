from pathlib import Path
import hashlib,json,subprocess,sys
root=Path(__file__).resolve().parent;dist=root/'dist-v24';dist.mkdir()
wheel=dist/'anysolver-0.4.7-py3-none-any.whl'
fem=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/.qualification/stiffened-shell/r8-ge-distributing-material-consumer-dev-20261004-v1/dist-v3/anyfem-0.4.1-py3-none-any.whl')
assert hashlib.sha256(fem.read_bytes()).hexdigest()=='716ac11f89336ec2a84b54b580ea1367ff6ce456d797497118e87b1b596bca49'
commands=[[sys.executable,'-m','pip','wheel','.', '--no-deps','--no-build-isolation','--no-cache-dir','-w',str(dist)],
[sys.executable,'-m','pip','install','--no-deps','--no-cache-dir','--target',str(root/'site-v24'),str(wheel),str(fem)]]
for tag,command in zip(('build-solver-v24','install-v24'),commands):
    with (root/(tag+'.log')).open('xb') as out:
        result=subprocess.run(command,stdout=out,stderr=subprocess.STDOUT,timeout=120)
    assert result.returncode==0,result.returncode
(root/'artifact-v24.json').open('x').write(json.dumps(dict(commands=commands,wheels={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (wheel,fem)}),indent=2)+'\n')
print('Built and installed final numerical identity candidate.')
