from pathlib import Path

raw=Path(__file__).resolve().parent
repo=raw.parents[2]
def edit(relative, pairs):
    path=repo/relative
    original=path.read_bytes()
    saved=raw/'before-v1'/relative
    saved.parent.mkdir(parents=True,exist_ok=True)
    saved.write_bytes(original)
    text=original.decode('utf-8').replace('\r\n','\n')
    for old,new in pairs:
        assert text.count(old)==1,(relative,old[:100],text.count(old))
        text=text.replace(old,new)
    path.write_bytes(text.encode('utf-8'))

edit('src/anysolver/_stiffened_shell_affine_endpoint.py',[
('def has_shell_material(owner):', '''def is_native_point_material(owner):
    """Narrow fixed-target native-fibre/mixed beam route, elastic flat full-map Q4."""
    if not getattr(owner,"_has_physical_fibre",False):
        return False
    from ._stiffened_shell_q4_algorithmic_adapter import POLICY
    definition=owner._definition
    return bool(definition.points and definition.shell.q4_elements and
        not definition.shell.s3_elements and definition.shell.j2_curve is None and
        definition.shell_reference_policy=="flat" and definition.q4_pullback_policy==POLICY and
        not definition.lines and not definition.footprints and
        not definition.distributing_footprints and not definition.finite_distributing_footprints)


def has_shell_material(owner):'''),
('if not (owner._bl5_shell_material or getattr(owner,"_curved_reference",False)):',
 'if not (owner._bl5_shell_material or getattr(owner,"_curved_reference",False) or is_native_point_material(owner)):'),
('beam_parent=_material_histories(prepared,a["beam_origin_plastic"],a["beam_origin_accumulated"])\n    # Validate accepted beam history admissibility before replay comparison.\n    _material_histories(prepared,a["beam_plastic"],a["beam_accumulated"])',
 '''native=is_native_point_material(owner)
    if native:
        from ._stiffened_shell_beam_history import histories
        beam_parent=histories(prepared._beam_parts,a,"beam_origin")
        histories(prepared._beam_parts,a,"beam")
    else:
        beam_parent=_material_histories(prepared,a["beam_origin_plastic"],a["beam_origin_accumulated"])
        # Validate accepted beam history admissibility before replay comparison.
        _material_histories(prepared,a["beam_plastic"],a["beam_accumulated"])'''),
('bp,ba=_material_arrays(evaluation[5])\n    comparisons=[("beam_plastic",bp),("beam_accumulated",ba)]',
 '''if native:
        from ._stiffened_shell_beam_history import arrays
        comparisons=list(arrays(prepared._beam_parts,evaluation[5],"beam"))
    else:
        bp,ba=_material_arrays(evaluation[5])
        comparisons=[("beam_plastic",bp),("beam_accumulated",ba)]'''),
])
edit('src/anysolver/_stiffened_shell_displacement_checkpoint.py',[
('if getattr(owner,"_curved_material",False):',
 '''from ._stiffened_shell_affine_endpoint import is_native_point_material
    if is_native_point_material(owner):
        return ("finite_displacement_native_point_material",
                "B3_GE_NATIVE_POINT_MATERIAL_DISPLACEMENT_V1_DEV",None,None)
    if getattr(owner,"_curved_material",False):'''),
('if getattr(owner,"_curved_material",False) and not has_shell_material(owner):',
 '''from ._stiffened_shell_affine_endpoint import is_native_point_material
    if is_native_point_material(owner):
        from ._stiffened_shell_beam_history import shapes
        return layout[:12]+shapes(owner._beam_parts,"beam")+shapes(owner._beam_parts,"beam_origin")
    if getattr(owner,"_curved_material",False) and not has_shell_material(owner):'''),
('kind,policy,chart_policy,event_policy=identities(owner)\n    steps=len(arrays["history"])',
 '''kind,policy,chart_policy,event_policy=identities(owner)
    if chart_policy is None and (chart_events or trial_policy is not None):
        raise ValueError("native point displacement excludes chart/event policies")
    steps=len(arrays["history"])'''),
('chart_events=m.get("chart_events",0)\n    if (canonical!=header',
 '''chart_events=m.get("chart_events",0)
    if chart_policy is None and (m.get("policy")!=policy or set(m)!=base_keys):
        raise ValueError("native point displacement excludes chart/event policies")
    if (canonical!=header'''),
])
edit('src/anysolver/_stiffened_shell_ge_checkpoint_binary.py',[
('    "finite_displacement_curved_material":',
 '    "finite_displacement_native_point_material": "B3_GE_E4_PL_NATIVE_POINT_MATERIAL_DISPLACEMENT_MECHANICS_V1_DEV",\n    "finite_displacement_curved_material":')])
edit('src/anysolver/_stiffened_shell_displacement_corrector.py',[
('    if driver._accepted is None or not (\n            owner._bl5_shell_material or getattr(owner,"_curved_material",False)):',
 '''    from ._stiffened_shell_affine_endpoint import is_native_point_material
    native=is_native_point_material(owner)
    if native and trial_policy is not None:
        raise ValueError("native point displacement excludes branch event policy")
    if driver._accepted is None or not (
            owner._bl5_shell_material or getattr(owner,"_curved_material",False) or native):''')])
edit('src/anysolver/_stiffened_shell_displacement_control.py',[
('    beam_generalized_material: tuple = ()',
 '    beam_generalized_material: tuple = ()\n    beam_fibre_material: tuple = ()\n    beam_fibre_energy: tuple = ()'),
('    beam_next=_material_histories(owner,a["beam_plastic"],a["beam_accumulated"])',
 '''    from ._stiffened_shell_affine_endpoint import is_native_point_material
    native=is_native_point_material(owner)
    if native:
        from ._stiffened_shell_beam_history import histories
        beam_next=histories(owner._beam_parts,a,"beam")
    else:
        beam_next=_material_histories(owner,a["beam_plastic"],a["beam_accumulated"])'''),
('beam_generalized_material=driver._generalized_records(state,beam_parent,beam_next))',
 '''beam_generalized_material=driver._generalized_records(state,beam_parent,beam_next,include_native=native))
    if native:
        from ._stiffened_shell_ge_finite_experimental import _fibre_recovery
        records,energies=_fibre_recovery(owner,state,beam_parent,beam_next)
        result=replace(result,beam_fibre_material=records,beam_fibre_energy=energies)'''),
('    if type(control) is not DisplacementControl or not (\n            owner._bl5_shell_material or getattr(owner,"_curved_material",False)):',
 '''    from ._stiffened_shell_affine_endpoint import is_native_point_material
    native=is_native_point_material(owner)
    if native and (_adaptive is not None or control.trial_policy is not None):
        raise ValueError("native point displacement admits fixed targets without branch event policy")
    if type(control) is not DisplacementControl or not (
            owner._bl5_shell_material or getattr(owner,"_curved_material",False) or native):'''),
('        arrays["beam_plastic"],arrays["beam_accumulated"]=_material_arrays(trial.evaluation[5])\n        arrays["beam_origin_plastic"],arrays["beam_origin_accumulated"]=_material_arrays(trial.beam_predecessor)',
 '''        if native:
            from ._stiffened_shell_beam_history import arrays as native_arrays
            arrays.update(native_arrays(owner._beam_parts,trial.evaluation[5],"beam"))
            arrays.update(native_arrays(owner._beam_parts,trial.beam_predecessor,"beam_origin"))
        else:
            arrays["beam_plastic"],arrays["beam_accumulated"]=_material_arrays(trial.evaluation[5])
            arrays["beam_origin_plastic"],arrays["beam_origin_accumulated"]=_material_arrays(trial.beam_predecessor)'''),
('    if type(expected_generation) is not int or expected_generation!=owner._generation:',
 '''    from ._stiffened_shell_affine_endpoint import is_native_point_material
    if is_native_point_material(owner):
        raise ValueError("native point displacement chart rebasing is not admitted")
    if type(expected_generation) is not int or expected_generation!=owner._generation:'''),
])
edit('src/anysolver/_stiffened_shell_ge_finite_experimental.py',[
('if owner._bl5_material or owner._curved_material or owner._distributing_material:',
 'if owner._bl5_material or owner._curved_material or owner._distributing_material or owner._has_physical_fibre:'),
('def _generalized_records(self,state,origins,accepted):\n        if not (self.owner._bl5_material or self.owner._curved_material or self.owner._distributing_material):return ()',
 '''def _generalized_records(self,state,origins,accepted,*,include_native=False):
        if not (self.owner._bl5_material or self.owner._curved_material or self.owner._distributing_material or
                (include_native and self.owner._has_physical_fibre)):return ()'''),
])
edit('src/anysolver/_stiffened_shell_ge_experimental.py',[
('        if self._bl5_shell_material:\n            capabilities["displacement_control"]',
 '''        from ._stiffened_shell_affine_endpoint import is_native_point_material
        if is_native_point_material(self):
            capabilities["displacement_control"] = "experimental_native_point_material_fixed_translation_v1"
        if self._bl5_shell_material:
            capabilities["displacement_control"]'''),
('        if displacement_control is not None:\n            if self._unsupported_modes:',
 '''        if displacement_control is not None:
            from ._stiffened_shell_affine_endpoint import is_native_point_material
            if is_native_point_material(self) and increment_control is not None:
                raise ValueError("native point displacement admits fixed targets only")
            if self._unsupported_modes:'''),
])
print('Prepared scoped native point displacement source delta; no numerical work launched.')
