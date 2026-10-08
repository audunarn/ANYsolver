"""Saved-observable checks for the bounded classical joint-refinement study.

No mechanical assembly or equilibrium solve belongs in adjudication.
Signed physical channels remain separate; small denominators have explicit
physical floors. A refinement screen is not a continuum error estimate.
"""

from __future__ import annotations

import math
import numpy as np

from _b3_e4_f03_kkt_scaling import E0, F0, M0, U0

FAMILIES=('P1','hybrid','enriched')
LIMITS={'free_residual_scaled':1e-8,'weak_gap_scaled':1e-9,
        'balance_scaled_absolute_max':1e-8,'energy_scaled':1e-8,
        'enriched_energy_order_scaled':1e-8,
        'structural_solve_relative_residual':1e-8,
        'nonpositive_schur_modes':0,'parent_state_parity_ratio':1.,
        'parent_observable_parity_ratio':1.}


def finite(value, shape, name):
    array=np.asarray(value,dtype=float)
    if array.shape!=shape or not np.all(np.isfinite(array)):
        raise ValueError(f'invalid finite {name}')
    return array


def channels(row):
    """Fixed physical observables, values and denominator floors in SI units."""
    result={}
    def add(name,value,scale):
        if not math.isfinite(value):
            raise ValueError(f'nonfinite physical channel {name}')
        result[name]={'value':float(value),'floor':float(1e-3*scale)}
    for i,x in enumerate(finite(row['tip_pose_m'],(3,),'tip pose')):
        add(f'tip_pose_m/{i}',x,U0)
    for key in ('support_wrenches','line_quarter_wrenches','physical_quarter_wrenches'):
        shape=(3,3) if key=='support_wrenches' else (4,3)
        for ij in np.ndindex(shape):
            add(f'{key}/{ij[0]}/{ij[1]}',finite(row[key],shape,key)[ij],
                M0 if ij[1]==2 else F0)
    for key in ('root_elastic_wrench','root_port_wrench','root_load_wrench',
                'root_line_wrench','root_endpoint_wrench'):
        for i,x in enumerate(finite(row[key],(3,),key)):
            add(f'{key}/{i}',x,M0 if i==2 else F0)
    for ij in np.ndindex((2,3)):
        # Third atom is conjugate to the length-scaled angle, so is in N.
        add(f'endpoint_atoms/{ij[0]}/{ij[1]}',
            finite(row['endpoint_atoms'],(2,3),'endpoint atoms')[ij],F0)
        add(f'endpoint_gaps_m/{ij[0]}/{ij[1]}',
            finite(row['endpoint_gaps_m'],(2,3),'endpoint gaps')[ij],U0)
    for key in ('shell_energy_j','beam_energy_j'):
        add(key,row[key],E0)
    from _b3_e4_f03_joint_refinement_observables import BANDS
    if len(row['fixed_bands'])!=len(BANDS):
        raise ValueError('fixed-band inventory mismatch')
    for j,band in enumerate(row['fixed_bands']):
        if band['interval_m']!=list(BANDS[j]):
            raise ValueError('fixed-band physical interval mismatch')
        for key in ('line_wrench','total_wrench'):
            for i,x in enumerate(finite(band[key],(3,),'band wrench')):
                add(f'fixed_bands/{j}/{key}/{i}',x,M0 if i==2 else F0)
    add('stored_energy_j',row['shell_energy_j']+row['beam_energy_j'],E0)
    add('gap_l2_m',row['gap_l2_m'],U0)
    add('combined_dual_norm_N',row['combined_dual_norm_N'],F0)
    return result


def measurements(data,spec,norm_identities):
    """Recompute work/balance, layout and norm-identity predicates."""
    if (data['topology']!=spec['topology'] or data['halfwidth_m']!=.05 or
            data['mesh']!=[spec[k] for k in ('n_s','n_y','n_beam','n_mortar')] or
            set(data['families'])!=set(FAMILIES)):
        raise ValueError('case physical contract mismatch')
    outcome={key:0. for key in LIMITS}
    energies={}
    for family in FAMILIES:
        row=data['families'][family]
        channels(row)
        rms=finite(row['gap_channel_rms_m'],(3,),'gap channel RMS')
        motion=finite(row['motion_channel_rms_m'],(3,),'motion channel RMS')
        if (np.any(rms<0) or np.any(motion<0) or
                not math.isclose(float(np.linalg.norm(rms)),row['gap_rms_m'],rel_tol=1e-12,abs_tol=1e-18) or
                not math.isclose(float(np.linalg.norm(motion)),row['motion_rms_m'],rel_tol=1e-12,abs_tol=1e-18) or
                not math.isclose(row['gap_rms_m'],row['gap_l2_m'],rel_tol=1e-10,abs_tol=1e-18)):
            raise ValueError('RMS aggregation mismatch')
        from _b3_e4_f03_joint_refinement_observables import fixed_bands
        if row['fixed_bands']!=fixed_bands(row['physical_line_coefficients'],row['endpoint_atoms']):
            raise ValueError('fixed-band recovery mismatch')
        finite(row['physical_line_coefficients'],(spec['n_mortar']+1,3),'line density')
        support=finite(row['support_wrenches'],(3,3),'supports')
        balance=support.sum(axis=0)/[F0,F0,M0]+[0.,1.,.5]
        partition=np.asarray(row['root_elastic_wrench'])+row['root_port_wrench']-np.asarray(row['root_load_wrench'])
        port=np.asarray(row['root_line_wrench'])+row['root_endpoint_wrench']
        if (not np.allclose(partition,support[2],rtol=1e-10,atol=1e-5) or
                not np.allclose(port,row['root_port_wrench'],rtol=1e-10,atol=1e-5) or
                not np.allclose(balance,row['balance_scaled'],rtol=1e-10,atol=1e-12)):
            raise ValueError('physical reaction partition mismatch')
        energies[family]=row['shell_energy_j']+row['beam_energy_j']
        energy=abs(2*energies[family]+row['interface_work_j']-row['external_work_j'])/E0
        if not math.isclose(energy,row['energy_scaled'],rel_tol=1e-10,abs_tol=1e-12):
            raise ValueError('energy identity mismatch')
        diag=row['stability']
        if (diag['norm_source']!='analytic_h1' or
                diag['norm_identity']!=norm_identities[family] or
                diag['auxiliary_status']!='PIECEWISE_ANALYTIC_FLOATING' or
                'auxiliary_squared_norm_change' in diag):
            raise ValueError('analytic norm contract mismatch')
        count=3*(spec['n_mortar']+(3 if family=='enriched' else 1))
        eig=finite(diag['generalized_eigenvalues'],(count,),'Schur spectrum')
        if np.any(np.diff(eig)<0):
            raise ValueError('unordered Schur spectrum')
        expected_beta=math.sqrt(eig[0]) if eig[0]>0 else None
        if diag['minimum_beta_diagnostic']!=expected_beta:
            raise ValueError('Schur minimum inconsistent with saved spectrum')
        current={'free_residual_scaled':row['free_residual_scaled'],
                 'weak_gap_scaled':row['weak_gap_scaled'],
                 'balance_scaled_absolute_max':float(np.max(np.abs(balance))),
                 'energy_scaled':energy,
                 'structural_solve_relative_residual':diag['structural_solve_relative_residual'],
                 'nonpositive_schur_modes':int(np.count_nonzero(eig<=0))}
        for key,value in current.items():
            if not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
                raise ValueError('invalid numerical metric')
            outcome[key]=max(outcome[key],value)
    order=max(0.,energies['enriched']-energies['P1'],energies['enriched']-energies['hybrid'])/E0
    if not math.isclose(order,data['enriched_energy_order_scaled'],rel_tol=1e-10,abs_tol=1e-12):
        raise ValueError('enriched energy ordering mismatch')
    outcome['enriched_energy_order_scaled']=order
    parity=data['parent_state_parity_ratio']
    if not math.isfinite(parity) or parity<0:
        raise ValueError('invalid parent parity')
    outcome['parent_state_parity_ratio']=parity
    parity=data['parent_observable_parity_ratio']
    if not math.isfinite(parity) or parity<0:
        raise ValueError('invalid parent observable parity')
    outcome['parent_observable_parity_ratio']=parity
    return outcome


def bind_physical_multipliers(row,family,n,lam,gram):
    """Bind recovery coefficients and work norm to the owned physical state."""
    count=3*(n+(3 if family=='enriched' else 1))
    lam=finite(lam,(count,),'physical multiplier state')
    density=np.zeros((n+1,3)); atoms=np.zeros((2,3))
    if family=='P1':
        density[:]=lam.reshape(n+1,3)
        measures=np.repeat(np.r_[.5/n,np.full(n-1,1/n),.5/n],3)
    elif family=='hybrid':
        density[1:-1]=lam[:-6].reshape(n-1,3)
        atoms[:]=lam[-6:].reshape(2,3)
        measures=np.r_[np.full(3*(n-1),1/n),np.ones(6)]
    else:
        density[:]=lam[:-6].reshape(n+1,3)
        atoms[:]=lam[-6:].reshape(2,3)
        measures=np.r_[np.repeat(np.r_[.5/n,np.full(n-1,1/n),.5/n],3),np.ones(6)]
    if (not np.array_equal(density,row['physical_line_coefficients']) or
            not np.array_equal(atoms,row['endpoint_atoms'])):
        raise ValueError('recovered coefficients do not match saved physical multipliers')
    from _b3_e4_f03_joint_refinement_observables import fixed_bands
    quarters=fixed_bands(density,atoms,[(i/4,(i+1)/4) for i in range(4)])
    for key,field in (('line_quarter_wrenches','line_wrench'),
                      ('physical_quarter_wrenches','total_wrench')):
        if not np.allclose(row[key],[q[field] for q in quarters],rtol=1e-12,atol=1e-7):
            raise ValueError('quarter wrenches disagree with saved multipliers')
    physical_normalized=lam*measures
    squared=float(physical_normalized@gram@physical_normalized)
    if (not math.isfinite(squared) or squared<0 or
            not math.isclose(math.sqrt(squared),row['combined_dual_norm_N'],rel_tol=1e-12,abs_tol=1e-7)):
        raise ValueError('dual action does not match saved physical multipliers')


def compare(first,second):
    """Signed before/after values plus symmetric, floor-protected change."""
    a=channels(first); b=channels(second)
    result={}
    for key,x in a.items():
        y=b[key]
        result[key]={'first':x['value'],'second':y['value'],'floor':x['floor'],
                     'signed_delta':y['value']-x['value'],
                     'relative_change':abs(y['value']-x['value'])/
                         max(abs(x['value']),abs(y['value']),x['floor'])}
    return result


def functional_difference(first,second):
    """Compare entire line-density plus endpoint-atom actions in the same norm."""
    from _b3_e4_f03_trace_dual_exact import dual_gram
    arrays=[]
    for row in (first,second):
        density=np.asarray(row['physical_line_coefficients'],dtype=float)
        n=len(density)-1
        finite(density,(n+1,3),'functional density')
        if n not in (4,8,16):
            raise ValueError('functional layout outside registered mesh inventory')
        arrays.append((density,finite(row['endpoint_atoms'],(2,3),'functional atoms')))
    target=max(len(x[0])-1 for x in arrays)
    coefficients=[]
    for density,atoms in arrays:
        while len(density)-1<target:
            refined=np.empty((2*(len(density)-1)+1,3))
            refined[::2]=density
            refined[1::2]=(density[:-1]+density[1:])/2
            density=refined
        measures=np.r_[.5/target,np.full(target-1,1/target),.5/target,1.,1.]
        coefficients.append(measures[:,None]*np.vstack((density,atoms)))
    gram=dual_gram(target,'enriched')
    def norm(coeff):
        squared=float(np.sum(coeff*(gram@coeff)))
        if not math.isfinite(squared) or squared<0:
            raise ValueError('invalid dual functional quadratic form')
        return math.sqrt(squared)
    a,b=coefficients
    na=norm(a); nb=norm(b); difference=norm(b-a)
    return {'first_norm_N':na,'second_norm_N':nb,'difference_N':difference,
            'relative_difference':difference/max(na,nb,1e-3*F0),
            'denominator_floor_N':1e-3*F0}


def screened_channel(name):
    return (name.startswith(('tip_pose_m/','support_wrenches/2/',
                             'endpoint_atoms/','physical_quarter_wrenches/')) or
            (name.startswith('fixed_bands/') and '/total_wrench/' in name) or
            name in ('shell_energy_j','beam_energy_j','stored_energy_j'))


def common_channel(name):
    return screened_channel(name) and not name.startswith('endpoint_atoms/')


def common_comparison(first,second):
    changes=compare(first,second)
    functional=functional_difference(first,second)
    passed=(all(v['relative_change']<=.01 for key,v in changes.items() if common_channel(key))
            and functional['relative_difference']<=.01)
    return {'channels':changes,'full_functional_difference':functional,
            'common_screen_passed':passed}


def refinement_summary(cases):
    """All channels are retained, including near-zero and partition channels."""
    result={}
    for prefix in ('q4','cst_cb'):
        for family in FAMILIES:
            rows=[cases[f'{prefix}_{level}']['families'][family]
                  for level in ('coarse','middle','fine')]
            pairs=[compare(rows[0],rows[1]),compare(rows[1],rows[2])]
            functional=[functional_difference(rows[0],rows[1]),
                        functional_difference(rows[1],rows[2])]
            screen={}
            for key in pairs[0]:
                if screened_channel(key):
                    first=pairs[0][key]; last=pairs[1][key]
                    screen[key]={'last_change_below_one_percent':last['relative_change']<=.01,
                        'absolute_change_contracts':abs(last['signed_delta'])<=
                            abs(first['signed_delta'])+.01*last['floor']}
            screen['full_multiplier_functional']={
                'last_change_below_one_percent':functional[1]['relative_difference']<=.01,
                'absolute_change_contracts':functional[1]['difference_N']<=
                    functional[0]['difference_N']+1e-5*F0}
            middle,fine=rows[1:]
            denominator=max(fine['motion_rms_m'],1e-3*U0)
            endpoint=float(np.max(np.abs(fine['endpoint_gaps_m'])))
            screen['gaps']={
                'rms_below_one_percent_motion':fine['gap_rms_m']/denominator<=.01,
                'endpoint_below_one_percent_motion':endpoint/denominator<=.01,
                'rms_does_not_increase':fine['gap_rms_m']<=middle['gap_rms_m']+1e-5*U0,
                'endpoint_does_not_increase':endpoint<=float(np.max(np.abs(middle['endpoint_gaps_m'])))+1e-5*U0}
            if family=='P1':
                screen={k:v for k,v in screen.items() if not k.startswith('endpoint_atoms/')}
            result[f'{prefix}/{family}']={'adjacent_pairs':pairs,
                'full_functional_differences':functional,'physical_trend_screen':screen,
                'trend_status':('SETTLED_ON_REGISTERED_LEVELS' if
                    all(all(v.values()) for v in screen.values()) else 'UNSETTLED_REFINEMENT'),
                'beta_sequence':[row['stability']['minimum_beta_diagnostic'] for row in rows],
                'scope':'descriptive three-level changes; not an error estimate or continuum stability proof'}
    for family in FAMILIES:
        result[f'cross_topology/{family}']={level:common_comparison(
            cases[f'q4_{level}']['families'][family],
            cases[f'cst_cb_{level}']['families'][family])
            for level in ('coarse','middle','fine')}
    for prefix in ('q4','cst_cb'):
        result[f'cross_family/{prefix}']={f'{a}/{b}':common_comparison(
            cases[f'{prefix}_fine']['families'][a],cases[f'{prefix}_fine']['families'][b])
            for a,b in (('P1','hybrid'),('P1','enriched'),('hybrid','enriched'))}
    passed=(all(result[f'{prefix}/{family}']['trend_status']=='SETTLED_ON_REGISTERED_LEVELS'
                for prefix in ('q4','cst_cb') for family in FAMILIES) and
            all(result[f'cross_topology/{family}']['fine']['common_screen_passed'] for family in FAMILIES) and
            all(v['common_screen_passed'] for prefix in ('q4','cst_cb')
                for v in result[f'cross_family/{prefix}'].values()))
    result['status']='PASSED_BOUNDED_TREND_SCREEN' if passed else 'UNRESOLVED_JOINT_REFINEMENT'
    return result
