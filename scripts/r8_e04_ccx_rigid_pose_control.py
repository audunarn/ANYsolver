"""Finite rigid-port mapping control, not a flexible beam/shell reference.

CalculiX *RIGID BODY is supported for these element-free marker nodes, not
original beam/shell nodes. A separate grounded spring keeps one solved equation.
The marker triad represents the declared E04 rectangular section frame only;
it supplies no beam or shell stiffness. Execute under the existing supervisor.
"""
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

ANGLE=.05
OFFSET=(.0127+.0254)/2
ROTATION=np.array((.4,-.3,.2))
TRANSLATION=np.array((.01,-.02,.03))
FORCE=np.array((7.,-3.,5.))
BEAM_FRAME=Rotation.from_rotvec((-ANGLE,0.,0.)).as_matrix()
BEAM_POSITION=OFFSET*BEAM_FRAME[:,2]
MARKERS=np.array((BEAM_POSITION,BEAM_POSITION+.05*BEAM_FRAME[:,0],
                  BEAM_POSITION+.00635*BEAM_FRAME[:,1]))
SPRING_STIFFNESS=100.


def deck():
    nodes={i+1:p for i,p in enumerate(MARKERS)}
    nodes.update({100:np.zeros(3),101:np.zeros(3),200:np.array((1.,0.,0.))})
    lines=['*HEADING','E04 finite rigid port development control','*NODE']
    lines += [','.join((str(i),*(f'{v:.17g}' for v in p))) for i,p in nodes.items()]
    lines += ['*NSET,NSET=Markers','1,2,3','*NSET,NSET=Ports','1,2,3,100,101,200',
        '*ELEMENT,TYPE=SPRING1,ELSET=Control','1,200','*SPRING,ELSET=Control','1','1000.',
        '*RIGID BODY,NSET=Markers,REF NODE=100,ROT NODE=101','*BOUNDARY',
        '100,1,3,0.','101,1,3,0.','200,2,3,0.',
        '*STEP,NLGEOM,INC=100','*STATIC','.1,1.,1e-6,.1','*BOUNDARY']
    for node,value in ((100,TRANSLATION),(101,ROTATION)):
        lines += [f'{node},{j+1},{j+1},{v:.17g}' for j,v in enumerate(value)]
    lines += ['*CLOAD',*(f'1,{j+1},{v:.17g}' for j,v in enumerate(FORCE)),
        '200,1,1.','*NODE PRINT,NSET=Ports,FREQUENCY=1','U,RF','*END STEP']
    return '\n'.join(lines)+'\n'


def expected():
    matrix=Rotation.from_rotvec(ROTATION).as_matrix()
    positions=MARKERS@matrix.T+TRANSLATION
    angle=np.linalg.norm(ROTATION)
    cross=np.array(((0.,-ROTATION[2],ROTATION[1]),(ROTATION[2],0.,-ROTATION[0]),
                    (-ROTATION[1],ROTATION[0],0.)))
    jacobian=np.eye(3)+(1-np.cos(angle))/angle**2*cross+(angle-np.sin(angle))/angle**3*cross@cross
    spatial_moment=np.cross(matrix@BEAM_POSITION,FORCE)
    return dict(marker_displacements=(positions-MARKERS).tolist(),
        reference_displacement=TRANSLATION.tolist(),rotation_coordinate=ROTATION.tolist(),
        reference_reaction=(-FORCE).tolist(),
        rotation_coordinate_reaction=(-jacobian.T@spatial_moment).tolist(),
        spatial_reaction_moment=(-spatial_moment).tolist(),control_displacement=.001)


def free_spring_deck():
    """Free six-DOF rigid carrier on nine linear Cartesian grounded springs."""
    lines=['*HEADING','E04 free finite rigid carrier on known springs','*NODE']
    lines += [','.join((str(i+1),*(f'{v:.17g}' for v in p))) for i,p in enumerate(MARKERS)]
    lines += ['100,0.,0.,0.','101,0.,0.,0.','*NSET,NSET=Markers','1,2,3',
              '*NSET,NSET=Ports','1,2,3,100,101']
    for direction in (1,2,3):
        lines += [f'*ELEMENT,TYPE=SPRING1,ELSET=D{direction}']
        lines += [f'{3*(direction-1)+node},{node}' for node in (1,2,3)]
        lines += [f'*SPRING,ELSET=D{direction}',str(direction),str(SPRING_STIFFNESS)]
    lines += ['*RIGID BODY,NSET=Markers,REF NODE=100,ROT NODE=101',
        '*STEP,NLGEOM,INC=200','*STATIC','.05,1.,1e-6,.05','*CLOAD',
        *(f'1,{j+1},{v:.17g}' for j,v in enumerate(FORCE)),
        '*NODE PRINT,NSET=Ports,FREQUENCY=1','U,RF','*END STEP']
    return '\n'.join(lines)+'\n'


def free_spring_expected(force=FORCE):
    """Global minimizer of 1/2 k sum|R r_i+t-r_i|² - F·u_1.

    Eliminating translation leaves maximization of tr(R A), where
    A=k sum p_i p_i^T+p_1 F^T and p_i=r_i-mean(r). Proper orthogonal
    Procrustes supplies the remaining finite rotation without Newton iteration.
    """
    force=np.asarray(force,dtype=float)
    center=MARKERS.mean(axis=0);centered=MARKERS-center
    action=SPRING_STIFFNESS*centered.T@centered+np.outer(centered[0],force)
    u,s,vh=np.linalg.svd(action)
    sign=np.linalg.det(vh.T@u.T)
    matrix=vh.T@np.diag((1.,1.,sign))@u.T
    translation=force/(3*SPRING_STIFFNESS)-(matrix-np.eye(3))@center
    positions=MARKERS@matrix.T+translation
    displacement=positions-MARKERS
    net_force=force-SPRING_STIFFNESS*displacement.sum(axis=0)
    net_moment=np.cross(positions[0],force)-SPRING_STIFFNESS*np.cross(positions,displacement).sum(axis=0)
    assert np.linalg.norm(net_force)<1e-12 and np.linalg.norm(net_moment)<1e-12
    return dict(marker_displacements=displacement.tolist(),reference_displacement=translation.tolist(),
        rotation_coordinate=Rotation.from_matrix(matrix).as_rotvec().tolist(),
        net_force=net_force.tolist(),net_moment=net_moment.tolist(),singular_values=s.tolist(),
        energy=float(.5*SPRING_STIFFNESS*np.sum(displacement**2)-force@displacement[0]))


def report(folder, *, free_springs=False):
    """Compare final printed output; retain its quantization explicitly."""
    import re
    import math
    import hashlib
    expected_deck=free_spring_deck() if free_springs else deck()
    actual_deck=(folder/'pose.inp').read_bytes()
    # Windows text writers encode LF as CRLF. Compare only that transport
    # normalization; preserve the executed byte identity separately.
    if actual_deck.replace(b'\r\n',b'\n')!=expected_deck.encode('ascii'):
        raise ValueError('executed deck differs from this control contract')
    text=(folder/'stdout.log').read_text()
    if ('Job finished' not in text or re.search(r'\*(?:WARNING|ERROR|FATAL)',text)
            or (folder/'stderr.log').read_text().strip()):
        raise ValueError('external execution did not finish cleanly')
    lines=(folder/'pose.dat').read_text().splitlines();values={};radii={}
    start=max(i for i,line in enumerate(lines) if line.strip().startswith('displacements ('))
    if float(lines[start].split()[-1])!=1.:
        raise ValueError('final prescribed load time was not reached')
    for line in lines[start+1:]:
        fields=line.split()
        if len(fields)!=4 or not fields[0].isdigit():
            if values:break
            continue
        node=int(fields[0])
        if node in values:
            raise ValueError('duplicate displacement node in final output')
        values[node]=[float(x) for x in fields[1:]]
        floors=[]
        for token in fields[1:]:
            mantissa,exponent=token.upper().split('E')
            digits=len(mantissa.split('.')[1])
            floors.append(.5*10**(int(exponent)-digits)+4*math.ulp(float(token)))
        radii[node]=floors
    required={1,2,3,100,101} | (set() if free_springs else {200})
    if set(values)!=required or not np.isfinite(list(values.values())).all():
        raise ValueError('complete finite final displacement output required')
    oracle=free_spring_expected() if free_springs else expected()
    errors={};compatible=True
    for node,expected_value in [(i+1,p) for i,p in enumerate(oracle['marker_displacements'])]+[
            (100,oracle['reference_displacement']),(101,oracle['rotation_coordinate'])]:
        difference=np.asarray(values[node])-expected_value;floor=np.array(radii[node])
        errors[node]=dict(absolute_error=difference.tolist(),rounding_floor=floor.tolist())
        if node!=101:
            compatible=compatible and bool(np.all(abs(difference)<=floor+1e-14))
    # ROT coordinates diagnose the chart convention; equivalent vectors do not
    # change the physical rotation and must not alone reject physical poses.
    observed_rotation=Rotation.from_rotvec(values[101]).as_matrix()
    oracle_rotation=Rotation.from_rotvec(oracle['rotation_coordinate']).as_matrix()
    answer=dict(displacements=values,errors=errors,oracle_print_rounding_bounds_compatible=compatible,
        executed_deck_sha256=hashlib.sha256(actual_deck).hexdigest(),
        programme_tolerance_pass=None,scope='finite rigid marker port only; no shell/beam stiffness',
        physical_rotation_error=float(np.linalg.norm(observed_rotation-oracle_rotation)),
        physical_rotation_rounding_bound=float(np.sqrt(2)*np.linalg.norm(radii[101])+1e-14))
    compatible=compatible and answer['physical_rotation_error']<=answer['physical_rotation_rounding_bound']
    answer['oracle_print_rounding_bounds_compatible']=compatible
    if free_springs:
        disp=np.array([values[i] for i in (1,2,3)]);position=MARKERS+disp
        force=FORCE-SPRING_STIFFNESS*disp.sum(axis=0)
        moment=np.cross(position[0],FORCE)-SPRING_STIFFNESS*np.cross(position,disp).sum(axis=0)
        answer.update(net_force=force.tolist(),net_moment=moment.tolist(),
            energy=float(.5*SPRING_STIFFNESS*np.sum(disp**2)-FORCE@disp[0]),
            oracle_energy=oracle['energy'])
        floors=np.array([radii[i] for i in (1,2,3)])
        force_floor=SPRING_STIFFNESS*floors.sum(axis=0)
        def skew(v):
            return np.array(((0.,-v[2],v[1]),(v[2],0.,-v[0]),(-v[1],v[0],0.)))
        moment_floor=sum(abs(-SPRING_STIFFNESS*skew(p)-(skew(FORCE) if i==0 else 0.))@floor
                         for i,(p,floor) in enumerate(zip(MARKERS,floors)))
        answer.update(force_rounding_bound=force_floor.tolist(),moment_rounding_bound=moment_floor.tolist())
    else:
        answer['port_rf_is_not_validated_wrench']=True
    return answer


if __name__=='__main__':
    import argparse,json
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--free-springs',action='store_true')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'pose.inp').write_text(free_spring_deck() if args.free_springs else deck(),encoding='ascii')
    (args.output/'expected.json').write_text(json.dumps(free_spring_expected() if args.free_springs else expected(),indent=2))
