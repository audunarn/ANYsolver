"""Native unloaded curved-beam modes versus separate continuum Ritz fields."""
from dataclasses import asdict
from hashlib import sha256
import numpy as np
from numpy.polynomial.legendre import leggauss,legvander
from docs.reference_cases import ge_beam3_curved_linear_ritz_reference as ritz
from docs.reference_cases import ge_beam3_curved_moment_fixture as fixture

INERTIA=np.diag([1.,1.,1.,.02,.01,.01])


def modal_overlap(macros,native_modes,reference):
    """Independent high-order kinetic work of lifted native velocity fields."""
    n=6*(2*macros+1); modes=np.asarray(native_modes)
    if modes.shape!=(n+6*macros,6): raise ValueError('complete native modal field')
    gram=np.zeros((6,6)); overlap=np.zeros((6,6)); refgram=np.zeros((6,6))
    points,weights=leggauss(16); coefficients=reference.modes.reshape(reference.degree+1,6,6)
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
    mac=overlap**2/np.outer(np.diag(gram),np.diag(refgram))
    return dict(native_mass_gram=gram,reference_mass_gram=refgram,overlap=overlap,mac=mac)


def build(save,progress):
    from anysolver._ge_beam3_seeded_load_program import ForceProgram
    from anysolver._ge_beam3_retained_fibre_state import Context
    from anysolver._ge_beam3_retained_fibre_modes import prepare,FROZEN
    from anysolver._native_exact_shift_chain_modes import solve_factor_chain_modes
    from anysolver._ge_beam3_p5_seeded.core import canonical
    refs=[]
    for degree,quadrature in ((14,64),(18,80)):
        progress(dict(stage='RITZ',degree=degree))
        refs.append(ritz.solve(fixture.reference_section(),INERTIA,degree=degree,quadrature=quadrature))
    fine=refs[-1]; profile_error=float(np.max(abs(refs[0].eigenvalues/fine.eigenvalues-1)))
    if profile_error>=1e-8: raise ValueError('reference frequency profile disagreement')
    save('reference-diagnostic.json',canonical([asdict(r) for r in refs]))
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
        if np.min(modes.eigenvalues)<=0: raise ValueError('unloaded supported native instability')
        fields=modal_overlap(count,modes.full_modes,fine)
        if max(np.max(abs(fields[k]-np.eye(6))) for k in ('native_mass_gram','reference_mass_gram'))>1e-8:
            raise ValueError('separate kinetic work reconstruction disagrees')
        detail=dict(packet=packet,modes=modes,field_comparison=fields,checkpoint_sha256=sha256(capsule).hexdigest())
        save(f'modes-{count}.json',canonical(detail))
        rows.append(dict(macros=count,eigenvalues=modes.eigenvalues.tolist(),reference_eigenvalues=fine.eigenvalues.tolist(),
            relative_frequency_errors=np.abs(np.sqrt(modes.eigenvalues/fine.eigenvalues)-1).tolist(),
            diagonal_mac=np.diag(fields['mac']).tolist(),spectral_residual=modes.spectral_residual,
            original_ritz_residual=modes.original_ritz_residual,reference_profile_eigenvalue_difference=profile_error))
        progress(dict(stage='NATIVE_COMPLETE',macros=count))
    return dict(schema='GE_BEAM3_CURVED_REFERENCE_MODES_DEVELOPMENT_V1',rows=rows,
        status='DEVELOPMENT_SPECTRAL_COMPARISON_NOT_QUALIFICATION',production_qualified=False,independent_review='PENDING',
        nonlinear_solves=0,new_reference_solves=2,new_native_spectra=3,unloaded_only=True,
        clustered_mac_qualification=False,buckling_factor_authorized=False)
