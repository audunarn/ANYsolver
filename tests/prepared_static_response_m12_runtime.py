"""Read-only runtime/binary identity record; not arithmetic qualification."""
import hashlib,json,os,sys
from pathlib import Path
import numpy,scipy
from scipy.sparse.linalg._dsolve import _superlu

def identity(path):
    path=Path(path)
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

if __name__=='__main__':
    import threadpoolctl
    pools=threadpoolctl.threadpool_info()
    record={'python':sys.version,'executable':sys.executable,'numpy':numpy.__version__,'scipy':scipy.__version__,
        'superlu_extension':identity(_superlu.__file__),'loaded_threadpools':pools,
        'threadpool_binary_identities':[identity(p['filepath']) for p in pools],
        'runtime_environment':{k:os.environ.get(k) for k in ('NUMBA_DISABLE_JIT','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS')},
        'qualification':'IDENTITY_ONLY; no proof of kernels, rounding mode or FTZ/DAZ state'}
    Path(sys.argv[1]).write_text(json.dumps(record,indent=2));print(json.dumps(record))
