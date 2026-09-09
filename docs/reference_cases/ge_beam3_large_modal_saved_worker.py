"""Bounded private numerical integration check, using saved factors only."""
import argparse
from hashlib import sha256
import os
from pathlib import Path
import sys
import time
import traceback
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes,canonical
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_n32_spectrum_worker import inputs,PACKETS
from docs.reference_cases.ge_beam3_next_spatial_native import member

REFERENCE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-n32-spectrum-9559f66-20260909')
MANIFEST='05df67c233cd21d0f69340a88f3809b9758c3774718dbfa91dac38d3d202b067'
SPECTRA={'plus':'9a1c89d8ab13d0c6d2e4c0d44fe225de377fd8cfe9bc4672ab679d2cca69facc',
         'minus':'4e41d4da4b407b0ad6b8af7c11bb28fe210cd4a8987d8e0881e94c0e93e0dc45'}


def reference(sign):
    raw=member(REFERENCE,MANIFEST,'wave/'+sign+'-100-a/output/spectrum.json',SPECTRA[sign])
    return raw,strict_bytes(raw)['result']


def run(revision,sign,output):
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('one numerical thread')
    packet,_=inputs(sign);reference_raw,accepted=reference(sign)
    root=Path(output).resolve()
    if root.is_relative_to(ROOT.resolve()):raise ValueError('exclusive external output')
    root.mkdir(exist_ok=False);sys.path.insert(0,str(ROOT/'src'))
    import numpy as np
    from anysolver._native_modal_capacity import solve_large_factor_chain_modes,apply_large_mode_map,POLICY
    from anysolver._ge_beam3_p5_seeded.core import canonical as native
    from anysolver.control import CancellationToken
    class Progress(CancellationToken):
        def __init__(self):super().__init__();self.last=0.;self.stage=None
        def raise_if_cancelled(self,stage=''):
            super().raise_if_cancelled(stage)
            now=time.monotonic()
            if stage!=self.stage or now-self.last>=10.:
                print(dict(stage=stage,sign=sign),flush=True);self.last=now;self.stage=stage
    try:
        print(dict(stage='saved-factor-authority-complete',sign=sign),flush=True)
        l,r,g,b=(np.array(packet[k]) for k in ('left','right','geometric','kinetic'))
        result=solve_large_factor_chain_modes(l,r,g,b,tuple(packet['free_dofs']),tuple(packet['algebraic_dofs']),
            bounds=(-1.,20.),num_modes=6,root_width=1e-10,relative_width=1e-12,cancellation_token=Progress())
        # Keep a complete numerical result even if the independent comparison fails.
        raw=native(result);strict_bytes(raw);write(root/'modes.json',raw)
        expected=np.array(accepted['eigenvalues'])
        error=float(np.max(np.abs(result.eigenvalues-expected)/np.maximum(1.,np.abs(expected))))
        speed=apply_large_mode_map(result,b);ref=b@np.array(accepted['full_modes']).T
        mac=np.sum(speed*ref,axis=0)**2/(np.sum(speed*speed,axis=0)*np.sum(ref*ref,axis=0))
        if not np.isfinite(error) or error>1e-9:raise ValueError('saved full-physical eigenvalue comparison')
        if not np.isfinite(mac).all() or np.min(mac)<1.-1e-9:raise ValueError('saved physical mass MAC comparison')
        if np.count_nonzero(result.eigenvalues<0.)!=1:raise ValueError('preserve actual unstable lowest mode')
        guard(revision)
        if canonical(inputs(sign)[0])!=canonical(packet) or reference(sign)[0]!=reference_raw:
            raise ValueError('saved factors/reference changed')
        write(root/'comparison.json',dict(schema='GE_BEAM3_LARGE_SAVED_FACTOR_MODAL_CHECK_V1',revision=revision,
            policy=POLICY,sign=sign,packet_sha256=PACKETS[sign],reference_sha256=SPECTRA[sign],
            modes_sha256=sha256(raw).hexdigest(),eigenvalue_error=error,mass_mac=mac.tolist(),
            original_ritz_residual=result.original_ritz_residual,coordinates=582,physical_dimension=381,
            equilibrium_rerun=False,history_advanced=False,reference_spectrum_rerun=False,
            production_qualified=False,independent_author_review=False))
        print(dict(stage='saved-factor-modal-complete',sign=sign),flush=True)
    except BaseException:
        write(root/'failure.json',dict(revision=revision,sign=sign,error=traceback.format_exc(),production_qualified=False))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True)
    p.add_argument('--sign',choices=('plus','minus'),required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.revision,a.sign,a.output)
