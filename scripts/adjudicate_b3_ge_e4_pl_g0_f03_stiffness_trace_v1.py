"""One-time read-only F03 classical stiffness/trace evidence adjudication.

Reassembles operators from saved physical q/lambda without refactorization.
This checks algebraic attribution; it is not an external physical reference.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
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


SOURCE='ed1b71a0951bbadaaf6682568b60baba55a00e0b'
EXECUTION_HEAD='454b3c9bacaf4d8b259963bf3f92f1e2e0fdc8a5'
ROOTS={
    32:('f03-stiffness-trace-y32-kq-cq-v1',
        'f03-stiffness-trace-y32-kcb-ccb-v1',
        'f03-stiffness-trace-y32-kq-ccb-v1',
        'f03-stiffness-trace-y32-kcb-cq-v1'),
    64:('f03-stiffness-trace-y64-kq-cq-v1',
        'f03-stiffness-trace-y64-kcb-ccb-v1',
        'f03-stiffness-trace-y64-kq-ccb-v1',
        'f03-stiffness-trace-y64-kcb-cq-v1'),
}
OLD={
    32:(('f03-classical-cst-cb-y32-q4-v1',
         '0402d1452613801896e45b201a4aeddff00666a3ed22d3d4f9b78c127ac18e43'),
        ('f03-classical-cst-cb-y32-v1',
         'f9522121ba077c4fe36b6cbd5bfbd5b9ef6544fe0ac942f4df9f49fcbe2e16a6')),
    64:(('f03-classical-cst-cb-upper-q4-v1',
         '1ac115f9e18dfedde87663b67735880be2c26aa3a2ea124fa9eeac682bbc3757'),
        ('f03-classical-cst-cb-upper-v1',
         'b0b01d74271f6c02f7dc664aaea5af9cf4e5a7a7e9a2414f840dc708c4fd38b3')),
}
LABELS=(('shell_energy','beam_energy')+
        tuple(f'tip_{c}' for c in ('u','v','Lc_yaw'))+
        tuple(f'station_{s}_{c}' for s in ('025','050','075')
              for c in ('u','v','Lc_yaw'))+
        tuple(f'{edge}_{c}' for edge in ('left','right','beam_root')
              for c in ('Fx','Fy','Mz')))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(root: Path) -> tuple[dict,list[dict],dict,str]:
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    result=json.loads((root/'result.json').read_text(encoding='utf-8'))
    phases=[json.loads(s) for s in (root/'phases.jsonl').read_text(encoding='utf-8').splitlines()]
    return manifest,phases,result,_sha(root/'manifest.json')


def _vector(o: dict) -> np.ndarray:
    return np.asarray([o['shell_energy_joule'],o['beam_energy_joule'],
                       *o['beam_tip_displacement_metre'],
                       *(v for station in o['shell_station_displacements_metre'] for v in station),
                       *(v for wrench in o['support_wrenches'] for v in wrench)],dtype=float)


def _wrench(dual: np.ndarray, positions: np.ndarray) -> np.ndarray:
    return np.array((np.sum(dual[::2]),np.sum(dual[1::2]),
                     positions[:,0]@dual[1::2]-positions[:,1]@dual[::2]))


def _port_quarters(lam: np.ndarray, nm: int) -> list[list[float]]:
    if nm%4:
        raise ValueError('quarter port diagnostic requires divisible mortar cells')
    roots,weights=np.polynomial.legendre.leggauss(2)
    result=[]
    for band in range(4):
        wrench=np.zeros(3)
        for cell in range(band*nm//4,(band+1)*nm//4):
            a,b=cell/nm,(cell+1)/nm
            for root,weight in zip(roots,weights):
                s=(a+b)/2+(b-a)*root/2
                density=sum(test*lam[3*i:3*i+3]
                            for i,test in line.mortar_tests(nm,'P1',s))
                # λ_yaw is conjugate to Lc*c_yaw, hence physical moment Lc*λ.
                wrench+=(b-a)*weight/2*np.array((density[0],density[1],
                                                  s*density[1]+line.YAW_LENGTH*density[2]))
        result.append(wrench.tolist())
    return result


def _verify_case(base: Path, name: str, ny: int, stiffness: str,
                 trace: str) -> dict:
    root=base/name
    manifest,phases,result,manifest_hash=_load(root)
    mesh=inventory.Mesh(128,ny,512,64)
    assert manifest['source_commit']==EXECUTION_HEAD and manifest['source_dirty'] is False
    assert (manifest['mesh']==vars(mesh) and manifest['topology']==stiffness and
            manifest['trace_topology']==trace and manifest['law']=='P1' and
            manifest['solve'] and manifest['scaled'] and manifest['loaded_probe'] and
            manifest['state_payload'] and manifest['loading']=='smooth')
    assert manifest['limits']==dict(max_rss_bytes=8*1024**3,max_seconds=900)
    assert result['reason']=='process_exit' and result['exit_code']==0
    assert result['sampled_peak_rss_bytes']<=8*1024**3
    assert result['elapsed_seconds']<=900
    assert (manifest['sources']==result['post_source_hashes']==phases[0]['sources']
            ==runner._hashes())
    assert runner._valid_state_phases(phases,stiffness,trace)
    assert runner._valid_state_payload(root,phases,mesh,'P1')
    assert (root/'stderr.log').stat().st_size==0
    assert all(pool['num_threads']==1 for pool in phases[0]['threadpools'])
    assert all(value=='1' for value in manifest['threads'].values())
    assert phases[0]['threads']==manifest['threads']
    o=phases[-1]
    assert len(o['finite_field_component_bounds_metre'])==3
    assert all(0<=lower<=upper and np.isfinite(upper)
               for lower,upper in o['finite_field_component_bounds_metre'])
    assert np.max(np.abs(o['global_balance_scaled']))<=1e-8
    assert o['free_force_scaled_max']<=1e-8 and o['weak_gap_scaled_max']<=1e-9
    assert abs(o['energy_identity_joule'])<=1e-8*scaling.E0
    assert abs(o['interface_work_joule'])<=1e-8*scaling.E0
    with np.load(root/'solved_state.npz',allow_pickle=False) as saved:
        q=saved['physical_q']; lam=saved['physical_lambda']
    stiff=shell.panel(mesh.n_s,mesh.n_y,stiffness)
    trace_panel=shell.panel(mesh.n_s,mesh.n_y,trace)
    np.testing.assert_array_equal(stiff.nodes,trace_panel.nodes)
    np.testing.assert_array_equal(stiff.supported,trace_panel.supported)
    ks=shell.stiffness(stiff); kb=beam.assembled_stiffness(mesh.n_beam)
    cs,cb,_=line.coupling(trace_panel,mesh.n_beam,mesh.n_mortar,'P1')
    qs,qb=q[:stiff.dof_count],q[stiff.dof_count:]
    f=np.r_[np.zeros(stiff.dof_count),beam.assembled_load(mesh.n_beam,'smooth')]
    k=sparse.block_diag((ks,kb),format='csr')
    c=sparse.hstack((-cs,cb),format='csr')
    supported=np.r_[stiff.supported,stiff.dof_count+beam.root_dofs(mesh.n_beam)]
    free=np.setdiff1d(np.arange(len(q)),supported)
    assert np.max(np.abs(q[supported]))==0
    residual=k@q+c.T@lam-f
    weak=c@q
    beam_local=free-stiff.dof_count
    u=2*mesh.n_beam+1; v=2*(mesh.n_beam+1)
    is_moment=(beam_local>=u+v)|((beam_local>=u)&(beam_local<u+v)&
                                ((beam_local-u)%2==1))
    free_max=float(np.max(np.abs(residual[free])/np.where(is_moment,scaling.M0,scaling.F0)))
    measure=np.full(mesh.n_mortar+1,scaling.L0/mesh.n_mortar)
    measure[[0,-1]]*=.5
    weak_max=float(np.max(np.abs(weak)/(scaling.U0*np.repeat(measure,3))))
    assert free_max<=1e-8 and weak_max<=1e-9
    np.testing.assert_allclose((free_max,weak_max),
                               (o['free_force_scaled_max'],o['weak_gap_scaled_max']),
                               rtol=2e-8,atol=1e-16)
    shell_elastic=ks@qs; shell_port=-(cs.T@lam)
    beam_elastic=kb@qb; beam_port=cb.T@lam
    np.testing.assert_allclose(np.r_[shell_elastic+shell_port,
                                      beam_elastic+beam_port-f[stiff.dof_count:]],
                               residual,rtol=1e-10,atol=1e-5)
    nx=2*mesh.n_s
    left=np.array([j*(nx+1) for j in range(ny+1)])
    edge_sets=(left,left+nx)
    groups=[]; bands=[]
    for nodes in edge_sets:
        ids=np.column_stack((2*nodes,2*nodes+1)).ravel()
        groups.append(_wrench(residual[ids],stiff.nodes[nodes]))
        band_rows=[]
        for mask in (stiff.nodes[nodes,1]<0,stiff.nodes[nodes,1]>=0):
            selected=nodes[mask]
            dofs=np.column_stack((2*selected,2*selected+1)).ravel()
            band_rows.append(_wrench(residual[dofs],stiff.nodes[selected]))
        np.testing.assert_allclose(np.sum(band_rows,axis=0),groups[-1],atol=1e-6)
        bands.append([row.tolist() for row in band_rows])
    groups.append(residual[stiff.dof_count+beam.root_dofs(mesh.n_beam)])
    np.testing.assert_allclose(groups,o['support_wrenches'],rtol=1e-10,atol=1e-5)
    np.testing.assert_allclose(o['applied_resultant'],(0.,scaling.F0,scaling.M0/2),
                               rtol=0,atol=1e-5)
    np.testing.assert_allclose(np.sum(groups,axis=0)+o['applied_resultant'],0.,
                               rtol=0,atol=1e-5)
    stations=[shell.pose(trace_panel,s)@qs for s in (.25,.5,.75)]
    stations=[(row[0],row[1],line.YAW_LENGTH*row[2]) for row in stations]
    np.testing.assert_allclose(stations,o['shell_station_displacements_metre'],
                               rtol=1e-9,atol=1e-12)
    tip=beam.trace(mesh.n_beam,1.)@qb
    np.testing.assert_allclose((tip[0],tip[1],line.YAW_LENGTH*tip[2]),
                               o['beam_tip_displacement_metre'],rtol=1e-9,atol=1e-12)
    gap=line.integrated_gap(trace_panel,mesh.n_beam,mesh.n_mortar,qs,qb)
    np.testing.assert_allclose(gap,o['integrated_gap_metre'],rtol=1e-9,atol=1e-12)
    np.testing.assert_allclose(gap/scaling.U0,o['fixed_scale_gap'],rtol=1e-9,atol=1e-10)
    gap_squared,motion_squared=loaded._motion_integrals(
        trace_panel,mesh.n_beam,mesh.n_mortar,qs,qb)
    motion=np.sqrt(motion_squared/scaling.L0)
    np.testing.assert_allclose(np.sqrt(gap_squared)/
                               (max(motion,.1*scaling.U0)*np.sqrt(scaling.L0)),
                               o['motion_scale_gap'],rtol=1e-9,atol=1e-10)
    energies=(float(qs@shell_elastic/2),float(qb@beam_elastic/2))
    np.testing.assert_allclose(energies,(o['shell_energy_joule'],o['beam_energy_joule']),
                               rtol=1e-9,atol=1e-8)
    work=(float(shell_port@qs),float(beam_port@qb))
    np.testing.assert_allclose(work,(o['shell_interface_work_joule'],
                                     o['beam_interface_work_joule']),rtol=1e-8,atol=1e-8)
    np.testing.assert_allclose(sum(work),lam@weak,rtol=1e-8,atol=1e-8)
    port_quarters=_port_quarters(lam,mesh.n_mortar)
    beam_x=np.zeros_like(qb);beam_y=np.zeros_like(qb);beam_yaw=np.zeros_like(qb)
    beam_x[:u]=1.
    beam_y[u:u+v:2]=1.
    beam_yaw[u:u+v:2]=np.arange(mesh.n_beam+1)/mesh.n_beam
    beam_yaw[u+1:u+v:2]=1.
    beam_yaw[u+v:]=1.
    np.testing.assert_allclose(np.sum(port_quarters,axis=0),
                               (beam_port@beam_x,beam_port@beam_y,
                                beam_port@beam_yaw),rtol=1e-9,atol=1e-5)
    return dict(name=name,manifest_sha256=manifest_hash,payload_sha256=_sha(root/'solved_state.npz'),
                elapsed_seconds=result['elapsed_seconds'],peak_rss_bytes=result['sampled_peak_rss_bytes'],
                unfactorized_kkt=next(row for row in phases if row['phase']=='unfactorized_kkt'),
                factorization=next(row for row in phases if row['phase']=='factorized'),
                failed_work=0,
                free_scaled=free_max,weak_scaled=weak_max,observed=o,
                support_bands=bands,root_terms=dict(elastic=beam_elastic[beam.root_dofs(mesh.n_beam)].tolist(),
                                                    port=beam_port[beam.root_dofs(mesh.n_beam)].tolist(),
                                                    external=f[stiff.dof_count+beam.root_dofs(mesh.n_beam)].tolist()),
                generalized_port_quarter_wrenches=port_quarters)


def _parity(base: Path, new: dict, old_name: str, old_hash: str) -> dict:
    old_root=base/old_name
    m,p,r,h=_load(old_root)
    assert h==old_hash and r['reason']=='process_exit' and r['exit_code']==0
    assert [entry['phase'] for entry in p]==[
        'identity','panel','shell_stiffness','beam_stiffness','coupling',
        'unfactorized_kkt','scaled_kkt','factorized','linear_solve','loaded_observables']
    assert not m['source_dirty'] and m['sources']==p[0]['sources']==r['post_source_hashes']
    a=_vector(new['observed']); b=_vector(p[-1])
    assert len(a)==len(b)==len(LABELS)==23
    floors=np.array([.001*scaling.E0]*2+[.1*scaling.U0]*12+
                    [(.01*scaling.M0 if i%3==2 else .01*scaling.F0)
                     for i in range(9)])
    ratios=np.abs(a-b)/np.maximum(np.abs(b),floors)
    assert np.max(ratios)<=1e-8
    assert abs(new['observed']['fixed_scale_gap']-p[-1]['fixed_scale_gap'])<=1e-10
    assert abs(new['observed']['motion_scale_gap']-p[-1]['motion_scale_gap'])<=1e-10
    return dict(old_name=old_name,old_manifest_sha256=h,max_normalized_difference=float(np.max(ratios)),
                g2_difference=float(new['observed']['fixed_scale_gap']-p[-1]['fixed_scale_gap']),
                gmotion_difference=float(new['observed']['motion_scale_gap']-p[-1]['motion_scale_gap']))


def _attribution(cases: list[dict]) -> dict:
    qq,bb,qb,bq=(_vector(case['observed']) for case in cases)
    total=bb-qq
    trace=((qb-qq)+(bb-bq))/2
    stiffness=((bq-qq)+(bb-qb))/2
    interaction=bb-bq-qb+qq
    np.testing.assert_allclose(trace+stiffness,total,rtol=0,atol=1e-12)
    return {label:dict(natural_q=float(qq[i]),natural_cb=float(bb[i]),
                       trace_on_q=float(qb[i]),stiffness_on_q=float(bq[i]),
                       total=float(total[i]),trace_effect=float(trace[i]),
                       stiffness_effect=float(stiffness[i]),
                       interaction=float(interaction[i]))
            for i,label in enumerate(LABELS)}


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--evidence-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    checkout=Path(__file__).resolve().parents[1]
    assert not subprocess.run(('git','status','--porcelain'),cwd=checkout,
                              check=True,capture_output=True,text=True).stdout.strip()
    assert not args.output.exists()
    args.output.mkdir(parents=True,exist_ok=False)
    try:
        cases={}; parity={}; effects={}
        for ny in (32,64):
            names=ROOTS[ny]
            natural=[_verify_case(args.evidence_root,names[i],ny,
                                  ('Q4','CST-CB')[i],('Q4','CST-CB')[i])
                     for i in (0,1)]
            parity[str(ny)]=[_parity(args.evidence_root,natural[i],*OLD[ny][i])
                             for i in (0,1)]
            mixed=[_verify_case(args.evidence_root,names[i],ny,
                                ('Q4','CST-CB')[i-2],('CST-CB','Q4')[i-2])
                   for i in (2,3)]
            built=natural+mixed
            cases[str(ny)]=built
            effects[str(ny)]=_attribution(built)
        record=dict(status='DIAGNOSTIC_PASS_NOT_G0B',
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    adjudicator_sha256=_sha(Path(__file__)),
                    executable_source_commit=SOURCE,
                    current_head=subprocess.run(('git','rev-parse','HEAD'),cwd=checkout,
                                                check=True,capture_output=True,text=True).stdout.strip(),
                    python=sys.version,platform=platform.platform(),
                    cases=cases,natural_parity=parity,attribution=effects)
        (args.output/'adjudication.json').write_text(
            json.dumps(record,indent=2,sort_keys=True,allow_nan=False),encoding='utf-8')
        print(json.dumps(dict(status=record['status'],evidence=str(args.output.resolve()),
                              root_mz={ny:effects[ny]['beam_root_Mz']
                                       for ny in ('32','64')}),sort_keys=True))
        return 0
    except Exception as exc:
        (args.output/'failure.json').write_text(
            json.dumps(dict(status='FAILED',type=type(exc).__name__,message=str(exc),
                            traceback=traceback.format_exc(),
                            timestamp_utc=datetime.now(timezone.utc).isoformat()),
                       indent=2),encoding='utf-8')
        raise


if __name__=='__main__':
    raise SystemExit(main())
