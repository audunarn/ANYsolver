"""Inert nonrigid B31 tip-work probe for the separately qualified knot deck."""

from __future__ import annotations

import generate_b3_e4_ccx_3d_knot_patch as knot
import generate_b3_e4_ccx_3d_reciprocity_influences as old


def build_tip_work_deck(signed_delta:float) -> str:
    """Load the tip in y with signed beam-root-y motion and expanded U."""
    if signed_delta not in (-old.DELTA,old.DELTA):
        raise ValueError("only the frozen signed influence amplitude is admitted")
    source=knot.build_knot_rigid_deck(1,signed_delta)
    first="*BOUNDARY\n"
    last="*NODE PRINT,NSET=AllNodes\n"
    before,tail=source.split(first,1)
    current,after=tail.split(last,1)
    rows=current.splitlines()
    if len(rows)!=36:
        raise ValueError("source support inventory changed")
    motion=old.support_motion("beam",1,signed_delta)
    boundary=[f"{node},{dof},{dof},{old.checked_boundary_token(f'{value:.12g}')}"
              for (node,dof),value in sorted(motion.items())]
    # Keep the original DAT node output; request expanded 3D displacement
    # output in FRD as a second, independent representation of tip work.
    if after!="U\nRF\n*END STEP\n":
        raise ValueError("source output inventory changed")
    deck=before+first+"\n".join(boundary)+"\n*CLOAD\n48,2,1000\n"+last+after.replace(
        "*END STEP\n","*NODE FILE,OUTPUT=3D\nU\n*END STEP\n")
    if (deck.count("*NODE FILE,OUTPUT=3D\n")!=1 or
            deck.count("*BOUNDARY\n")!=1 or len(boundary)!=36 or
            deck.count("*CLOAD\n48,2,1000\n")!=1 or
            deck.count("*EQUATION\n")!=12 or
            deck.count("*BEAM SECTION")!=2):
        raise ValueError("tip-work deck inventory changed")
    return deck
