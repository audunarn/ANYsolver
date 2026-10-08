"""Saved-density two-part body-work DEV consumer; no qualification claims."""
from fractions import Fraction as F
from pathlib import Path
import json
from dataclasses import asdict,is_dataclass
import numpy as np
from scipy import sparse
from scripts import r8_bl5_body_port_probe as original
from scripts import r8_bl5_body_port_twofold as core

IDENTITY='R8_BL5_TWO_PART_SAVED_DENSITY_WORKFLOW_DEV_V1'

def paired(value):
    """Exact sum of existing material field high/low halves."""
    return tuple(F.from_float(float(h))+F.from_float(float(l)) for h,l in zip(*value))

def action(matrix,q):
    return core.matrix_action(sparse.csr_matrix(matrix),q)

def text(values):
    return [str(core._decimal(v)) for v in values]

def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2,default=lambda v: str(core._decimal(v)) if isinstance(v,F) else asdict(v) if is_dataclass(v) else original.continuum.jsonable(v))+'\n')

def check_wrench(rigid,load,support):
    values=tuple(F.from_float(float(v))+s for v,s in zip(load,support))
    wrench=tuple(sum((F.from_float(float(a))*v for a,v in zip(row,values)),F(0)) for row in np.asarray(rigid).T)
    if max(map(abs,wrench),default=F(0))>F.from_float(1e-8):
        raise ValueError('original physical common-origin wrench failed')
    return wrench

def require_elastic(response,origin):
    if response['origin']!=origin or response['history']!=origin:
        raise ValueError('virgin history changed')
    if paired(([response['incremental_dissipation'][0]],[response['incremental_dissipation'][1]]))!=(F(0),):
        raise ValueError('nonzero material dissipation')
    for station in response['stations']:
        if any(f.branch!='ELASTIC' or any(f.plastic_increment) for f in station['fibres']):
            raise ValueError('strict ELASTIC branch required; boundary/knot excluded')

def material(owner,q,diagnostics=None):
    """Virgin quadratic law superposition, actual cell responses at pHi/pLo.

    Field pairs returned by the cell are separate from coordinate pairs. All
    contractions include both. Reference-linear J acts on both pose parts.
    Combined section response is an admission witness, not a new constitutive law.
    """
    rows=[];energy=F(0);calls=0
    for element_index,(element,slots,origin) in enumerate(owner._beam_parts):
        op=element.operator;ref=op.reference
        if origin!=op.cell.virgin():raise ValueError('strict virgin elastic origin required')
        local=core.TwofoldVector(q.high[slots],q.low[slots])
        zero=op.cell.response([0.]*18,origin,check=op.guard,include_energy=True);calls+=1
        if diagnostics is not None:write(Path(diagnostics)/('material-reference-'+str(element_index)+'.json'),dict(status='CALCULATED_NOT_VALIDATED',response=zero))
        require_elastic(zero,origin)
        if any(paired(zero['gradient'])) or any(paired(zero['potential'])) or any(zero['stored_energy']):
            raise ValueError('zero reference gradient/potential/energy required')
        hi=op.cell.response(local.high[24:].tolist(),origin,check=op.guard,include_energy=True)
        lo=op.cell.response(local.low[24:].tolist(),origin,check=op.guard,include_energy=True);calls+=2
        if diagnostics is not None:write(Path(diagnostics)/('material-parts-'+str(element_index)+'.json'),dict(status='CALCULATED_NOT_VALIDATED',p_hi=local.high[24:],p_lo=local.low[24:],hi=hi,lo=lo))
        require_elastic(hi,origin);require_elastic(lo,origin)
        gh=paired(hi['gradient']);gl=paired(lo['gradient']);gradient=tuple(a+b for a,b in zip(gh,gl))
        reference=op.evaluate(ref.coordinates,np.zeros((3,3)),ref.nodal_triads,
            np.tile(np.eye(3),(2,1,1)),np.zeros(18),origin=origin);calls+=1
        kin=action(reference.hessian[24:,:24],core.TwofoldVector(local.high[:24],local.low[:24]))
        residual=tuple(a-b for a,b in zip(kin,gradient))
        eh=sum(map(F.from_float,hi['stored_energy']),F(0));el=sum(map(F.from_float,lo['stored_energy']),F(0))
        cross=sum((F.from_float(float(p))*g for p,g in zip(local.high[24:],gl)),F(0))
        stored=eh+el+cross;energy+=stored
        stations=[]
        for station_index,(sh,sl,station_origin) in enumerate(zip(hi['stations'],lo['stations'],origin.stations)):
            strain=tuple(a+b for a,b in zip(paired(sh['strain']),paired(sl['strain'])))
            h=np.array([float(v) for v in strain]);l=np.array([float(v-F.from_float(float(a))) for v,a in zip(strain,h)])
            combined=op.cell.section.response(h,station_origin,strain_low=l,check=op.guard);calls+=1
            if diagnostics is not None:write(Path(diagnostics)/('material-combined-'+str(element_index)+'-'+str(station_index)+'.json'),dict(status='CALCULATED_NOT_VALIDATED',strain_exact=text(strain),response=combined))
            if combined.history!=station_origin or any(combined.dissipation):
                raise ValueError('combined history/dissipation changed')
            witnesses=[]
            for fibre,witness in zip(op.cell.section.fibres,combined.fibres):
                # Exact represented combined stress, independent of rounded two-part admission strain.
                mapping=tuple(F(v) for v in op.cell.section._map(fibre))
                ef=sum((a*b for a,b in zip(mapping,strain)),F(0))
                stress=F.from_float(float(fibre.young))*ef
                if (witness.branch!='ELASTIC' or any(witness.plastic_increment)
                        or abs(stress)>=F.from_float(float(fibre.curve.flow_stress[0]))):
                    raise ValueError('combined actual fibre stress is not strictly elastic')
                witnesses.append(dict(id=fibre.fibre_id,branch=witness.branch,exact_stress=text([stress])[0]))
            stations.append(dict(strain_exact=text(strain),strain_hi=h.tolist(),strain_lo=l.tolist(),fibres=witnesses))
        row=dict(element=element.node_ids,origin_identity=op.cell.identity,history_unchanged=True,
            p_hi=local.high[24:].tolist(),p_lo=local.low[24:].tolist(),gradient_hi_fields=hi['gradient'],
            gradient_lo_fields=lo['gradient'],stationarity=text(residual),energy_hi=str(core._decimal(eh)),
            energy_lo=str(core._decimal(el)),energy_cross=str(core._decimal(cross)),stored_energy=str(core._decimal(stored)),stations=stations)
        rows.append(row)
        if diagnostics is not None:write(Path(diagnostics)/('material-stationarity-'+str(element_index)+'.json'),dict(status='CALCULATED_NOT_VALIDATED',**row))
        if max(map(abs,residual),default=F(0))>F.from_float(1e-9):raise ValueError('original reference-linear material stationarity failed')
    return dict(elements=rows,stored_energy_exact=energy,local_response_calls=calls)

def run(saved,prepared,output):
    output=Path(output);output.mkdir(exist_ok=False)
    owner,loads,rigid,preflight=prepared;ns=owner._shell_count
    write(output/'preflight.json',preflight)
    reference=original.continuum_fields(saved);write(output/'saved-continuum.json',reference)
    write(output/'material-evaluation.json',dict(status='NOT_EVALUATED'))
    inventory=dict(shell_RHS=0,beam_RHS=0)
    shell=core.solve_body_twofold(owner._K[:ns,:ns].tocsr(),loads[:ns],owner._coordinate_scale[:ns],fixed=owner._fixed)
    inventory['shell_RHS']=1;write(output/'shell.json',shell.report);write(output/'inventory.json',inventory)
    if shell.report['status']!='DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED':raise ValueError('original shell gate failed: '+shell.report['status'])
    residual=tuple(v-F.from_float(float(f)) for v,f in zip(action(owner._K[:ns,:ns],shell.coordinates),loads[:ns]))
    support=tuple(v if i in set(owner._fixed) else F(0) for i,v in enumerate(residual))
    write(output/'shell-wrench.json',dict(residual=text(check_wrench(original.shell_rigid_fields(owner),loads[:ns],support))))
    beam=core.solve_body_twofold(owner._K[ns:,ns:].tocsr(),loads[ns:],owner._coordinate_scale[ns:],rigid=rigid)
    inventory['beam_RHS']=1;write(output/'beam.json',beam.report);write(output/'inventory.json',inventory)
    if beam.report['status']!='DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED':raise ValueError('original beam gate failed: '+beam.report['status'])
    q=core.TwofoldVector(np.r_[shell.coordinates.high,beam.coordinates.high],np.r_[shell.coordinates.low,beam.coordinates.low])
    write(output/'material-evaluation.json',dict(status='STARTED_CALCULATED_NOT_VALIDATED'))
    mat=material(owner,q,diagnostics=output);write(output/'beam-material.json',mat)
    work=core.pairing(loads[ns:],beam.coordinates);error=abs(2*mat['stored_energy_exact']-work)/max(abs(work),F.from_float(1e-12))
    if error>F.from_float(1e-8):raise ValueError('actual represented material energy/work failed')
    beam_res=tuple(v-F.from_float(float(f)) for v,f in zip(action(owner._K[ns:,ns:],beam.coordinates),loads[ns:]))
    write(output/'beam-wrench.json',dict(residual=text(check_wrench(rigid,np.zeros(len(beam_res)),beam_res))))
    q=core.TwofoldVector(np.r_[shell.coordinates.high,beam.coordinates.high],np.r_[shell.coordinates.low,beam.coordinates.low])
    points=[];state=original.matched.reference_state(owner)
    for op,slots,weight,edge,alpha in owner._line_samples:
        response=op.evaluate(np.zeros((2,6)),state,np.zeros(5))
        gap=action(response.gap_jacobian,core.TwofoldVector(q.high[slots],q.low[slots]))
        points.append(dict(edge=int(edge),alpha=float(alpha),weight=float(weight),gap_exact=text(gap)))
    native={name:core.pairing(loads[sl],coord) for name,sl,coord in (('shell',slice(None,ns),shell.coordinates),('beam',slice(ns,None),beam.coordinates))}
    result=dict(identity=IDENTITY,status='DEVELOPMENT_SAME_DENSITY_WORK_NOT_ACCEPTED',inventory=inventory,
        coordinates_hi=q.high.tolist(),coordinates_lo=q.low.tolist(),native_work_exact=native,
        effective_work_ratio={n:float(v/F.from_float(reference['body'][n]['paired_work_J'])) for n,v in native.items()},
        energy_error=str(core._decimal(error)),point_gaps=points,integrated_gap_exact=text(action(owner._C,q)),
        limitations='Same-density effective work only. Common-action subset and unmatched broken-cell trace limits remain; no coupled/accuracy/qualification claim.')
    write(output/'result.json',result);return result



