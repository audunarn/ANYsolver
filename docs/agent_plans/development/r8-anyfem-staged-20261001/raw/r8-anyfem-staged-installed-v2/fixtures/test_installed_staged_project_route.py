from dataclasses import replace
import numpy as np
import pytest
from anysolver import stiffened_shell as ss
from anyfem.io.project_file import save_project,load_project
from anyfem.model.project import Project
from anyfem.model.records import AnalysisDefinition
from anyfem.solve.stiffened_shell_project import point_panel_from_analysis,solve_point_panel
from test_experimental_stiffened_shell_consumer import _case

@pytest.mark.parametrize('s3',(False,True))
def test_installed_staged_project_owner_restart_and_continue(tmp_path,s3):
    base=replace(_case(),actions=())
    if s3:
        shell=replace(base.shell,q4_elements=(),s3_elements=tuple(t for a,b,c,d in base.shell.q4_elements for t in ((a,b,c),(a,c,d))))
        base=replace(base,shell=shell)
    initial=base.create_analysis()
    try:model=initial.preflight()['identity']
    finally:initial.close()
    programme=ss.StagedDeadLoadProgramme(model,((ss.NodalAction('beam',105,(0.,0.,100.,0.,0.,0.)),),(ss.NodalAction('beam',105,(0.,30.,100.,0.,0.,0.)),)))
    panel=replace(base,load_programme=programme)
    project=Project(name='installed staged '+('S3' if s3 else 'Q4'))
    record=AnalysisDefinition.experimental_point_panel('staged',panel);project.analyses[record.id]=record
    reopened=load_project(save_project(project,tmp_path/'staged.anyfem'))
    restored_record=reopened.analyses[record.id];restored_panel=point_panel_from_analysis(restored_record)
    assert restored_panel.to_dict()==panel.to_dict()
    options=dict(max_iterations=20,max_backtracks=12)
    dispatched=solve_point_panel(restored_record,targets=(.5,1.,1.5,2.),**options)
    assert dispatched.status=='completed' and dispatched.load_programme_complete
    assert dispatched.load_position==2. and dispatched.load_programme_identity==programme.identity
    owners=[restored_panel.create_analysis() for _ in range(3)]
    try:
        control,prefix,resumed=owners
        final=control.solve(restored_panel.load_input,(.5,1.,1.5,2.),**options)
        accepted=prefix.solve(restored_panel.load_input,(.5,1.),**options)
        checkpoint=prefix.checkpoint();(tmp_path/'accepted.checkpoint').write_bytes(checkpoint)
        direct=resumed.restore(checkpoint)
        assert direct.load_position==1. and accepted.load_position==1.
        continued=resumed.solve(restored_panel.load_input,(1.5,2.),**options)
        assert final.accepted_factors==continued.accepted_factors==(.5,1.,1.5,2.)
        for result in (dispatched,final,continued):
            assert result.free_equilibrium_ratio<=1e-8 and result.constraint_max<=1e-9
            assert result.load_stage_cursor==2 and result.load_stage_fraction==0.
        for field in ('shell_displacement','beam_positions','beam_frames','cell_frames','cell_resultants','multipliers','support_reactions','applied_dead_load'):
            np.testing.assert_allclose(getattr(final,field),getattr(continued,field),rtol=1e-8,atol=1e-10)
            np.testing.assert_array_equal(getattr(final,field),getattr(dispatched,field))
        assert final.load_programme_identity==continued.load_programme_identity==programme.identity
    finally:
        for owner in owners:owner.close()
