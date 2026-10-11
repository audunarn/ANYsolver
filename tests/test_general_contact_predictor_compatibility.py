"""Legacy settings byte contracts and real opt-in public request routing."""
import copy
from dataclasses import fields,replace
import hashlib,json,os
from pathlib import Path
import numpy as np
import pytest


def legacy_settings(settings):
    # Independent pre-selector dataclass schema, preserving all prior fields.
    return {f.name:copy.deepcopy(getattr(settings,f.name)) for f in fields(settings)
            if f.name!='path_predictor'}


@pytest.mark.parametrize('kind',('caps','transient','rigid'))
def test_actual_manager_contract_matches_pre_selector_schema(kind,monkeypatch):
    if kind=='caps':
        from examples.general_contact_multiple_beam_s3_caps import build
        from anysolver.general_contact import multiple_beam_s3_caps as module
        model,definition,settings,_=build()
        manager=module.MultipleBeamS3CapManager(model,definition,settings)
        contract=manager.restart_contract()
        assert 'path_predictor' not in contract['settings']
        assert all('path_predictor' not in p['effective_settings'] for p in contract['pairs'])
        monkeypatch.setattr(module,'_contact_settings_contract',legacy_settings)
        assert manager.restart_contract()==contract
    elif kind=='transient':
        from examples.general_contact_multiple_beam_s3_transient import build
        from anysolver.general_contact import multiple_beam_s3_transient as module
        model,definition,settings,_=build()
        manager=module.MultipleBeamS3TransientManager(model,definition,settings)
        contract=manager.restart_contract()
        assert 'path_predictor' not in contract['settings']
        monkeypatch.setattr(module,'_contact_settings_contract',legacy_settings)
        assert manager.restart_contract()==contract
    else:
        from examples.general_contact_triangulated_rigid import case
        from anysolver.general_contact import triangulated_rigid_static as module
        manager=module.TriangulatedRigidManager(*case())
        contract=manager._contract_bytes()
        assert 'path_predictor' not in json.loads(contract)['settings']
        monkeypatch.setattr(module,'_contact_settings_contract',legacy_settings)
        assert manager._contract_bytes()==contract
        assert manager.restart_contract()['rigid_mesh_contract_sha256']==hashlib.sha256(contract).hexdigest()


def test_common_settings_contract_keeps_optin_and_all_prior_fields():
    from anysolver import ContactSolverSettings
    from anysolver.general_contact.core import _contact_settings_contract
    from anysolver.general_contact.automatic_domain import _settings_contract
    settings=ContactSolverSettings(path_predictor='control_projection_dev',maximum_swept_subdivisions=9)
    expected={**legacy_settings(settings),'path_predictor':'control_projection_dev'}
    assert _contact_settings_contract(settings)==expected==_settings_contract(settings)
    default=replace(settings,path_predictor='none')
    assert _contact_settings_contract(default)==legacy_settings(default)==_settings_contract(default)
    value=_contact_settings_contract(settings);value['maximum_swept_subdivisions']=999
    assert settings.maximum_swept_subdivisions==9


def test_public_optin_request_identity_then_actual_first_press():
    from anysolver import identify_general_contact_request,verify_general_contact_request,LoadCase,ContactRequestIdentityError
    from examples.general_contact_automatic_domain import build_projected_shell_pair,solve_shell_pair
    model,domain,settings,resolution,path=build_projected_shell_pair(lifecycle=True,
        path_predictor='control_projection_dev')
    controls=dict(contact_path_program=path,max_load_factor=1/3,max_iterations=15)
    identity=identify_general_contact_request(model,resolution.definition,settings,**controls)
    assert verify_general_contact_request(identity,model,resolution.definition,settings,**controls)==identity
    record=identity.to_dict()
    assert record['request']['loading']['kind']=='contact_path'
    assert record['request']['settings']['path_predictor']=='control_projection_dev'
    assert not identity.admitted_for_application
    load=LoadCase('predictor must not convert dead loads');load.add_nodal_load(1,forces=(0.,0.,-.1))
    with pytest.raises(ContactRequestIdentityError,match='path_predictor requires'):
        identify_general_contact_request(model,resolution.definition,settings,load_case=load)
    result=solve_shell_pair(model,domain,settings,resolution,path,max_load_factor=1/3)
    assert result.status=='completed' and len(result.steps)==1
    assert result.info['contact_path']['path_predictor']=='control_projection_dev'
    contact=result.info['general_contact']
    assert contact['active_pressure_dofs']>0 and contact['minimum_gap']>=-5e-5
    target=model.mesh.dof_manager.get_node_dofs(9)[2]
    assert abs(result.displacements[target])>1e-10
    result_root=os.environ.get('AUTOMATIC_DOMAIN_RESULT')
    if result_root:Path(result_root).write_text(json.dumps(dict(verified=True,
        identity=record,status=result.status,contact=contact,target_uz=float(result.displacements[target]),
        executed_selector=result.info['contact_path']['path_predictor']),indent=2,
        default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist()))
