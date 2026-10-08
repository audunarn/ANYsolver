"""Prepared saved-operator common-P0 action diagnostic. No execution on import.
No ANYsolver/OpenSees import, new mesh, global inverse or stiffness alteration.
Future execution requires root scheduling and independent pre-run review.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys

TEMP = Path(__file__).resolve().parent
WORKTREE = Path('C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling')
NATIVE = TEMP/'r8-bl5-native-p0-family-v1'
EXTERNAL = TEMP/'r8-bl5-external-p0-family-v1'
SEAMS = {
    '_ge_beam3_retained_generalized.py': '39121d4d76a5524579c2ea506c9bdf968a3d254cb7e6740de6173eb5aa7e6787',
    '_stiffened_shell_l1_local_experimental.py': 'ac954ee5aa9caa0a86b8b24f4f51726a5abd051b00dfcdebafc24fa7b74b35f6',
    '_stiffened_shell_bl5_local_experimental.py': '0389999a092bda04c03f5d860db23ccf4fb6a6deedb3fa52cc910e284a49e4e9',
    '_stiffened_shell_ge_experimental.py': '60da6cfc8c84f0f7bb3b18a0a9bf2ff748666a69f1772e03ebbf2ce300d91647',
}
COLLECTORS = {
    NATIVE/'b3_e4_bl5_matched_p0_native_refinement_dev.py': '143297217ec7a4851fb79f83155d23adce7d38971bc82760e94c82a5a1f83fd7',
    EXTERNAL/'b3_e4_bl5_external_p0_refinement_dev.py': '0e5435e0d38952642662eb1aad7dd374c341c866c9d099c87d2e66ce135a21c0',
}
WHEEL = '0c45666609355e654cb726a0e4e0780d386bccfaafef1209ffd994bdd3b9d09c'
LOADS = {'fy': (0.,100.,0.,0.,0.,0.), 'mx': (0.,0.,0.,10.,0.,0.), 'mz': (0.,0.,0.,0.,0.,10.)}
# Existing physical work/balance1e-8; prospective algebraic/map1e-10;
# self-replay roles1e-8. Common-action discrepancies have NO pass threshold.
MAP_TOL, PHYSICAL_TOL, REPLAY_TOL = 1e-10, 1e-8, 1e-8


class MappingError(RuntimeError): pass
class CompatibilityError(RuntimeError): pass
class ReplayError(RuntimeError): pass
class EquilibriumError(RuntimeError): pass


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())


def require(condition, message, error=MappingError):
    if not condition: raise error(message)


def write_json(path, value):
    temporary = path.with_suffix('.pending.json')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
    temporary.replace(path)


def maximum(a): return float(np.max(np.abs(a), initial=0.))


def relative(a, b, floor=1e-12):
    return maximum(a-b)/max(maximum(a), maximum(b), floor)


def matrix_error(a, b):
    return maximum((a-b).data)/max(maximum(a.data), maximum(b.data), 1e-12)


def csr(raw, name):
    return sparse.csr_matrix((raw[name+'_data'], raw[name+'_indices'], raw[name+'_indptr']),
                             shape=tuple(raw[name+'_shape']))


def native_C_from_trace(trace, layout, n):
    """Independent flat-frame derivative; every omitted/native retained slot kept."""
    m = 32
    rows, cols, vals = [], [], []
    support_measure = np.zeros(m)
    def add(row, slot, value):
        rows.append(row); cols.append(slot); vals.append(value)
    for sample in trace:
        reference = np.asarray(sample['shell_reference_m'])
        x = float((1.-sample['shell_alpha'])*reference[0,0]+sample['shell_alpha']*reference[1,0])
        j = min(int(x*m), m-1)
        ids = np.asarray(sample['multiplier_rows'], dtype=int)
        basis = np.asarray(sample['density_basis'])
        expected_ids = np.array([c*m+j for c in range(5)])
        require(np.array_equal(ids, expected_ids) and np.array_equal(basis, np.eye(5)),
                'saved density basis must prove channel-major physical P0, not rescaled lambda')
        p = sample['beam_port']; w = float(sample['measure_m'])
        require(w > 0. and np.array_equal(p['frame'],np.eye(3)) and np.array_equal(p['lift_m'],[0.,0.,0.])
                and np.array_equal(sample['reference_director'],[0.,0.,1.])
                and np.array_equal(sample['director_basis'],[[1.,0.,0.],[0.,1.,0.]])
                and sample['reference_arm_m']==[0.,0.,-.05] and sample['thickness_m']==.035,
                'only verified flat virgin frames/director/arms admitted')
        s = np.asarray(sample['full_slots'],dtype=int)
        member = layout['retained_members'][p['member_index']]
        cell = np.asarray(member['cell_rotation_slots'][3*p['native_cell']:3*p['native_cell']+3])
        require(len(s)==21 and np.array_equal(s[18:21],cell), 'actual retained cell rotation slots required')
        ns, nb = (1.-sample['shell_alpha'],sample['shell_alpha']), (1.-p['weight'],p['weight'])
        rs, rb = .0175, -.05
        for base, fraction in ((0,ns[0]),(6,ns[1])):
            for d in range(3): add(ids[d],s[base+d],w*fraction)
            add(ids[0],s[base+4],w*fraction*rs)
            add(ids[1],s[base+3],-w*fraction*rs)
            add(ids[3],s[base+4],w*fraction)
            add(ids[4],s[base+3],-w*fraction)
        for base,fraction in ((12,nb[0]),(15,nb[1])):
            for d in range(3): add(ids[d],s[base+d],-w*fraction)
        add(ids[0],s[19],-w*rb); add(ids[1],s[18],w*rb)
        add(ids[3],s[19],-w); add(ids[4],s[18],w)
        support_measure[j] += w
    require(len(trace)==256 and relative(support_measure,np.full(m,1./m))<=MAP_TOL,
            'complete union integration,32 supports of width1/32m required')
    return sparse.coo_matrix((vals,(rows,cols)),shape=(160,n)).tocsr(), support_measure


def rigid_maps(layout, xyz, n):
    """Independent six physical rigid fields, including all384 retained spins."""
    origin = xyz[len(layout['shell_node_ids'])]
    maps = {d: np.zeros((6,n)) for d in ('shell','beam')}
    for row in layout['typed_physical_nodes']:
        i = row['q_offset']; r = xyz[i//6]-origin; g = maps[row['domain']]
        g[:3,i:i+3] = np.eye(3)
        for d,omega in enumerate(np.eye(3)):
            g[d+3,i:i+3] = np.cross(omega,r)
            g[d+3,i+3:i+6] = omega
    for member in layout['retained_members']:
        for cell in range(2):
            slots = member['cell_rotation_slots'][3*cell:3*cell+3]
            maps['beam'][3:,slots] = np.eye(3)
    return maps


def external_C(raw, layout, n):
    typed = {row['external_node']:row['q_offset'] for row in layout['typed_physical_nodes']}
    require(len(typed)==1234, 'external disjoint IDs must map all typed physical nodes')
    rr, cc, vv = [], [], []
    for i,equation in enumerate(raw['equations']):
        require(len(equation)%3==0, 'flat equation triples required')
        for node,d,value in zip(equation[::3],equation[1::3],equation[2::3]):
            require(node in typed and 1<=d<=6, 'explicit external node/dof mapping required')
            rr.append(i); cc.append(typed[node]+d-1); vv.append(value)
    require(len(raw['equations'])==160, 'all external P0 rows required')
    return sparse.coo_matrix((vv,(rr,cc)),shape=(160,n)).tocsr()


def mapped_lambda(mu):
    require(np.asarray(mu).shape==(160,) and np.isfinite(mu).all(), 'finite external densities required')
    # External support-major -> native channel-major; no width division:
    # both coefficient arrays multiply integrated work rows, hence are densities.
    a = np.asarray(mu).reshape(32,5)
    return np.vstack((-a[:,:3].T,-a[:,4],a[:,3])).reshape(-1)


def external_vector(field, layout, n):
    out = np.zeros(n)
    for row in layout['typed_physical_nodes']:
        i = row['q_offset']; value = field[str(row['external_node'])]
        require(len(value)==6, 'full external6 covector/pose required')
        out[i:i+6] = value
    return out


def null_residual(K, rigid):
    # Rowwise absolute-contribution budget, preserving all quiet coordinates.
    r = K@rigid
    a = np.abs(K)@np.abs(rigid)
    require(not np.any((a==0.) & (r!=0.)), 'rigid residual on an exactly inactive row')
    return float(np.max(np.abs(r)/np.where(a>0.,a,1.),initial=0.))


def compatibility(rigid, rhs, scale):
    # 1rad normal spin and1m common-origin force-equivalent scale.
    dot = float(rigid@rhs)
    budget_scale = max(float(np.sum(np.abs(rigid*rhs))),float(np.linalg.norm(rhs*scale)),1e-12)
    return {'rigid_work_Nm':dot,'scale_Nm':budget_scale,'ratio':abs(dot)/budget_scale}


def equilibrium_ratio(residual, applied, scale):
    # Same load-based global/active-row criterion as frozen public linear owner.
    wr,wa=residual*scale,applied*scale
    magnitude=max(maximum(wr),maximum(wa))
    if magnitude==0.: return 0.
    denominator=float(np.linalg.norm(wa/magnitude))
    if denominator==0.: return float('inf')
    active=applied!=0.
    return max(float(np.linalg.norm(wr/magnitude))/denominator,
               maximum(residual[active]/applied[active]))


def field_report(q, reference, layout, domain):
    blocks = np.array([row['q_offset'] for row in layout['typed_physical_nodes'] if row['domain']==domain])
    a = q[blocks[:,None]+np.arange(6)]; b = reference[blocks[:,None]+np.arange(6)]
    report = {'norm_measure':'Unweighted Euclidean sampled nodal-vector norm; not integrated Q1/P1 L2'}
    for name,indices in [('translation_m',slice(0,3)),('rotation_rad',slice(3,6)),('combined_Lref1m',slice(0,6))]:
        x,y = a[:,indices],b[:,indices]
        report[name] = {'difference_vector_norm':float(np.linalg.norm(x-y)), 'reference_vector_norm':float(np.linalg.norm(y)),
                        'relative_vector_norm':float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-12)),
                        'difference_max_abs':maximum(x-y)}
    return report


def run(args):
    output = args.output_dir
    output.mkdir(parents=True,exist_ok=False)
    status = {'status':'failed','classification':'uncoupled native common-P0-action development control only',
              'source_sha256':sha(__file__),'nx':64,'cases':{},'bound_inputs':{},
              'runtime':{'python':sys.version,'threadpools':threadpool_info(),'product_or_numba_imports':False},
              'not_claimed':['1%convergence','locking acceptance','formalF03','new external solve','full coupled gauge removal']}
    def bind(path):
        status['bound_inputs'][str(path.resolve())] = sha(path)
    try:
        nr,er = NATIVE/'n64',EXTERNAL/'n64'
        for path,expected in COLLECTORS.items():
            bind(path); require(sha(path)==expected,'frozen collector source mismatch')
        identity=read(nr/'identity.json');bind(nr/'identity.json')
        require(identity['matching_modules']==388 and identity['wheel_sha256']==WHEEL,'saved product identity mismatch')
        for filename,expected in SEAMS.items():
            path=WORKTREE/'src/anysolver'/filename;bind(path)
            require(sha(path)==expected and identity['module_sha256']['anysolver/'+filename]==expected,
                    'current mechanics seam no longer equals frozen saved operator source')
        layout,inputs,trace = read(nr/'layout.json'),read(nr/'inputs.json'),read(nr/'station-traces.json')
        for name in ('layout.json','inputs.json','station-traces.json','operators.npz'):bind(nr/name)
        require(sha(nr/'operators.npz')==inputs['operators_sha256'],'saved operator binding mismatch')
        require(layout['nx']==64 and layout['ny']==16 and layout['halfcell_count']==128
                and layout['counts']['full_q']==8940 and layout['counts']['multipliers']==160,
                'only frozen finest native fixture admitted')
        with np.load(nr/'operators.npz',allow_pickle=False) as f:
            op={k:np.array(f[k],copy=True) for k in f.files}
        K,C=csr(op,'K'),csr(op,'C');n=K.shape[0];ns=6*len(layout['shell_node_ids'])
        scale=op['coordinate_scale'];xyz=np.asarray(inputs['xyz_m'])
        require(K.shape==(8940,8940) and C.shape==(160,8940) and np.isfinite(K.data).all()
                and np.isfinite(C.data).all() and np.isfinite(scale).all() and np.all(scale>0.),'finite full mixed operators required')
        require(maximum(K[:ns,ns:].data)==0. and maximum(K[ns:,:ns].data)==0.,'saved bulk domains must be uncoupled')
        require(matrix_error(K,K.T)<=MAP_TOL,'saved K skew exceeds existing inverse/eigen symmetry budget')
        independent,measures=native_C_from_trace(trace,layout,n)
        maps=rigid_maps(layout,xyz,n)
        status['premises']={'C_full_derivative_relative':matrix_error(C,independent),'support_measures_m':measures.tolist()}
        require(status['premises']['C_full_derivative_relative']<=MAP_TOL,'full independent virgin C derivative mismatch')
        for d in maps:
            require(relative(maps[d],op[d+'_rigid_work_map'])<=MAP_TOL,'all retained rigid-work map mismatch')
        fixed=set(map(int,op['fixed']));shell=np.arange(ns);beam=np.arange(ns,n)
        expectedfixed={row['q_offset']+d for row in layout['typed_physical_nodes']
            for d in range(6) if (row['domain']=='shell' and xyz[row['q_offset']//6,0]==0.)
            or (row['domain']=='beam' and row['native_node']==101 and d<5)}
        require(fixed==expectedfixed and np.array_equal(op['free'],np.array([i for i in range(n) if i not in fixed])),
                'unaltered full shell root / beam first5 supports and all other free coordinates required')
        # Reuse the already reviewed finite-family local nullspace premise;
        # no new local eigensolve or exact-certification claim.
        localpath=TEMP/'r8-bl5-local-kernel-v2/result.json';local=read(localpath);bind(localpath)
        require(sha(localpath)=='1d3ed66a7f1128254bc07d323d678ebca512af2dcd7662329752685d8447430f','reviewed local premise record changed')
        require(local['status']=='LOCAL_PREMISES_RESOLVED_DEVELOPMENT_ONLY'
            and all(local['predicates'].values()) and any(v['nx']==64 and v['halfcells']==128 for v in local['cases']),
            'reviewed same-geometry local-energy/nullspace prerequisite unavailable')
        eligible=[v for v in local['local_checks'] if v.get('beam') and
            np.array_equal(v['coordinates_m'],xyz[len(layout['shell_node_ids']):len(layout['shell_node_ids'])+3])]
        require(len(eligible)==1 and eligible[0]['local_premise_resolved'] and eligible[0]['negative_block_resolved']
            and eligible[0]['additional_unresolved_modes']==0,'matching native beam local6rigid/negative18 premise unresolved')
        root=next(row for row in layout['typed_physical_nodes'] if row['domain']=='beam' and row['native_node']==101)
        gauge=root['q_offset']+5;r=maps['beam'][5]
        require(gauge not in fixed and set(range(root['q_offset'],gauge))<=fixed and r[gauge]==1.
                and maximum(r[list(fixed)])==0.,'proven root-first5/free-normal-spin support map required')
        require(len(layout['retained_members'])==64 and all(m['beam_nodes']==[101+2*i,102+2*i,103+2*i]
            for i,m in enumerate(layout['retained_members'])),'connected native member chain required')
        rigid_K={d:[null_residual(K,g[c]) for c in range(6)] for d,g in maps.items()}
        require(all(v<=MAP_TOL for values in rigid_K.values() for v in values),'bulk six-rigid-field work premise failed')
        status['premises']['six_bulk_rigid_K_ratios']=rigid_K
        null_error=null_residual(K,r)
        require(null_error<=MAP_TOL,'native isolated rigid Mz mode not annihilated by full retained K')
        status['premises'].update({'isolated_normal_spin_K_ratio':null_error,'gauge_coordinate':gauge,
           'nullspace_scope':'Source positive section + connected native local6rigid/negative18 structure, root5 constraints leave only1 spin; nominal numerical corroboration, no exact PSD certificate.'})
        prepared={}
        for case in args.cases:
            nc,ec=nr/case,er/case
            for path in (nc/'raw-state.npz',nc/'raw-state.json',nc/'physical-actions.json',ec/'raw-inventory.json',ec/'recovered-actions.json',ec/'summary.json'):bind(path)
            require(sha(nc/'raw-state.npz')==read(nc/'raw-state.json')['arrays_sha256'],'native detached-state binding mismatch')
            with np.load(nc/'raw-state.npz',allow_pickle=False) as f:
                saved={k:np.array(f[k],copy=True) for k in f.files}
            raw,actions=read(ec/'raw-inventory.json'),read(ec/'recovered-actions.json')
            CE=external_C(raw,layout,n);mu=np.asarray(actions['row_density_multipliers']);lam=mapped_lambda(mu)
            require(len(actions['support_records'])==32,'complete external32-support density inventory required')
            for j,support in enumerate(actions['support_records']):
                require(support['support_id']==j and support['interval_m']==[j/32.,(j+1)/32.]
                    and np.array_equal(support['density_N_per_m_Nm_per_m'],mu[5*j:5*j+5]),
                    'external support-major physical density/measure identity mismatch')
            extq=external_vector(raw['poses'],layout,n);extG=external_vector({**actions['shell_domain_nodal_G'],**actions['beam_domain_nodal_G']},layout,n)
            extC=external_vector(actions['connection_resisting_C_transpose_lambda'],layout,n)
            externalL=external_vector(actions['applied_nodal_L'],layout,n)
            for row in layout['typed_physical_nodes']:
                i=row['q_offset'];node=row['external_node']
                require(np.array_equal(raw['nodes'][str(node)],xyz[i//6]),'typed physical geometry mismatch')
                flags=[int(i+d in fixed) for d in range(6)]
                require(flags==raw['fixes'].get(str(node),[0]*6),'physical support mismatch')
            tip=layout['typed_physical_nodes'][-1]['q_offset']
            expectedL=np.zeros(n);expectedL[tip:tip+6]=LOADS[case]
            require(np.array_equal(saved['load'],expectedL) and np.array_equal(externalL,expectedL),'same physical RHS required')
            cn=C.T@lam;cnself=C.T@saved['multipliers'];ce=CE.T@mu
            # Complete160 basis actions, including fixed coordinates, independently verify shell equivalence.
            T=sparse.coo_matrix((np.tile([-1.,-1.,-1.,-1.,1.],32),
                ([c*32+j for j in range(32) for c in range(5)],
                 [5*j+c for j in range(32) for c in (0,1,2,4,3)])),shape=(160,160)).tocsr()
            shellbasis=matrix_error((C.T@T)[:ns,:],CE.T[:ns,:])
            rigidbasis={d:relative(maps[d]@(C.T@T),maps[d]@CE.T) for d in maps}
            checks={'external_full_transpose_recovery':relative(ce,extC),'native_full_transpose_recovery':relative(cnself,saved['constraint_resisting']),
                    'common_shell_all160_basis':shellbasis,'common_rigid_all160_basis':rigidbasis,
                    'combined6rigid_zero':maximum((maps['shell']+maps['beam'])@cn),
                    'combined_all160_basis_zero':maximum((maps['shell']+maps['beam'])@(C.T@T))/(1./32.),
                    'external_stationarity_free':relative((extG+extC-externalL)[op['free']],np.zeros(len(op['free'])),floor=max(maximum(externalL),1.))}
            # Store every input/action before admission failures; no future solve yet.
            np.savez_compressed(output/(case+'-prepared.npz'),q_saved=saved['q'],native_lambda=saved['multipliers'],external_mu=mu,mapped_native_lambda=lam,
                 load=expectedL, native_constraint_resisting=cnself,common_constraint_resisting=cn,external_constraint_resisting=ce,
                 external_q=extq,external_G=extG,external_C_recorded=extC,rigid_normal_spin=r,coordinate_scale=scale)
            status['cases'][case]={'mapping_checks':checks,'status':'mapping_not_yet_admitted'}
            write_json(output/'result.json',status)
            require(checks['external_full_transpose_recovery']<=MAP_TOL and checks['native_full_transpose_recovery']<=MAP_TOL
                    and shellbasis<=MAP_TOL and all(v<=MAP_TOL for v in rigidbasis.values())
                    and checks['combined_all160_basis_zero']<=MAP_TOL,'unverified physical P0 basis/work map')
            selfrhs=expectedL-cnself;commonrhs=expectedL-cn
            compat={name:compatibility(r,rhs,scale) for name,rhs in [('native_self',selfrhs),('external_common',commonrhs)]}
            status['cases'][case]={'mapping_checks':checks,'compatibility':compat,'status':'prepared'}
            write_json(output/'result.json',status)
            require(all(v['ratio']<=PHYSICAL_TOL for v in compat.values()),'isolated beam normal-spin loading incompatible',CompatibilityError)
            require(checks['external_stationarity_free']<=PHYSICAL_TOL,'saved external isolated response failed stationarity',EquilibriumError)
            prepared[case]=(saved,extq,extG,extC,cnself,cn,selfrhs,commonrhs)
        require(not any(name=='anysolver' or name.startswith('anysolver.') for name in sys.modules),'product import forbidden')
        if args.screen_only:
            status['status']='PREPARED_NO_FACTORIZATION';write_json(output/'result.json',status);return
        factors={}
        for domain,indices in [('shell',shell),('beam',beam)]:
            free=np.array([i for i in indices if i not in fixed and (domain!='beam' or i!=gauge)],dtype=int)
            D=sparse.diags(scale[free]);matrix=(D@K[free,:][:,free]@D).tocsc()
            # Unaltered indefinite mixed equations; diagonal congruence, no SPD assumption.
            factors[domain]=(free,splu(matrix),indices)
        status['factorizations']=2
        for case,(saved,extq,extG,extC,cnself,cn,selfrhs,commonrhs) in prepared.items():
            for name,rhs,connection,reference in [('native_self',selfrhs,cnself,saved['q']),('external_common',commonrhs,cn,extq)]:
                q=np.zeros(n)
                for domain,(free,factor,indices) in factors.items():
                    q[free]=scale[free]*factor.solve(scale[free]*rhs[free])
                    # One unchanged-equation correction, no tolerance or model adaptation.
                    q[free]+=scale[free]*factor.solve(scale[free]*(rhs-K@q)[free])
                G=K@q;residual=G-rhs;gauge_reaction=float(residual[gauge])
                q_gauge_zero=q.copy()
                q+=r*reference[gauge]  # borrowed reference yaw: isolated quotient, NOT a coupled yaw prediction
                G=K@q;residual=G-rhs
                ground=np.zeros(n);ground[list(fixed)]=residual[list(fixed)]
                weak_gaps=C@q
                np.savez_compressed(output/(case+'-'+name+'.npz'),q=q,rhs=rhs,load=saved['load'],Kq=G,
                    constraint_resisting=connection,physical_ground=ground,gauge_reaction=np.array(gauge_reaction),residual=residual,
                    q_reference=reference,q_gauge_zero=q_gauge_zero,weak_gaps=weak_gaps,
                    external_G=extG,fixed=op['fixed'],free_original=op['free'])
                roles={}
                for domain in ('shell','beam'):roles[domain]=field_report(q,reference,layout,domain)
                eq=equilibrium_ratio(residual[op['free']],rhs[op['free']],scale[op['free']])
                gauge_ratio=abs(gauge_reaction)/max(maximum(rhs*scale),1e-12)
                work=float(q@(K@q));rhswork=float(q@rhs)
                entry={'free_equilibrium_ratio':eq,'gauge_reaction_Nm':gauge_reaction,'gauge_reaction_ratio':gauge_ratio,
                    'borrowed_yaw_quotient_alignment_rad':float(reference[gauge]),
                    'yaw_role':'Isolated-yaw quotient aligned to saved reference; not a coupled yaw prediction',
                    'internal_work_J':work,'rhs_work_J':rhswork,
                    'internal_work_meaning':'q.T K q; twice elastic energy at stationary elastic state',
                    'weak_gap_diagnostics_only':{'integrated_translation_gap_max_m2':maximum(weak_gaps[:96]),
                        'integrated_director_gap_max_m':maximum(weak_gaps[96:]),
                        'average_translation_gap_max_m':maximum(weak_gaps[:96])/(1./32.),
                        'average_director_gap_max_rad':maximum(weak_gaps[96:])/(1./32.),
                        'fixed_row_work_scaled_max':maximum(weak_gaps/op['constraint_scale']),
                        'role':'No coupled-state admission predicate; isolated common-action states may violate Cq=0'},
                    'internal_work_rhs_relative':abs(work-rhswork)/max(abs(work),abs(rhswork),1e-12),'fields':roles,'domain_cuts':{}}
                for domain in maps:
                    entry['domain_cuts'][domain]={'internal_G':(maps[domain]@G).tolist(),'constraint_resisting':(maps[domain]@connection).tolist(),
                        'physical_ground':(maps[domain]@ground).tolist(),'applied_L':(maps[domain]@saved['load']).tolist()}
                    slots=shell if domain=='shell' else beam
                    entry['domain_cuts'][domain]['work_J']={
                        'native_internal':float(q[slots]@G[slots]),'native_applied':float(q[slots]@saved['load'][slots]),
                        'native_connection_exerted':float(-q[slots]@connection[slots]),
                        'zero_yaw_applied':float(q_gauge_zero[slots]@saved['load'][slots]),
                        'zero_yaw_connection_exerted':float(-q_gauge_zero[slots]@connection[slots]),
                        'borrowed_yaw_applied_increment':float((q-q_gauge_zero)[slots]@saved['load'][slots]),
                        'borrowed_yaw_connection_exerted_increment':float(-(q-q_gauge_zero)[slots]@connection[slots]),
                        'borrowed_yaw_net_RHS_increment':float((q-q_gauge_zero)[slots]@rhs[slots]),
                        'work_gauge_role':'Applied/interface work separately depends on isolated yaw; compatible net RHS/internal work is invariant within checked residual budget',
                        'native_rhs':float(q[slots]@rhs[slots]),
                        'reference_internal':float(reference[slots]@(saved['Kq'] if name=='native_self' else extG)[slots]),
                        'reference_applied':float(reference[slots]@saved['load'][slots]),
                        'reference_connection_exerted':float(-reference[slots]@(cnself if name=='native_self' else extC)[slots])}
                if name=='native_self':
                    entry['full_q_roles_relative']={
                        'physical':relative(q[:layout['counts']['physical_dofs']],reference[:layout['counts']['physical_dofs']]),
                        'cell_rotations':relative(q[[i for m in layout['retained_members'] for i in m['cell_rotation_slots']]],reference[[i for m in layout['retained_members'] for i in m['cell_rotation_slots']]]),
                        'resultants_Lref1m':relative(q[[i for m in layout['retained_members'] for i in m['resultant_slots']]],reference[[i for m in layout['retained_members'] for i in m['resultant_slots']]]),
                        'all_internal_G':relative(G,saved['Kq'])}
                else:
                    entry['root_components']={}
                    # Interior retained Theta is not a nodal root boundary value.
                    retained_slots=[];external_cell_means=[]
                    typed={(v['domain'],v['native_node']):v['q_offset'] for v in layout['typed_physical_nodes']}
                    for member in layout['retained_members']:
                        retained_slots.extend(member['cell_rotation_slots'])
                        for left,right in zip(member['beam_nodes'][:-1],member['beam_nodes'][1:]):
                            a,b=typed['beam',left],typed['beam',right]
                            external_cell_means.extend(.5*(extq[a+3:a+6]+extq[b+3:b+6]))
                    extcell=np.asarray(external_cell_means);theta=q[retained_slots]
                    entry['retained_cell_vs_external_P1_mean_rad']={'norm_measure':'Unweighted384-component retained-cell vector norm; not integrated L2',
                        'difference_vector_norm':float(np.linalg.norm(theta-extcell)),
                        'external_vector_norm':float(np.linalg.norm(extcell)),'difference_max':maximum(theta-extcell)}
                    for row in layout['typed_physical_nodes']:
                        i=row['q_offset']
                        if any(i+d in fixed for d in range(6)):
                            key=row['domain']+':'+str(row['native_node'])
                            entry['root_components'][key]={'native_G':G[i:i+6].tolist(),'external_G':extG[i:i+6].tolist(),
                                'native_C':connection[i:i+6].tolist(),'external_C':extC[i:i+6].tolist(),
                                'external_physical_ground':(extG+extC-saved['load'])[i:i+6].tolist(),
                                'physical_ground':ground[i:i+6].tolist()}
                status['cases'][case][name]=entry;write_json(output/'result.json',status)
                require(eq<=PHYSICAL_TOL and gauge_ratio<=PHYSICAL_TOL and entry['internal_work_rhs_relative']<=PHYSICAL_TOL,
                        'isolated stationary solve/gauge/work failed',EquilibriumError)
                if name=='native_self':require(all(v<=REPLAY_TOL for v in entry['full_q_roles_relative'].values()),'native action self-replay failed',ReplayError)
            status['cases'][case]['status']='completed_observables_no_accuracy_acceptance'
        status['status']='COMPLETED_DEVELOPMENT_ONLY'
    except BaseException as exc:
        status['exception']={'type':type(exc).__name__,'message':str(exc)}
        raise
    finally:
        status['no_product_reference_imports']=not any(name=='anysolver' or name.startswith(('anysolver.','openseespy')) for name in sys.modules)
        write_json(output/'result.json',status)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--cases',nargs='+',choices=tuple(LOADS),default=['fy'])
    p.add_argument('--screen-only',action='store_true',help='all mappings/load compatibility; NO factorization or solve')
    args=p.parse_args();require(len(args.cases)==len(set(args.cases)),'no repeated case permitted')
    for key in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[key]='1'
    os.environ['NUMBA_DISABLE_JIT']='1'
    global np,sparse,splu,threadpool_info
    import numpy as np
    from scipy import sparse
    from scipy.sparse.linalg import splu
    from threadpoolctl import threadpool_info
    pools=threadpool_info();require(pools and all(x['num_threads']==1 for x in pools),'one effective BLAS thread required')
    run(args)


if __name__=='__main__':main()
