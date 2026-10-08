from pathlib import Path
import hashlib,json
import numpy as np
from scipy import linalg
from threadpoolctl import threadpool_info
root=Path(__file__).resolve().parent
z=np.load(root/'scalar.npz',allow_pickle=False)
p,g,m=z['projection'],z['discrete_lower'],z['reference_upper']
values,vectors=linalg.eigh(m,g)
v=vectors[:,-1];v=v/np.max(np.abs(v));density=p@v
mass=p.T@p/32
assert np.max(np.abs(mass-np.diag(np.diag(mass))))<1e-15
scale=np.diag(1/np.sqrt(np.diag(mass)))
gs,ms=scale@g@scale,scale@m@scale
scaled=linalg.eigvalsh(ms,gs)
assert np.max(np.abs(values-scaled))/max(values[-1],1)<1e-10
out=dict(status='SAVED_ARRAY_REPRESENTATION_DIAGNOSTIC_ONLY',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
input_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ('scalar.json','scalar.npz')},
worst_lifting_multiplier_coefficients=v.reshape(8,2).tolist(),
worst_lifting_density_halves=density.tolist(),
worst_lifting_scalar_action=(z['action']@v).tolist(),
physical_L2_density_mass_diagonal=np.diag(mass).tolist(),
raw_Gram_condition=dict(discrete=float(np.linalg.cond(g)),reference=float(np.linalg.cond(m))),
physical_L2_normalized_Gram_condition=dict(discrete=float(np.linalg.cond(gs)),reference=float(np.linalg.cond(ms))),
quotient_congruence_relative_difference=float(np.max(np.abs(values-scaled))/values[-1]),
all_generalized_eigenvalues=values.tolist(),
minimum_discrete_eigenvalue=float(linalg.eigvalsh(g)[0]),
limitations='No accepted contract/threshold amendment, native beta, loaded solve or space selection. Raw conditioning failure preserved.',
pools=threadpool_info())
(root/'representation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ('raw_Gram_condition','physical_L2_normalized_Gram_condition','quotient_congruence_relative_difference')}))
