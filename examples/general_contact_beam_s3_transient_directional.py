"""Exact binary axis-aligned full-line first touch; source development only."""
from examples.general_contact_beam_s3_transient_rotational import build as rotational_build
from anysolver.general_contact.transient import solve_transient_contact,ContactTransientSolverControls
from anysolver.dynamics import TransientConfig


def build():
    model,definition,settings,velocity=rotational_build()
    for node in (1,6,2):model.mesh.nodes[node].z=.02
    model.mesh.bump_revision('geometry')
    return model,definition,settings,velocity


def run(*,end=2.e-5,restart=None):
    m,d,s,v=build()
    result=solve_transient_contact(m,d,TransientConfig(1.e-5,end,initial_velocity=v),
        contact_settings=s,solver_controls=ContactTransientSolverControls(
            allow_directional_beam_s3_dev=True,save_constraint_reactions_dev=True),
        emit_restart_checkpoint=True,restart_checkpoint=restart)
    return m,result
