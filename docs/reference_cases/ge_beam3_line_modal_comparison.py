"""Saved native spectra versus a separately constructed continuum spectrum."""
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import numpy as np
from numpy.polynomial.legendre import leggauss,legvander
from docs.reference_cases import ge_beam3_dead_line_reference as equilibrium
from docs.reference_cases import ge_beam3_line_modal_reference as modal
from docs.reference_cases.ge_beam3_curved_moment_fixture import HEIGHT,reference_section
from docs.reference_cases.ge_beam3_preserved_arch_load_comparison import parse,canonical

BASE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease')
INERTIA=np.diag([1.,1.,1.,.02,.01,.01])
FORCE=(.3,-.2,.1)
INPUTS={
 'checkpoint-1.json':('ge-beam3-dead-line-20260907-v1/checkpoint-1.json',22929,'680bbf90abb5311c5e606ce33418354ccbe78e2c7d186968577a115e22f61e36'),
 'checkpoint-2.json':('ge-beam3-dead-line-20260907-v1/checkpoint-2.json',41811,'1f11cef7d65542a764defb660200d385ad53b2be1be4d0d1d00f2384e604bca2'),
 'checkpoint-4.json':('ge-beam3-dead-line-20260907-v1/checkpoint-4.json',79669,'8cfae0b45a24defd313e60638aa9b3c88e6ec3ea8ea06789f84469970d55655b'),
 'native-1.json':('ge-beam3-line-spectra-20260907-3e666be/cycle-a/pytest/test_saved_loaded_spectra_sign0/modes-1.json',33372,'4ff09e0ce025853a28ef500ec69649f5e272e42d50b4953ef768dad9a9f5af06'),
 'native-2.json':('ge-beam3-line-spectra-20260907-3e666be/cycle-a/pytest/test_saved_loaded_spectra_sign1/modes-2.json',87752,'b2a0210eaf1db00711fdcab2fba8a88cf3706d47146ae24fdc0dba6dd62bff50'),
 'native-4.json':('ge-beam3-line-spectra-20260907-3e666be/cycle-a/pytest/test_saved_loaded_spectra_sign2/modes-4.json',263748,'c85211ff3dc8a2b9d08e407680f1cf4692485f7e5fb16a9650cde944b17ed96f'),
}
ARTIFACTS=(*INPUTS,'equilibrium.json','reference-14.json','reference-18.json','overlap-1.json','overlap-2.json','overlap-4.json')


def plain(value):
    if isinstance(value,np.ndarray): return value.tolist()
    if isinstance(value,np.generic): return value.item()
    if isinstance(value,dict): return {k:plain(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)): return [plain(v) for v in value]
    return value


def bound_inputs():
    result={}
    for name,(path,size,digest) in INPUTS.items():
        source=BASE/path
        if source.is_symlink() or not source.is_file(): raise ValueError('regular preserved spectral input required')
        raw=source.read_bytes()
        if len(raw)!=size or sha256(raw).hexdigest()!=digest: raise ValueError('preserved spectral input changed')
        parse(raw); result[name]=raw
    return result


def overlap_sites(macros,order):
    if type(macros) is not int or macros not in (1,2,4) or type(order) is not int or order not in (4,16,32):
        raise ValueError('registered modal field quadrature')
    points,weights=leggauss(order); rows=[]
    for eid in range(macros):
        for cell in (0,1):
            left=2*eid+cell; tl=-1+left/macros; tr=-1+(left+1)/macros
            for point,weight in zip(points,weights):
                eta=float((point+1)/2); t=float((1-eta)*tl+eta*tr)
                rows.append((eid,cell,left,tl,tr,eta,t,float(weight)))
    return rows


def overlap(macros,modes,state,reference,equilibrium_packet,*,order):
    """Material-frame transported kinetic MAC, not a clustered qualification."""
    n=6*(2*macros+1); modes=np.asarray(modes,dtype=float)
    if modes.shape!=(n+6*macros,6) or not np.isfinite(modes).all(): raise ValueError('complete native mode field')
    rotations=np.asarray(state['mechanical']['cell_rotations']); gram=np.zeros((6,6)); cross=np.zeros((6,6)); refgram=np.zeros((6,6))
    coefficients=np.asarray(reference['modes']).reshape(reference['degree']+1,6,6)
    lookup={float(t):i for i,t in enumerate(equilibrium_packet['parameter'])}
    for eid,cell,left,tl,tr,eta,t,weight in overlap_sites(macros,order):
        if t not in lookup: raise ValueError('exact material-frame reference sample absent')
        jac=np.sqrt(1+(.3*t)**2); tangent=np.array([1.,-.3*t,0.])/jac
        r0=np.column_stack((tangent,[0.,0.,1.],np.cross(tangent,[0.,0.,1.])))
        qnative=rotations[eid,cell]@r0
        qreference=np.asarray(equilibrium_packet['frames'][lookup[t]])
        xl=np.array([tl,HEIGHT*(1-tl*tl),0.]); xr=np.array([tr,HEIGHT*(1-tr*tr),0.])
        lift=np.array([t,HEIGHT*(1-t*t),0.])-((1-eta)*xl+eta*xr)
        omega=modes[n+6*eid+3*cell:n+6*eid+3*cell+3]
        offset=rotations[eid,cell]@lift
        velocity=(1-eta)*modes[6*left:6*left+3]+eta*modes[6*(left+1):6*(left+1)+3]-modal.skew(offset)@omega
        a=np.vstack((qnative.T@velocity,qnative.T@omega))
        phi=(1+t)*legvander(np.array([t]),reference['degree'])[0]
        field=np.einsum('i,ijk->jk',phi,coefficients)
        b=np.vstack((qreference.T@field[:3],qreference.T@field[3:]))
        measure=weight*jac/(2*macros)
        gram+=measure*(a.T@INERTIA@a); cross+=measure*(a.T@INERTIA@b); refgram+=measure*(b.T@INERTIA@b)
    if min(np.min(np.diag(gram)),np.min(np.diag(refgram)))<=0: raise ValueError('positive kinetic mode norms')
    mac=cross**2/np.outer(np.diag(gram),np.diag(refgram))
    return dict(native_mass_gram=gram,reference_mass_gram=refgram,overlap=cross,material_frame_mac=mac)


def recompute(packets):
    if set(packets)!=set(ARTIFACTS): raise ValueError('exact comparison artifact inventory')
    for name,(_,size,digest) in INPUTS.items():
        raw=canonical(packets[name])
        if len(raw)!=size or sha256(raw).hexdigest()!=digest: raise ValueError('saved native input binding')
    eq=packets['equilibrium.json']; a=packets['reference-14.json']; b=packets['reference-18.json']
    if (eq['profile']!='BVP9' or eq['height']!=HEIGHT or eq['force']!=list(FORCE)
            or eq['section']!=reference_section().tolist() or eq['production_qualified'] is not False):
        raise ValueError('registered continuum equilibrium required')
    arrays={'section','force','parameter','positions','frames','strains','resultants','spatial_forces','spatial_moments'}
    state=equilibrium.ReferenceResult(**{k:np.asarray(v,dtype=float) if k in arrays else v for k,v in eq.items()})
    for p in (state.boundary_error,state.differential_error,state.orthogonality_error):
        if not np.isfinite(p) or not 0<=p<=2e-8: raise ValueError('continuum equilibrium residual')
    for p,degree,rule in ((a,14,64),(b,18,80)):
        if (p['degree']!=degree or p['quadrature']!=rule or p['height']!=HEIGHT or p['force']!=list(FORCE)
                or p['inertia']!=INERTIA.tolist() or p['production_qualified'] is not False
                or p['external_hessian_policy']!='ZERO_FOR_ADDITIVE_SPATIAL_POSITION_VARIATION'
                or not 0<=p['residual']<=1e-8): raise ValueError('registered continuum spectral profile')
        # Reassemble the continuum operators, but do not solve a new eigenproblem.
        k,m,material,geometric,_=modal.build(state,INERTIA.tolist(),degree=degree,quadrature=rule)
        for name,value in (('stiffness',k),('mass',m),('material',material),('geometric',geometric)):
            if canonical(plain(value))!=canonical(p[name]): raise ValueError('continuum operator mutation')
        vectors=np.asarray(p['modes']); values=np.asarray(p['eigenvalues'])
        if vectors.shape!=(len(k),6) or values.shape!=(6,) or not np.isfinite(vectors).all() or not np.isfinite(values).all():
            raise ValueError('complete finite continuum modes')
        scale=np.maximum(1.,np.maximum(np.linalg.norm(material@vectors,axis=0),
            np.maximum(np.linalg.norm(geometric@vectors,axis=0),np.linalg.norm((m@vectors)*values,axis=0))))
        residual=float(np.max(np.linalg.norm(k@vectors-(m@vectors)*values,axis=0)/scale))
        if residual!=p['residual'] or residual>1e-8 or np.any(np.diff(values)<=0) or np.max(abs(vectors.T@m@vectors-np.eye(6)))>1e-11:
            raise ValueError('continuum eigenpair mutation')
    roots=np.asarray(b['eigenvalues']); coarse=np.asarray(a['eigenvalues'])
    profile=float(np.max(abs(roots-coarse)/np.maximum(1.,abs(roots))))
    if profile>1e-7: raise ValueError('continuum spectral resolution disagreement')
    rows=[]
    for m in (1,2,4):
        native=packets[f'native-{m}.json']; modes=native['modes']; state=packets[f'checkpoint-{m}.json']['records'][-1]
        if (modes['checkpoint_sha256']!=INPUTS[f'checkpoint-{m}.json'][2] or modes['equilibrium_load_parameter']!=1.
                or modes['external_potential_hessian_included'] is not True or modes['state_advanced'] is not False):
            raise ValueError('actual loaded native state required')
        detail={str(order):plain(overlap(m,modes['full_modes'],state,b,eq,order=order)) for order in (4,16,32)}
        if canonical(detail)!=canonical(packets[f'overlap-{m}.json']): raise ValueError('kinetic mode comparison changed')
        same=detail['4']; low=detail['16']; high=detail['32']
        identity=float(np.max(abs(np.asarray(same['native_mass_gram'])-np.eye(6))))
        reference_identity=float(np.max(abs(np.asarray(high['reference_mass_gram'])-np.eye(6))))
        mac_error=float(np.max(abs(np.asarray(low['material_frame_mac'])-np.asarray(high['material_frame_mac']))))
        if identity>1e-11 or reference_identity>1e-8 or mac_error>1e-8: raise ValueError('independent kinetic/profile checks')
        values=np.asarray(modes['eigenvalues']); positive=bool(np.min(values)>0 and np.min(roots)>0)
        rows.append(dict(macros=m,native_eigenvalues=values.tolist(),reference_eigenvalues=roots.tolist(),
            eigenvalue_relative_errors=(abs(values-roots)/np.maximum(1.,abs(roots))).tolist(),
            relative_frequency_errors=(abs(np.sqrt(values/roots)-1).tolist() if positive else None),
            native_negative_modes=int(np.count_nonzero(values<0)),reference_negative_modes=int(np.count_nonzero(roots<0)),
            diagonal_material_frame_mac=np.diag(high['material_frame_mac']).tolist(),
            native_rule_kinetic_identity_error=identity,reference_kinetic_identity_error=reference_identity,
            higher_rule_native_kinetic_quadrature_error=float(np.max(abs(np.asarray(high['native_mass_gram'])-np.eye(6)))),
            mac_quadrature_difference=mac_error,reference_resolution_error=profile,
            native_signed_ritz_residual=modes['original_ritz_residual'],reference_ritz_residual=b['residual']))
    return rows


def build(save,progress):
    original=bound_inputs(); packets={name:parse(raw) for name,raw in original.items()}
    for name,raw in original.items(): save(name,raw)
    samples={-1.,1.,*map(float,modal.sites(64)[0]),*map(float,modal.sites(80)[0])}
    for m in (1,2,4):
        for rule in (4,16,32): samples.update(row[6] for row in overlap_sites(m,rule))
    progress(dict(stage='CONTINUUM_EQUILIBRIUM',samples=len(samples)))
    eq=equilibrium.solve(reference_section().tolist(),list(FORCE),sorted(samples))
    packets['equilibrium.json']=plain(asdict(eq)); save('equilibrium.json',canonical(packets['equilibrium.json']))
    for degree,rule in ((14,64),(18,80)):
        progress(dict(stage='CONTINUUM_SPECTRUM',degree=degree))
        result=modal.solve(eq,INERTIA.tolist(),degree=degree,quadrature=rule)
        name=f'reference-{degree}.json'; packets[name]=plain(asdict(result)); save(name,canonical(packets[name]))
    for m in (1,2,4):
        progress(dict(stage='PRESERVED_NATIVE_COMPARISON',macros=m))
        state=packets[f'checkpoint-{m}.json']['records'][-1]; modes=packets[f'native-{m}.json']['modes']['full_modes']
        detail={str(rule):plain(overlap(m,modes,state,packets['reference-18.json'],packets['equilibrium.json'],order=rule)) for rule in (4,16,32)}
        name=f'overlap-{m}.json'; packets[name]=detail; save(name,canonical(detail))
    rows=recompute(packets)
    if bound_inputs()!=original: raise ValueError('preserved sources changed during comparison')
    return rows


def summary(output,revision):
    packets={}; artifacts=[]
    for name in ARTIFACTS:
        path=output/name
        if path.is_symlink() or not path.is_file(): raise ValueError('complete regular comparison artifacts required')
        raw=path.read_bytes(); packets[name]=parse(raw)
        artifacts.append(dict(path=name,bytes=len(raw),sha256=sha256(raw).hexdigest()))
    return dict(schema='GE_BEAM3_LINE_MODAL_REFERENCE_COMPARISON_V1',revision=revision,rows=recompute(packets),artifacts=artifacts,
        status='DEVELOPMENT_MODAL_COMPARISON_NOT_QUALIFICATION',production_qualified=False,independent_review='PENDING',
        new_native_spectra=0,new_native_nonlinear_solves=0,new_reference_equilibria=1,new_reference_spectra=2,
        comparison_policy='MATERIAL_FRAME_TRANSPORTED_KINETIC_MAC',clustered_mac_qualification=False,
        buckling_factor_authorized=False)
