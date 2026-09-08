"""Bounded full/planar/lateral signed spectra of authenticated arch states."""
import argparse
import os
from pathlib import Path
import sys
from docs.reference_cases.ge_beam3_retained_arch_loaded import historical
from docs.reference_cases.ge_beam3_fibre_arch_probe import ROOT, guard
from docs.reference_cases.ge_beam3_retained_prestress_wave import publish, write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT


def planar_partition(packet, nodal_count, check=lambda:None):
    """Partition ORIGINAL factors only when structural zeros prove decoupling."""
    import numpy as np
    check(); left, right, g, b = packet.left, packet.right, packet.geometric, packet.kinetic
    size = right.shape[1]
    if type(nodal_count) is not int or nodal_count%6 or not 6<=nodal_count<=size<=256 or (size-nodal_count)%6:
        raise ValueError('complete nodal/cell layout')
    planar = [start+j for start in range(0,nodal_count,6) for j in (0,1,5)]
    planar += list(range(nodal_count+2,size,3))
    groups = dict(planar=tuple(sorted(planar)), lateral=tuple(i for i in range(size) if i not in planar))
    support = np.array([np.any(right[:,c]!=0.,axis=1) for c in groups.values()],dtype=np.int64).T
    if np.any(np.count_nonzero((left!=0.).astype(np.int64)@support,axis=1)>1):
        raise ValueError('material factors couple planar/lateral families')
    if np.any(np.count_nonzero(np.array([np.any(b[:,c]!=0.,axis=1) for c in groups.values()]),axis=0)>1):
        raise ValueError('kinetic factors couple planar/lateral families')
    if np.any(g[np.ix_(groups['planar'],groups['lateral'])]!=0.) or np.any(g[np.ix_(groups['lateral'],groups['planar'])]!=0.):
        raise ValueError('geometric factor couples planar/lateral families')
    made = {}
    for name, c in groups.items():
        rows = np.flatnonzero(np.any(right[:,c]!=0.,axis=1)); outputs = np.flatnonzero(np.any(left[:,rows]!=0.,axis=1))
        velocities = np.flatnonzero(np.any(b[:,c]!=0.,axis=1)); index = {j:i for i,j in enumerate(c)}
        made[name] = dict(columns=c,left=left[np.ix_(outputs,rows)],right=right[np.ix_(rows,c)],
            geometric=g[np.ix_(c,c)],kinetic=b[np.ix_(velocities,c)],
            free=tuple(index[j] for j in packet.free_dofs if j in index),
            algebraic=tuple(index[j] for j in packet.algebraic_dofs if j in index))
    check(); return made


def inspect_packet(packet, nodal, check):
    import numpy as np
    from scipy.linalg import eigh
    from anysolver._native_paired_factor_chain_modes import solve_paired_factor_chain_modes as paired
    from anysolver._dyadic_factor_chain import reassemble_chain_exact_binary64
    from anysolver._ge_beam3_p5_seeded.core import canonical
    check(); before = canonical(packet)
    # Independent direct stationary elimination, used as a diagnostic comparison
    # to the retained factor-map solver. It is not an independently authored
    # beam formulation or an engineering frequency reference.
    k, mass = reassemble_chain_exact_binary64(packet.left,packet.right,packet.geometric,packet.kinetic,
                                             np.eye(len(packet.mass)),check)
    free, algebraic = packet.free_dofs, packet.algebraic_dofs
    physical = tuple(i for i in free if i not in algebraic)
    trace = k[np.ix_(algebraic,algebraic)]
    np.linalg.cholesky(trace)  # Never hide an unstable massless direction.
    mapping = np.zeros((len(k),len(physical))); mapping[list(physical)] = np.eye(len(physical))
    mapping[list(algebraic)] = -np.linalg.solve(trace,k[np.ix_(algebraic,physical)])
    def relative(a,b): return float(np.linalg.norm(a-b))/max(1.,float(np.linalg.norm(b)))
    stationary = relative(k[list(algebraic)]@mapping,np.zeros((len(algebraic),len(physical))))
    if stationary > 1e-11: raise ValueError('direct algebraic stationarity')
    reduced, kinetic = reassemble_chain_exact_binary64(packet.left,packet.right,packet.geometric,packet.kinetic,mapping,check)
    np.linalg.cholesky(kinetic)
    values = eigh(reduced,kinetic,eigvals_only=True)
    whole = paired(packet.left,packet.right,packet.geometric,packet.kinetic,free,algebraic,
                   bounds=(-100.,1e6),num_modes=6)
    error = relative(whole.eigenvalues,values[:6])
    if error > 1e-11: raise ValueError('independent direct Schur spectral comparison')
    families = planar_partition(packet,nodal,check); modes = {}
    for name,f in families.items():
        print(dict(stage='family-spectrum',family=name),flush=True)
        modes[name] = paired(f['left'],f['right'],f['geometric'],f['kinetic'],f['free'],f['algebraic'],
                             bounds=(-100.,1e6),num_modes=6)
    union = np.sort(np.r_[modes['planar'].eigenvalues,modes['lateral'].eigenvalues])[:6]
    union_error = relative(union,whole.eigenvalues)
    if union_error > 1e-11: raise ValueError('complete/partitioned original spectrum mismatch')
    check()
    if canonical(packet)!=before: raise ValueError('factor inputs changed')
    return dict(whole=whole,families=modes,physical_dimension=len(physical),algebraic_dimension=len(algebraic),
        trace_positive=True,mass_positive=True,stationarity_error=stationary,
        direct_eigenvalues=values,schur_spectrum_error=error,partition_error=union_error,
        current_frequency_squared_not_load_factor=True,full_spatial_qualification=False,production_qualified=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--macros',type=int,required=True)
    p.add_argument('--step',type=int,required=True);p.add_argument('--output',required=True);a=p.parse_args()
    guard(a.revision);raw,binding=historical(a.macros,a.step)
    if sys.flags.optimize or any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()): raise ValueError('one thread and assertions required')
    output=Path(a.output).resolve()
    if output.is_relative_to(ROOT) or output.exists(): raise ValueError('fresh external output required')
    output.mkdir()
    sys.path.insert(0,str(ROOT/'src'))
    import numpy as np
    from anysolver import _ge_beam3_retained_arc_modal as modal
    from anysolver._ge_beam3_p5_seeded.core import canonical
    from docs.reference_cases import ge_beam3_retained_arch_case as case
    m=case.model(a.macros);program=case.program(a.macros)
    masses={i:np.diag([1.,1.,1.,3e-5,1e-5,2e-5]) for i in m.mesh.elements}
    print(dict(stage='arc-modal-capture',macros=a.macros,step=a.step),flush=True)
    packet,check=modal.prepare(m,program,raw,masses,expected_sha256=binding['checkpoint_sha256'])
    write(output/'packet-diagnostic.json',canonical(packet))
    print(dict(stage='full-physical-spectrum',macros=a.macros,step=a.step),flush=True)
    result=inspect_packet(packet,m.mesh.dof_manager.total_dofs,check)
    guard(a.revision);historical(a.macros,a.step)
    value=dict(schema='GE_BEAM3_ARC_CURRENT_REST_SPECTRA_V1',input=binding,macros=a.macros,step=a.step,
        section_inertia_diagonal=[1.,1.,1.,3e-5,1e-5,2e-5],result=result,
        terminal='UNCLASSIFIED_GE_BEAM3_ARC_CURRENT_REST_SPECTRA_ONLY',independent_review='PENDING',production_qualified=False)
    publish(output/'science.json',canonical(value))
    print(dict(stage='arc-spectrum-complete'),flush=True)


if __name__=='__main__':main()
