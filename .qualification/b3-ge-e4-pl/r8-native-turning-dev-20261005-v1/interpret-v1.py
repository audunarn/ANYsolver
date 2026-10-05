"""One endpoint replay to interpret the saved path; no continued stepping."""
from pathlib import Path
import ast,json
from dataclasses import asdict
import numpy as np
from scipy.spatial.transform import Rotation
raw=Path(__file__).resolve().parent
source=raw/'screen-v1.py'
tree=ast.parse(source.read_bytes());prefix=[]
for statement in tree.body:
    if isinstance(statement,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='record' for t in statement.targets):break
    prefix.append(statement)
namespace=dict(__file__=str(source),__name__='fixture_only')
exec(compile(ast.Module(body=prefix,type_ignores=[]),str(source),'exec'),namespace)
ss=namespace['ss'];model=namespace['model'];xyz=namespace['xyz'];frames=namespace['frames']
owner=ss.create_analysis(definition=model)
try:
    checkpoint=(raw/'last-prefix.checkpoint').read_bytes();result=owner.restore(checkpoint)
    assert owner.checkpoint()==checkpoint
    shell_u=result.shell_displacement.reshape(-1,6)[:,:3]
    beam_u=result.beam_positions-xyz
    shell_spin=Rotation.from_matrix(result.shell_frames).as_rotvec()
    beam_spin=Rotation.from_matrix(result.beam_frames@frames.transpose(0,2,1)).as_rotvec()
    weights=namespace['weights']
    translations=np.concatenate((shell_u,beam_u))
    rotational_chord=np.concatenate((.5*np.sum((result.shell_frames-np.eye(3))**2,axis=(1,2)),
        .5*np.sum((result.beam_frames-frames)**2,axis=(1,2))))
    translation_terms=weights*np.sum(translations**2,axis=1)
    rotation_terms=weights*rotational_chord
    record=dict(status='INTERPRETED_SAVED_ENDPOINT_NO_NEW_STEPS',exact_checkpoint=True,
        shell_displacements=shell_u.tolist(),beam_displacements=beam_u.tolist(),
        shell_spins=shell_spin.tolist(),beam_spins=beam_spin.tolist(),
        metric_translation_terms=translation_terms.tolist(),metric_rotation_terms=rotation_terms.tolist(),
        point_wrenches=[asdict(x) for x in result.point_wrenches],
        beam_station_records=[asdict(x) for x in result.beam_generalized_material],
        eq=result.free_equilibrium_ratio,gap=result.constraint_max)
    def convert(value):
        if isinstance(value,np.ndarray):return value.tolist()
        if isinstance(value,np.generic):return value.item()
        raise TypeError(type(value).__name__)
    (raw/'interpretation-v1.json').write_bytes((json.dumps(record,default=convert,indent=2)+'\n').encode('ascii'))
    print(json.dumps(dict(exact_checkpoint=True,eq=result.free_equilibrium_ratio,
        beam_max_lateral=float(np.max(np.abs(beam_u[:,1]))),
        shell_max_lateral=float(np.max(np.abs(shell_u[:,1]))),
        max_shell_spin=float(np.max(np.linalg.norm(shell_spin,axis=1))),
        max_beam_spin=float(np.max(np.linalg.norm(beam_spin,axis=1))),
        metric_translation=float(np.sum(translation_terms)),metric_rotation=float(np.sum(rotation_terms)))))
finally:owner.close()
