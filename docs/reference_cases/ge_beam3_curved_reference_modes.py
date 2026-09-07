"""Native unloaded curved-beam modes versus separate continuum Ritz fields."""
from hashlib import sha256
from pathlib import Path
import numpy as np
from numpy.polynomial.legendre import leggauss,legvander
from docs.reference_cases import ge_beam3_curved_linear_ritz_reference as ritz
from docs.reference_cases import ge_beam3_curved_moment_fixture as fixture
from docs.reference_cases.ge_beam3_preserved_arch_load_comparison import parse

INERTIA=np.diag([1.,1.,1.,.02,.01,.01])
REFERENCE_PATH=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-curved-spectra-20260907-v1/reference-diagnostic.json')
REFERENCE_SHA='9434d222b33aaedfe36a0c128a476b9a14692107f6663b923eb4484cbe85a51c'


def preserved_reference():
    raw=REFERENCE_PATH.read_bytes()
    if len(raw)!=646569 or sha256(raw).hexdigest()!=REFERENCE_SHA: raise ValueError('preserved continuum reference identity')
    values=parse(raw); results=[]
    for value in values:
        value=dict(value)
        for key in ('stiffness','mass','eigenvalues','modes'): value[key]=np.asarray(value[key])
        results.append(ritz.RitzResult(**value))
    return raw,results


def modal_overlap(macros,native_modes,reference,*,quadrature=16):
    """Independent high-order kinetic work of lifted native velocity fields."""
    n=6*(2*macros+1); modes=np.asarray(native_modes)
    if modes.shape!=(n+6*macros,6) or not np.isfinite(modes).all(): raise ValueError('complete finite native modal field')
    if type(quadrature) is not int or quadrature not in (4,16,32): raise ValueError('explicit diagnostic kinetic rule')
    gram=np.zeros((6,6)); overlap=np.zeros((6,6)); refgram=np.zeros((6,6))
    points,weights=leggauss(quadrature); coefficients=reference.modes.reshape(reference.degree+1,6,6)
    for eid in range(macros):
        for cell in (0,1):
            left=2*eid+cell; right=left+1
            tl=-1+left/macros; tr=-1+right/macros
            xl=np.array([tl,fixture.HEIGHT*(1-tl*tl),0.]); xr=np.array([tr,fixture.HEIGHT*(1-tr*tr),0.])
            omega=modes[n+6*eid+3*cell:n+6*eid+3*cell+3]
            for point,weight in zip(points,weights):
                eta=(point+1)/2; t=(1-eta)*tl+eta*tr; jac=np.sqrt(1+(.3*t)**2)
                tangent=np.array([1.,-.3*t,0.])/jac
                frame=np.column_stack((tangent,[0.,0.,1.],np.cross(tangent,[0.,0.,1.])))
                offset=np.array([t,fixture.HEIGHT*(1-t*t),0.])-((1-eta)*xl+eta*xr)
                velocity=(1-eta)*modes[6*left:6*left+3]+eta*modes[6*right:6*right+3]-ritz.skew(offset)@omega
                a=np.vstack((frame.T@velocity,frame.T@omega))
                phi=(1+t)*legvander(np.array([t]),reference.degree)[0]
                field=np.einsum('i,ijk->jk',phi,coefficients)
                b=np.vstack((frame.T@field[:3],frame.T@field[3:]))
                measure=float(weight*jac/(2*macros))
                gram+=measure*(a.T@INERTIA@a); overlap+=measure*(a.T@INERTIA@b); refgram+=measure*(b.T@INERTIA@b)
    if min(np.min(np.diag(gram)),np.min(np.diag(refgram)))<=0: raise ValueError('positive physical modal norms')
    mac=overlap**2/np.outer(np.diag(gram),np.diag(refgram))
    return dict(native_mass_gram=gram,reference_mass_gram=refgram,overlap=overlap,mac=mac)


def build(save,progress):
    from anysolver._ge_beam3_seeded_load_program import ForceProgram
    from anysolver._ge_beam3_retained_fibre_state import Context
    from anysolver._ge_beam3_retained_fibre_modes import prepare,FROZEN
    from anysolver._native_exact_shift_chain_modes import solve_factor_chain_modes
    from anysolver._ge_beam3_p5_seeded.core import canonical
    progress(dict(stage='PRESERVED_RITZ_REFERENCE'))
    reference_raw,refs=preserved_reference()
    fine=refs[-1]; profile_error=float(np.max(abs(refs[0].eigenvalues/fine.eigenvalues-1)))
    if profile_error>=1e-8: raise ValueError('reference frequency profile disagreement')
    save('reference-diagnostic.json',reference_raw)
    rows=[]
    for count in (1,2,4):
        progress(dict(stage='NATIVE_PREPARE',macros=count))
        model=fixture.model(count); program=ForceProgram((0.,),())
        capsule=Context(model,program).checkpoint(())
        save(f'checkpoint-{count}.json',capsule)
        packet,guard=prepare(model,program,capsule,{eid:INERTIA for eid in model.mesh.elements},material_policy=FROZEN)
        progress(dict(stage='NATIVE_SPECTRUM',macros=count))
        modes=solve_factor_chain_modes(packet.left,packet.right,packet.geometric,packet.kinetic,
            packet.free,packet.algebraic,bounds=(-100.,1e5),num_modes=6,root_width=1e-10)
        guard()
        save(f'native-spectrum-{count}.json',canonical(dict(packet=packet,modes=modes)))
        if np.min(modes.eigenvalues)<=0: raise ValueError('unloaded supported native instability')
        fields=modal_overlap(count,modes.full_modes,fine)
        same_rule=modal_overlap(count,modes.full_modes,fine,quadrature=4)
        if np.max(abs(same_rule['native_mass_gram']-np.eye(6)))>1e-11:
            raise ValueError('separate native-rule kinetic work reconstruction disagrees')
        if np.max(abs(fields['reference_mass_gram']-np.eye(6)))>1e-8:
            raise ValueError('separate continuum kinetic work reconstruction disagrees')
        detail=dict(packet=packet,modes=modes,field_comparison=fields,frozen_rule_field_comparison=same_rule,
            checkpoint_sha256=sha256(capsule).hexdigest())
        save(f'modes-{count}.json',canonical(detail))
        rows.append(dict(macros=count,eigenvalues=modes.eigenvalues.tolist(),reference_eigenvalues=fine.eigenvalues.tolist(),
            relative_frequency_errors=np.abs(np.sqrt(modes.eigenvalues/fine.eigenvalues)-1).tolist(),
            diagonal_mac=np.diag(fields['mac']).tolist(),spectral_residual=modes.spectral_residual,
            native_rule_kinetic_identity_error=float(np.max(abs(same_rule['native_mass_gram']-np.eye(6)))),
            higher_rule_kinetic_quadrature_error=float(np.max(abs(fields['native_mass_gram']-np.eye(6)))),
            original_ritz_residual=modes.original_ritz_residual,reference_profile_eigenvalue_difference=profile_error))
        progress(dict(stage='NATIVE_COMPLETE',macros=count))
    return dict(schema='GE_BEAM3_CURVED_REFERENCE_MODES_DEVELOPMENT_V2',rows=rows,
        status='DEVELOPMENT_SPECTRAL_COMPARISON_NOT_QUALIFICATION',production_qualified=False,independent_review='PENDING',
        nonlinear_solves=0,new_reference_solves=0,new_native_spectra=3,unloaded_only=True,
        clustered_mac_qualification=False,buckling_factor_authorized=False)
