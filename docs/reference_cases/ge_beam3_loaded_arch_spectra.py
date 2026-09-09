"""Loaded continuum/native comparison using saved four-macro arch states."""
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import numpy as np
from docs.reference_cases import ge_beam3_curved_p5_arch_reference as equilibrium
from docs.reference_cases import ge_beam3_loaded_ritz_reference as ritz
from docs.reference_cases import ge_beam3_fibre_arch_refinement as family

INPUT=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-fibre-arch4-20260907-3f05a4e/checkpoint-diagnostic.json')
INPUT_SHA='bcf90a0eca2923ee04ab00bf61b6e1eabdac40779671f90666bdbc2964420a1f'


def input_bytes():
    raw=INPUT.read_bytes()
    if len(raw)!=95786 or sha256(raw).hexdigest()!=INPUT_SHA: raise ValueError('preserved four-macro checkpoint identity')
    return raw


def build(save,progress):
    raw=input_bytes(); save('input-checkpoint.json',raw)
    from anysolver import _ge_beam3_seeded_fibre_control as control
    from anysolver import _ge_beam3_controlled_fibre_modes as spectral
    from anysolver._ge_beam3_p5_seeded.core import canonical
    model=family.model(4); program=family.program(4); context=control.Context(model,program)
    _,records=context.restore(raw)
    if context.checkpoint(records)!=raw: raise ValueError('preserved control replay changed')
    inertias={eid:np.diag([1.,1.,1.,.02,.01,.01]) for eid in model.mesh.elements}
    samples={-1.,0.,*map(float,np.linspace(-1.,0.,33))}
    for order in (48,64): samples.update(-abs(float(t)) for t in ritz.quadrature_sites(order)[0])
    previous=None; rows=[]
    for cursor,target in ((1,.01),(4,.055)):
        progress(dict(stage='CONTINUUM_EQUILIBRIUM',target=target))
        reference=equilibrium.solve(target,height=.1,axial=1.,shear=.4,bending=.0001,previous=previous,
            profile='BVP9',sample_parameters=sorted(samples))
        previous=reference; save(f'equilibrium-{cursor}.json',canonical(asdict(reference)))
        spectra=[]
        for degree,order in ((12,48),(16,64)):
            progress(dict(stage='CONTINUUM_SECOND_VARIATION',target=target,degree=degree))
            result=ritz.solve(reference,degree=degree,quadrature=order)
            save(f'ritz-{cursor}-{degree}.json',canonical(asdict(result))); spectra.append(result)
        coarse,fine=spectra
        profile=float(np.max(abs(coarse.eigenvalues-fine.eigenvalues)/np.maximum(1.,abs(fine.eigenvalues))))
        if profile>1e-7: raise ValueError('loaded Ritz resolution disagreement')
        capsule=context.checkpoint(records[:cursor]); save(f'checkpoint-{cursor}.json',capsule)
        progress(dict(stage='NATIVE_FIXED_LOAD_SPECTRUM',target=target))
        packet,modes=spectral.solve_modes(model,program,capsule,inertias,material_policy=spectral.FROZEN,
            bounds=(-1e6,1e8),num_modes=6,expected_checkpoint_sha256=sha256(capsule).hexdigest())
        save(f'native-{cursor}.json',canonical(dict(packet=packet,modes=modes)))
        rows.append(dict(cursor=cursor,displacement=target,native_load=modes.equilibrium_load_parameter,
            continuum_load=float(1e6*reference.load),continuum_load_slope=float(1e6*reference.load_slope),
            native_eigenvalues=modes.eigenvalues.tolist(),continuum_eigenvalues=fine.eigenvalues.tolist(),
            native_negative_modes=int(np.count_nonzero(modes.eigenvalues<0)),
            continuum_negative_modes=int(np.count_nonzero(fine.eigenvalues<0)),
            eigenvalue_relative_errors=(abs(modes.eigenvalues-fine.eigenvalues)/np.maximum(1.,abs(fine.eigenvalues))).tolist(),
            reference_resolution_error=profile,native_spectral_residual=modes.spectral_residual,
            native_original_ritz_residual=modes.original_ritz_residual,reference_ritz_residual=fine.residual,
            fixed_load_perturbation=True,control_constraint_retained=False,same_equilibrium_branch_proved=False))
        progress(dict(stage='TARGET_COMPLETE',target=target))
    if input_bytes()!=raw: raise ValueError('preserved input changed')
    return dict(schema='GE_BEAM3_LOADED_ARCH_SPECTRAL_DEVELOPMENT_V1',rows=rows,input_sha256=INPUT_SHA,
        status='DEVELOPMENT_LOADED_SPECTRA_NOT_QUALIFICATION',production_qualified=False,independent_review='PENDING',
        native_nonlinear_solves=0,new_continuum_equilibria=2,new_reference_spectra=4,new_native_spectra=2,
        buckling_factor_authorized=False,failed_input_invocation_reclassified=False)
