"""One fixed joint32 physical comparison for the growing projected BL5 space.

No numerical solve, mesh refinement, policy selection or F03 execution. Native
retained traces and classic external beam fields remain different discretizations.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import traceback

import numpy as np
from threadpoolctl import threadpool_info
LOADS={'fy':(0.,100.,0.,0.,0.,0.),'mx':(0.,0.,0.,10.,0.,0.),'mz':(0.,0.,0.,0.,0.,10.)}
EXTERNAL_CHECKS={'all_free_coordinate_equilibrium_scaled','average_five_channel_gap_scaled',
    'emitted_coordinate_gap_scaled','local_recovery_residual_scaled','independent_arm_pullback_scaled',
    'each_support_action_reaction_scaled','interface_wrench_scaled','ground_plus_applied_wrench_scaled',
    'complete_domain_cut_wrench_scaled','physical_work_relative','internal_applied_work_relative',
    'compatible_interface_work_relative','solved_dual_work_relative','virtual_dual_work_relative',
    'continuous_density_nodal_total_wrench_scaled'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition,message):
    if not condition:raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def plain(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,dict):return {k:plain(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [plain(v) for v in value]
    return value


def field_errors(native,external,cells,coordinates,beam=False):
    """Integrate common nodal P1/Q1 fields only; no cell-rotation identification.

    Same diagnostic definition as the preceding matched comparisons. This
    standalone evaluator does not import a product or identify retained fields.
    """
    errors,references=np.zeros(6),np.zeros(6)
    gauss=(-1/math.sqrt(3),1/math.sqrt(3))
    for cell in cells:
        ids=list(cell);n,e,xyz=native[ids],external[ids],coordinates[ids]
        for point in (gauss if beam else [(x,y) for x in gauss for y in gauss]):
            if beam:
                weights=np.array(((1-point)/2,(1+point)/2));measure=np.linalg.norm(xyz[1]-xyz[0])/2
            else:
                x,y=point;weights=np.array(((1-x)*(1-y),(1+x)*(1-y),(1+x)*(1+y),(1-x)*(1+y)))/4
                measure=np.linalg.norm(np.cross(xyz[1]-xyz[0],xyz[3]-xyz[0]))/4
            difference,value=weights@(n-e),weights@e
            errors+=measure*difference*difference;references+=measure*value*value
    return dict(component_error_squared=errors.tolist(),component_reference_squared=references.tolist(),
        translation_relative_l2=math.sqrt(math.fsum(errors[:3])/max(math.fsum(references[:3]),1e-24)),
        rotation_relative_l2=math.sqrt(math.fsum(errors[3:])/max(math.fsum(references[3:]),1e-24)),
        combined_1m_relative_l2=math.sqrt(math.fsum(errors)/max(math.fsum(references),1e-24)),
        denominator_floor=1e-24,component_units='translations m; rotations rad; shell measure m2/beam measure m')


def compare(owner_path,external_root,fixtures,output):
    if output.exists():raise FileExistsError(output)
    report=dict(status='FAILED_DEVELOPMENT_COMPARISON',cases={},
        scope='same fine geometry/supports/sections/loads and projected80 weak action; different beam/shell elements and retained traces; supplementary OpenSees, not converged accuracy or policy acceptance',
        source_sha256=sha(__file__))
    try:
        owner=read(owner_path)
        inputs_path=owner_path.parent/'native/inputs.json'
        require(sha(inputs_path)==owner['native_input_sha256']['inputs.json'],'bound actual native definition required')
        inputs=read(inputs_path)
        require(owner['status']=='COMPLETED_INSTALLED_DEVELOPMENT_ONLY' and all(owner['predicates'].values())
            and owner['identity']=='BL5_PROJECTED_FOUR_SHELL_INTERVALS_JOINT32_DEV_V1' and owner['fixture']==dict(nx=32,ny=8,halfcells=64,supports=8),'completed actual joint32 owner required')
        wrapper_path=fixtures/'r8_bl5_projected_joint_external_dev.py'
        spec=importlib.util.spec_from_file_location('nested_external',wrapper_path)
        wrapper=importlib.util.module_from_spec(spec);spec.loader.exec_module(wrapper)
        affine,refinement,_,_,_,reference=wrapper.services()
        model=refinement.geometry(32,reference);model['support_count']=8
        pairing=wrapper.aggregate_rows(model,reference,affine)
        require(len(pairing['physical_rows'])==80,'complete independent80 action required')
        numbering=inputs['layout'];nodes=numbering['typed_physical_nodes']
        ids=[r['external_node'] for r in nodes];xyz=np.array(inputs['xyz_m'])
        ns=len(numbering['shell_node_ids']);nb=len(numbering['beam_node_ids'])
        require((ns,nb,len(ids))==(297,65,362),'fixed physical field layout required')
        require([r['q_offset'] for r in nodes]==list(range(0,2172,6)),'explicit nodal execution slots required')
        shell_index={n:i for i,n in enumerate(numbering['shell_node_ids'])}
        cells=[tuple(shell_index[n] for n in cell) for cell in inputs['shell']['q4_elements']]
        fixed={(d,n if d=='shell' else 100001+n-101,c) for d,n,c in inputs['fixed']}
        elastic=np.diag((reference.E_PA*reference.BEAM_AREA_M2,
            reference.G_PA*reference.BEAM_SHEAR_AREA_M2,reference.G_PA*reference.BEAM_SHEAR_AREA_M2,
            reference.G_PA*reference.BEAM_TORSION_M4,reference.E_PA*reference.BEAM_BENDING_M4,
            reference.E_PA*reference.BEAM_BENDING_M4))
        require(inputs['shell']['thickness_m']==reference.SHELL_THICKNESS_M
            and inputs['shell']['young_pa']==reference.E_PA and inputs['shell']['poisson']==reference.NU
            and all(np.array_equal(b['section']['elastic'],elastic) for b in inputs['beams']),
            'same actual native shell/beam static sections required')
        require(inputs['line']['basis']=='discontinuous_p1_cell_average' and inputs['line']['multiplier_span']==8
            and inputs['policy']['support_endpoints_m']==[i/8 for i in range(9)],'same nested physical correspondence required')
        for station in inputs['station_traces']:
            require(np.allclose(station['beam_port']['frame'],np.eye(3),rtol=0,atol=1e-13)
                and np.allclose(station['reference_arm_m'],(0,0,reference.BEAM_BOTTOM_ARM_M),rtol=0,atol=1e-13)
                and np.allclose(station['reference_director'],(0,0,1),rtol=0,atol=1e-13)
                and np.linalg.norm(station['beam_port']['lift_m'])<=1e-13,'matched physical frames/offsets required')
        states={}
        for case in LOADS:
            raw=inputs_path.parent/case/'raw-state.npz'
            meta=read(raw.with_suffix('.json'))
            require(meta['status']=='completed' and meta['arrays_sha256']==sha(raw),'bound completed actual owner state required')
            with np.load(raw,allow_pickle=False) as z:
                states.update({case+'_'+name:z[name].copy() for name in ('q','load')})
        if True:
            for case,wrench in LOADS.items():
                folder=external_root/case
                es,ei,er,ea=(read(folder/name) for name in
                    ('summary.json','inputs.json','raw-inventory.json','recovered-actions.json'))
                require(es['status']=='completed' and es['case']==case and es['nx']==32 and es['ny']==8 and es['supports']==8
                    and es['rows']==80 and es['source_sha256']==sha(wrapper_path)
                    and es['basis']==ei['basis']==ea['basis']=='discontinuous_p1_cell_average',
                    'same completed independent joint32 reference required')
                expected=refinement.planned_inventory(refinement.command_recipe(model,reference,pairing['emitted_rows'],case))
                require(all(er[k]==json.loads(json.dumps(plain(v))) for k,v in expected.items()),'complete actual external command inventory required')
                require(ei['physical_rows']==pairing['physical_rows'] and ei['supports']==json.loads(json.dumps(plain(pairing['supports'])))
                    and ei['load']==list(wrench),'matched independent rows/supports/load required')
                require(set(ea['checks'])==EXTERNAL_CHECKS and ea['checks']==es['checks'],'complete external physical controls required')
                require(all(math.isfinite(v) and v<=(1e-9 if k in
                    ('average_five_channel_gap_scaled','emitted_coordinate_gap_scaled') else 1e-8)
                    for k,v in ea['checks'].items()),'external physical controls failed')
                require(set(map(int,er['poses']))==set(ids)
                    and np.allclose([er['nodes'][str(n)] for n in ids],xyz,rtol=0,atol=1e-13),
                    'same complete physical geometry required')
                efixed={('shell' if int(n) in shell_index else 'beam',int(n),c)
                    for n,flags in er['fixes'].items() for c,flag in enumerate(flags) if flag}
                require(fixed==efixed,'same physical supports required')
                q=states[case+'_q'];load=states[case+'_load']
                require(q.shape==load.shape==(2940,) and np.isfinite(q).all() and np.isfinite(load).all(),
                    'complete native nodal/retained state required')
                expected_load=np.zeros(2940);expected_load[2166:2172]=wrench
                require(np.array_equal(load,expected_load),'actual native load must match reference load')
                native=q[:2172].reshape(362,6);other=np.array([er['poses'][str(n)] for n in ids])
                require(other.shape==native.shape and np.isfinite(other).all(),'finite common nodal fields required')
                item=owner['cases'][case];work=float(q@load);ework=ea['work_J']['applied']
                require(work==item['work_J'] and math.isfinite(ework) and ework>0,'positive matched applied work required')
                moments=np.array(item['exact_transfer_moments'])
                em=np.array([ea['continuous_density_measures']['polynomial_x_moments'][str(p)] for p in range(3)])
                report['cases'][case]=dict(work_relative_signed=(work-ework)/max(abs(ework),1e-12),
                    native_work_J=work,external_work_J=ework,
                    fields=dict(shell=field_errors(native[:ns],other[:ns],cells,xyz[:ns]),
                        beam=field_errors(native[ns:],other[ns:],[(i,i+1) for i in range(nb-1)],xyz[ns:],True)),
                    native_transfer_moments=moments.tolist(),external_transfer_moments=em.tolist(),
                    transfer_difference=(moments-em).tolist(),
                    fixed_region_difference=(np.array(item['exact_region_wrench'])-
                        np.array(ea['continuous_density_measures']['fixed_region_025_075']['open'])).tolist(),
                    ground_difference={d:(np.array(item['ground_wrenches'][d])-np.array(ea[d+'_ground_wrench'])).tolist()
                        for d in ('beam','shell')},
                    native_pointwise_gaps={k:item['physical_transfer'][k] for k in
                        ('pointwise_translation_gap_max_m','pointwise_director_gap_max')},
                    native_tip_pose=native[-1].tolist(),external_tip_pose=other[-1].tolist(),
                    external_sha256={name:sha(folder/name) for name in
                        ('summary.json','inputs.json','raw-inventory.json','recovered-actions.json')})
        report.update(status='COMPLETED_MATCHED_DEVELOPMENT_ONLY',owner_sha256=sha(owner_path),
            owner_state_sha256={case:sha(inputs_path.parent/case/'raw-state.npz') for case in LOADS},definition_sha256=sha(inputs_path),
            wrapper_sha256=sha(wrapper_path),pools=threadpool_info())
    except BaseException as error:
        report['failure']=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
        raise
    finally:output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for arg in ('owner','external','fixtures','output'):p.add_argument('--'+arg,type=Path,required=True)
    a=p.parse_args()
    if not threadpool_info() or any(x['num_threads']!=1 for x in threadpool_info()):
        raise RuntimeError('effective one-thread pools required')
    r=compare(a.owner,a.external,a.fixtures,a.output)
    print(json.dumps(dict(status=r['status'],work_percent={k:100*v['work_relative_signed'] for k,v in r['cases'].items()})))
