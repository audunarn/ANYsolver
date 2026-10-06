"""Opt-in connected centered elastic native dynamics DEVELOPMENT API.

Source candidate: no qualification, contact or generic FEModel admission.
"""
from ._ge_beam3_connected_dynamic import (ConnectedDynamicAnalysis, ConnectedState,
    ConnectedCandidate, PROFILE, SCHEMA)

SELECTOR='ge_beam3_connected_centered_elastic_dynamic_dev'


def create_analysis(formulation,definitions,boundaries, *, inertia_order=24,
                    max_iterations=12,max_backtracks=8):
    if formulation!=SELECTOR:raise ValueError('explicit connected dynamic selector required')
    return ConnectedDynamicAnalysis(definitions,boundaries,inertia_order=inertia_order,
        max_iterations=max_iterations,max_backtracks=max_backtracks)
