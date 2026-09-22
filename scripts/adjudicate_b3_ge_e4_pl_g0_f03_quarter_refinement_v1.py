"""Read-only reconstruction of a registered F03 first-quarter natural sweep.

No factorization or solve is performed. This classical comparator is neither
an external physical reference nor a native mixed-workflow qualification.
"""

from __future__ import annotations

import argparse
from dataclasses import fields
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import traceback

import numpy as np
from scipy import sparse

import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_inventory as inventory
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling
import _b3_e4_f03_loaded_preflight as loaded
import b3_e4_f03_resource_preflight as runner


TRIPLES=((128,16,64),(128,32,64),(128,64,64),
         (32,64,64),(64,64,64),(128,64,16),(128,64,32))
CASES=tuple((ns,ny,nm,topology) for ns,ny,nm in TRIPLES
            for topology in ('Q4','CST-CB'))
Y_EDGES=(-.5,-.25,0.,.25,.5)
S_EDGES=tuple(i/32 for i in range(9))
CENTERS=tuple((i+.5)/32 for i in range(8))


def case_name(ns: int, ny: int, nm: int, topology: str) -> str:
    return (f'f03-quarter-ns{ns}-ny{ny}-nm{nm}-'
            f'{"q4" if topology=="Q4" else "cb"}-v1')


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(root: Path) -> tuple[dict,list[dict],dict]:
    return (json.loads((root/'manifest.json').read_text(encoding='utf-8')),
            [json.loads(row) for row in (root/'phases.jsonl').read_text(
                encoding='utf-8').splitlines()],
            json.loads((root/'result.json').read_text(encoding='utf-8')))


def _wrench(dual: np.ndarray, nodes: np.ndarray) -> np.ndarray:
    return np.array((dual[::2].sum(),dual[1::2].sum(),
                     nodes[:,0]@dual[1::2]-nodes[:,1]@dual[::2]))


def _port_interval(lam: np.ndarray, nm: int, a: float, b: float,
                   overlay: np.ndarray) -> np.ndarray:
    """Integrate force, eccentric moment and couple over the physical interval."""
    knots=sorted(set([a,b]+[float(k) for k in overlay if a<k<b]+
                     [i/nm for i in range(nm+1) if a<i/nm<b]))
    roots,weights=np.polynomial.legendre.leggauss(2)
    total=np.zeros(4)
    for lower,upper in zip(knots[:-1],knots[1:]):
        for root,weight in zip(roots,weights):
            s=(lower+upper)/2+(upper-lower)*root/2
            density=sum(test*lam[3*i:3*i+3]
                        for i,test in line.mortar_tests(nm,'P1',s))
            total+=(upper-lower)*weight/2*np.array(
                (density[0],density[1],s*density[1],line.YAW_LENGTH*density[2]))
    return total


def _port_bands(lam: np.ndarray, nm: int,
                overlay: np.ndarray) -> tuple[list,list]:
    first=[_port_interval(lam,nm,a,b,overlay).tolist()
           for a,b in zip(S_EDGES[:-1],S_EDGES[1:])]
    quarters=[_port_interval(lam,nm,i/4,(i+1)/4,overlay).tolist()
              for i in range(4)]
    np.testing.assert_allclose(np.sum(first,axis=0),quarters[0],
                               rtol=1e-12,atol=1e-9)
    return first,quarters


def _verify(base: Path, registered: dict, case: tuple) -> tuple[dict,np.ndarray]:
    ns,ny,nm,topology=case
    name=case_name(*case)
    root=base/name
    manifest,phases,result=_read(root)
    mesh=inventory.Mesh(ns,ny,512,nm)
    assert manifest['source_commit']==registered['execution_head']
    assert manifest['source_dirty'] is False
    assert (manifest['mesh']==vars(mesh) and manifest['topology']==topology and
            manifest['trace_topology']==topology and manifest['law']=='P1' and
            manifest['solve'] and manifest['scaled'] and manifest['loaded_probe'] and
            manifest['state_payload'] and manifest['loading']=='smooth')
    assert manifest['sources']==registered['runner_source_hashes']==runner._hashes()
    assert all(manifest[key]==value for key,value in registered['runtime'].items())
    assert result['post_source_hashes']==manifest['sources']==phases[0]['sources']
    assert manifest['limits']==registered['limits']
    assert result['reason']=='process_exit' and result['exit_code']==0
    assert result['sampled_peak_rss_bytes']<=registered['limits']['max_rss_bytes']
    assert result['elapsed_seconds']<=registered['limits']['max_seconds']
    assert runner._valid_state_phases(phases,topology,topology)
    assert runner._valid_state_payload(root,phases,mesh,'P1')
    assert (root/'stderr.log').stat().st_size==0
    assert manifest['threads']==registered['threads']
    assert phases[0]['threads']==manifest['threads']
    assert all(p['num_threads']==1 for p in phases[0]['threadpools'])
    assert phases[0]['modules']==registered['module_paths']
    o=phases[-1]
    assert o['free_force_scaled_max']<=1e-8
    assert o['weak_gap_scaled_max']<=1e-9
    assert max(map(abs,o['global_balance_scaled']))<=1e-8
    assert abs(o['energy_identity_joule'])<=1e-8*scaling.E0
    assert abs(o['interface_work_joule'])<=1e-8*scaling.E0
    assert len(o['finite_field_component_bounds_metre'])==3
    assert all(0<=lower<=upper and math.isfinite(upper)
               for lower,upper in o['finite_field_component_bounds_metre'])
    with np.load(root/'solved_state.npz',allow_pickle=False) as saved:
        q=saved['physical_q'].copy()
        lam=saved['physical_lambda'].copy()
    model=shell.panel(ns,ny,topology)
    ks=shell.stiffness(model)
    kb=beam.assembled_stiffness(mesh.n_beam)
    cs,cb,overlay=line.coupling(model,mesh.n_beam,nm,'P1')
    k=sparse.block_diag((ks,kb),format='csr')
    c=sparse.hstack((-cs,cb),format='csr')
    force=np.r_[np.zeros(model.dof_count),
                beam.assembled_load(mesh.n_beam,'smooth')]
    supported=np.r_[model.supported,
                    model.dof_count+beam.root_dofs(mesh.n_beam)]
    free=np.setdiff1d(np.arange(len(q)),supported)
    matrix_phase=next(p for p in phases if p['phase']=='unfactorized_kkt')
    factor_phase=next(p for p in phases if p['phase']=='factorized')
    assert matrix_phase['kkt_dimension']==len(free)+len(lam)
    assert matrix_phase['kkt_nnz']==(
        k[free,:][:,free].nnz+2*c[:,free].nnz)
    assert factor_phase['factor_nnz']==(
        factor_phase['l_nnz']+factor_phase['u_nnz'])
    assert np.max(np.abs(q[supported]))==0
    residual=k@q+c.T@lam-force
    weak=c@q
    beam_local=free-model.dof_count
    u=2*mesh.n_beam+1; v=2*(mesh.n_beam+1)
    is_moment=(beam_local>=u+v)|((beam_local>=u)&(beam_local<u+v)&
                                ((beam_local-u)%2==1))
    free_max=float(np.max(np.abs(residual[free])/
                          np.where(is_moment,scaling.M0,scaling.F0)))
    measure=np.full(nm+1,scaling.L0/nm)
    measure[[0,-1]]*=.5
    weak_max=float(np.max(np.abs(weak)/(scaling.U0*np.repeat(measure,3))))
    assert free_max<=1e-8 and weak_max<=1e-9
    np.testing.assert_allclose((free_max,weak_max),
                               (o['free_force_scaled_max'],o['weak_gap_scaled_max']),
                               rtol=2e-8,atol=1e-16)
    shell_elastic=ks@q[:model.dof_count]
    beam_elastic=kb@q[model.dof_count:]
    shell_port=-(cs.T@lam)
    beam_port=cb.T@lam
    root_ids=beam.root_dofs(mesh.n_beam)
    edge_groups=[]; edge_bands=[]
    nx=2*ns
    for i in (0,nx):
        nodes=np.array([j*(nx+1)+i for j in range(ny+1)])
        ids=np.column_stack((2*nodes,2*nodes+1)).ravel()
        edge_groups.append(_wrench(residual[ids],model.nodes[nodes]))
        bands=[]
        for a,b in zip(Y_EDGES[:-1],Y_EDGES[1:]):
            mask=(model.nodes[nodes,1]>=a-1e-12)&(model.nodes[nodes,1]<b-1e-12)
            if b==Y_EDGES[-1]:
                mask=model.nodes[nodes,1]>=a-1e-12
            selected=nodes[mask]
            dofs=np.column_stack((2*selected,2*selected+1)).ravel()
            bands.append(_wrench(residual[dofs],model.nodes[selected]).tolist())
        np.testing.assert_allclose(np.sum(bands,axis=0),edge_groups[-1],atol=1e-5)
        edge_bands.append(bands)
    root_reaction=residual[model.dof_count+root_ids]
    groups=np.asarray([*edge_groups,root_reaction])
    np.testing.assert_allclose(groups,o['support_wrenches'],rtol=1e-10,atol=1e-5)
    np.testing.assert_allclose(groups.sum(axis=0)+o['applied_resultant'],0.,
                               atol=1e-5,rtol=0)
    np.testing.assert_allclose(o['applied_resultant'],
                               (0.,scaling.F0,scaling.M0/2),atol=1e-5,rtol=0)
    qs,qb=q[:model.dof_count],q[model.dof_count:]
    stations=np.array([shell.pose(model,s)@qs for s in (.25,.5,.75)])
    stations[:,2]*=line.YAW_LENGTH
    np.testing.assert_allclose(stations,o['shell_station_displacements_metre'],
                               rtol=1e-9,atol=1e-12)
    tip=beam.trace(mesh.n_beam,1.)@qb
    tip[2]*=line.YAW_LENGTH
    np.testing.assert_allclose(tip,o['beam_tip_displacement_metre'],
                               rtol=1e-9,atol=1e-12)
    gap=line.integrated_gap(model,mesh.n_beam,nm,qs,qb)
    np.testing.assert_allclose(gap,o['integrated_gap_metre'],rtol=1e-9,atol=1e-12)
    gap_squared,motion_squared=loaded._motion_integrals(model,mesh.n_beam,nm,qs,qb)
    motion=math.sqrt(motion_squared/scaling.L0)
    fixed=math.sqrt(gap_squared)/(scaling.U0*math.sqrt(scaling.L0))
    relative=math.sqrt(gap_squared)/(
        max(motion,.1*scaling.U0)*math.sqrt(scaling.L0))
    np.testing.assert_allclose((motion,fixed,relative),
                               (o['motion_rms_metre'],o['fixed_scale_gap'],
                                o['motion_scale_gap']),rtol=1e-9,atol=1e-10)
    np.testing.assert_allclose(math.sqrt(gap_squared),gap,rtol=1e-9,atol=1e-12)
    energies=(qs@shell_elastic/2,qb@beam_elastic/2)
    np.testing.assert_allclose(energies,(o['shell_energy_joule'],
                                         o['beam_energy_joule']),rtol=1e-9,atol=1e-8)
    work=(shell_port@qs,beam_port@qb)
    np.testing.assert_allclose(work,(o['shell_interface_work_joule'],
                                     o['beam_interface_work_joule']),rtol=1e-8,atol=1e-8)
    np.testing.assert_allclose(sum(work),lam@weak,rtol=1e-8,atol=1e-8)
    first,quarters=_port_bands(lam,nm,overlay)
    beam_x=np.zeros_like(qb);beam_y=np.zeros_like(qb);beam_yaw=np.zeros_like(qb)
    beam_x[:u]=1.
    beam_y[u:u+v:2]=1.
    beam_yaw[u:u+v:2]=np.arange(mesh.n_beam+1)/mesh.n_beam
    beam_yaw[u+1:u+v:2]=1.
    beam_yaw[u+v:]=1.
    np.testing.assert_allclose(np.sum(quarters,axis=0)[:2].tolist()+[
        np.sum(quarters,axis=0)[2:].sum()],
        (beam_port@beam_x,beam_port@beam_y,beam_port@beam_yaw),
        rtol=1e-9,atol=1e-5)
    fixed=np.array([shell.pose(model,s)@qs for s in CENTERS])
    fixed[:,2]*=line.YAW_LENGTH
    return (dict(name=name,manifest_sha256=_sha(root/'manifest.json'),
                 payload_sha256=_sha(root/'solved_state.npz'),
                 elapsed_seconds=result['elapsed_seconds'],
                 peak_rss_bytes=result['sampled_peak_rss_bytes'],
                 unfactorized_kkt=matrix_phase,factorization=factor_phase,
                 free_scaled=free_max,weak_scaled=weak_max,
                 observed=o,edge_bands=edge_bands,
                 root_terms=dict(elastic=beam_elastic[root_ids].tolist(),
                                 port=beam_port[root_ids].tolist(),
                                 external=force[model.dof_count+root_ids].tolist()),
                 first_eighth_port=first,port_quarters=quarters,
                 fixed_first_quarter_station_pose=fixed.tolist()),q)


def _crossings(model: shell.Panel, nm: int,
               qc: np.ndarray, qq: np.ndarray) -> list[dict]:
    assert model.topology=='CST-CB'
    overlay=line.overlay(model,512,nm)
    q4_model=shell.panel(model.n_s,model.n_y,'Q4')
    result=[]
    for sample,(dx,dy) in enumerate(shell.OFFSETS):
        j=min(max(int(np.floor((dy+.5)*model.n_y-1e-12)),0),model.n_y-1)
        fraction=(dy-(-.5+j/model.n_y))*model.n_y
        for i in range(2*model.n_s):
            crossing=(1-fraction if (i+j)%2 else fraction)
            sc=-.5+(i+crossing)/model.n_s-dx
            if not 0<sc<.25:
                continue
            p=int(np.searchsorted(overlay,sc))
            if p<len(overlay) and abs(overlay[p]-sc)<2e-12:
                previous=overlay[p-1] if p else 0.
                nxt=overlay[p+1] if p+1<len(overlay) else 1.
            elif p and abs(overlay[p-1]-sc)<2e-12:
                previous=overlay[p-2] if p>1 else 0.
                nxt=overlay[p] if p<len(overlay) else 1.
            else:
                previous=overlay[p-1] if p else 0.
                nxt=overlay[p] if p<len(overlay) else 1.
            eps=min(1e-6,.1*min(sc-previous,nxt-sc))
            if eps<=0:
                raise AssertionError('diagonal crossing has no one-sided host interval')
            stations=(sc-eps,sc-eps/2,sc+eps/2,sc+eps)
            assert shell.sample(model,sc-eps+dx,dy)[0] != shell.sample(
                model,sc+eps+dx,dy)[0]
            poses=np.array([shell.pose(model,s)@qc for s in stations])
            q4=np.array([shell.pose(q4_model,s)@qq for s in stations])
            poses[:,2]*=line.YAW_LENGTH
            q4[:,2]*=line.YAW_LENGTH
            derivative=np.array(((poses[1]-poses[0])/(eps/2),
                                 (poses[3]-poses[2])/(eps/2)))
            q4_derivative=np.array(((q4[1]-q4[0])/(eps/2),
                                    (q4[3]-q4[2])/(eps/2)))
            result.append(dict(sample=sample,branch='falling' if (i+j)%2 else 'rising',
                               s=sc,epsilon=eps,pose_left=poses[0].tolist(),
                               pose_right=poses[-1].tolist(),
                               derivative_left=derivative[0].tolist(),
                               derivative_right=derivative[1].tolist(),
                               q4_pose_left=q4[0].tolist(),q4_pose_right=q4[-1].tolist(),
                               q4_derivative_left=q4_derivative[0].tolist(),
                               q4_derivative_right=q4_derivative[1].tolist()))
    return result


def _channels(entry: dict) -> dict[str,float]:
    """Flatten the fixed physical inventory without mixed-unit normalization."""
    result={}
    def walk(prefix, value):
        if isinstance(value,dict):
            for key,part in sorted(value.items()):
                walk(f'{prefix}.{key}',part)
        elif isinstance(value,(list,tuple)):
            for i,part in enumerate(value):
                walk(f'{prefix}[{i}]',part)
        else:
            if not isinstance(value,(int,float)) or isinstance(value,bool):
                raise ValueError(f'non-numeric physical channel {prefix}')
            result[prefix]=float(value)
    for field in fields(loaded.LoadedObservables):
        walk(f'observed.{field.name}',entry['observed'][field.name])
    for key in ('edge_bands','root_terms','first_eighth_port',
                'port_quarters','fixed_first_quarter_station_pose'):
        walk(key,entry[key])
    if not all(math.isfinite(value) for value in result.values()):
        raise ValueError('nonfinite physical channel')
    return result


def _delta(a: dict[str,float], b: dict[str,float]) -> dict[str,float]:
    assert a.keys()==b.keys()
    result={key:b[key]-a[key] for key in a}
    if not all(math.isfinite(value) for value in result.values()):
        raise ValueError('nonfinite signed physical difference')
    return result


def _sweeps(channels: dict) -> dict:
    layouts={
        'transverse':((128,16,64),(128,32,64),(128,64,64)),
        'longitudinal':((32,64,64),(64,64,64),(128,64,64)),
        'multiplier':((128,64,16),(128,64,32),(128,64,64)),
    }
    result={}
    for name,triples in layouts.items():
        rows=[]
        for low,high in zip(triples[:-1],triples[1:]):
            before={t:channels[case_name(*low,t)] for t in ('Q4','CST-CB')}
            after={t:channels[case_name(*high,t)] for t in ('Q4','CST-CB')}
            prior=_delta(before['Q4'],before['CST-CB'])
            later=_delta(after['Q4'],after['CST-CB'])
            rows.append(dict(from_mesh=list(low),to_mesh=list(high),
                             q4_change=_delta(before['Q4'],after['Q4']),
                             cb_change=_delta(before['CST-CB'],after['CST-CB']),
                             signed_pair_change=_delta(prior,later)))
        result[name]=rows
    return result


def _finite(value) -> bool:
    if isinstance(value,dict):
        return all(_finite(item) for item in value.values())
    if isinstance(value,(list,tuple)):
        return all(_finite(item) for item in value)
    if isinstance(value,float):
        return math.isfinite(value)
    return True


def adjudicate(registration: Path, evidence: Path, output: Path) -> dict:
    registered=json.loads(registration.read_text(encoding='utf-8'))
    assert registered['cases']==[case_name(*case) for case in CASES]
    assert registered['runner_source_hashes']==runner._hashes()
    assert registered['adjudicator_sha256']==_sha(Path(__file__))
    assert registered['limits']==dict(max_rss_bytes=8*1024**3,max_seconds=900)
    assert all(v=='1' for v in registered['threads'].values())
    entries={}; states={}
    for case in CASES:
        entry,q=_verify(evidence,registered,case)
        entries[entry['name']]=entry
        states[entry['name']]=q
    contrasts={}; crossings={}
    channels={name:_channels(entry) for name,entry in entries.items()}
    for ns,ny,nm in TRIPLES:
        q4=case_name(ns,ny,nm,'Q4')
        cb=case_name(ns,ny,nm,'CST-CB')
        q4_entry,cb_entry=entries[q4],entries[cb]
        contrasts[f'{ns},{ny},{nm}']=dict(
            signed_by_channel=_delta(channels[q4],channels[cb]),
            root_mz_nm=cb_entry['observed']['support_wrenches'][2][2]-
                       q4_entry['observed']['support_wrenches'][2][2],
            left_fy_n=cb_entry['observed']['support_wrenches'][0][1]-
                      q4_entry['observed']['support_wrenches'][0][1])
        model=shell.panel(ns,ny,'CST-CB')
        qc=states[cb][:model.dof_count]
        qq=states[q4][:model.dof_count]
        crossings[f'{ns},{ny},{nm}']=_crossings(model,nm,qc,qq)
    answer=dict(status='DIAGNOSTIC_ACCEPTED_G0B_OPEN',
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                execution_head=registered['execution_head'],
                registration_sha256=_sha(registration),
                adjudicator_sha256=_sha(Path(__file__)),
                inventory=len(entries),entries=entries,contrasts=contrasts,
                sweeps=_sweeps(channels),crossings=crossings)
    if not _finite(answer):
        raise ValueError('nonfinite adjudication output')
    return answer


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--registration',type=Path,required=True)
    parser.add_argument('--evidence-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    try:
        result=adjudicate(args.registration,args.evidence_root,args.output)
        result['registration_path']=str(args.registration.resolve())
        (args.output/'adjudication.json').write_text(json.dumps(result,indent=2,sort_keys=True,
                                                              allow_nan=False),
                                                     encoding='utf-8')
        print(json.dumps(dict(status=result['status'],inventory=result['inventory'],
                              output=str(args.output.resolve()))))
        return 0
    except Exception:
        (args.output/'failure.log').write_text(traceback.format_exc(),encoding='utf-8')
        print(json.dumps(dict(status='FAILED',output=str(args.output.resolve()))),
              file=sys.stderr)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
