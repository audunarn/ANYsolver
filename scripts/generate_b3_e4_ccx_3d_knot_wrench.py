"""Inert loaded and reciprocal decks for the separately accepted knot comparator.

The earlier no-knot 24-case wrench result remains failed. This is a new
discrete external model with independently screened rigid and tip-work maps.
"""

from __future__ import annotations

import generate_b3_e4_ccx_3d_knot_patch as knot
import generate_b3_e4_ccx_3d_reciprocity_influences as old


def _replace_supports(deck:str,motion:dict[tuple[int,int],float],
                      *,load:bool)->str:
    head,tail=deck.split("*BOUNDARY\n",1)
    present,rest=tail.split("*NODE PRINT,NSET=AllNodes\n",1)
    if len(present.splitlines())!=36 or rest!="U\nRF\n*END STEP\n":
        raise ValueError("knot comparator support/output inventory changed")
    if set(motion)!=set(old.support_motion("beam",0,old.DELTA)):
        raise ValueError("changed support coordinate inventory")
    rows=[f"{node},{dof},{dof},{old.checked_boundary_token(f'{value:.12g}')}"
          for (node,dof),value in sorted(motion.items())]
    cards="*BOUNDARY\n"+"\n".join(rows)+"\n"
    if load:
        cards+="*CLOAD\n48,2,1000\n"
    result=head+cards+"*NODE PRINT,NSET=AllNodes\n"+rest
    if (result.count("*BOUNDARY\n")!=1 or result.count("*EQUATION\n")!=12 or
            result.count("*BEAM SECTION")!=2 or
            result.count("*CLOAD\n")!=int(load)):
        raise ValueError("knot wrench deck inventory changed")
    return result


def build_loaded_baseline()->str:
    """A fixed-support 1000 N tip-y baseline on the knot-based geometry."""
    deck=knot.build_knot_rigid_deck(0,old.DELTA)
    zero={key:0. for key in old.support_motion("beam",0,old.DELTA)}
    return _replace_supports(deck,zero,load=True)


def build_unloaded_influence(group:str,component:int,signed_delta:float)->str:
    """One prescribed support-work basis, with no tip force."""
    deck=knot.build_knot_rigid_deck(component,signed_delta)
    motion=old.support_motion(group,component,signed_delta)
    return _replace_supports(deck,motion,load=False)
