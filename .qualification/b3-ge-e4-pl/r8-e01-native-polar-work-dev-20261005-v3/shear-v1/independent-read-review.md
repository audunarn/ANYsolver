# Supporting independent Read mechanics review - 5 October 2026

Reviewer: /root/fast_test_runner (OpenAI, not the implementation author).
Read only; no numerical executions or edits.

For reference half-chord length L, native strain is Rc.T(d/L)-ex; current
chord normalization would lose axial stretch and is not used. With
D=sqrt(4+gamma^2):
- ux=gamma*y: polar=(2/D-1,gamma/D,0); material-line=(0,0,0).
- uy=gamma*x: polar=((2+gamma^2)/D-1,gamma/D,0);
  material-line=(sqrt(1+gamma^2)-1,0,0).
- symmetric shear: polar=(0,gamma,0);
  material-line=(sqrt(1+gamma^2)-1,0,0).
- F3x=h and independent director ez: both=(0,0,h).
- common finite rigid motion: both zero.

The vertical eccentric arms and L1 surface offset reconcile consistently.
In-plane comparisons have the same beam positions but DIFFERENT prescribed
section rotations. No scoped geometry/support contradiction was found.
Zero gaps establish compatibility with each declared law; they do not
establish equilibrium, constitutive work, welded-line equivalence, finite
footprint accuracy or a preferred physical law. This is supporting review,
not required different-family scientific acceptance.

Root decision: retain distinct law identities. Do not replace existing
point/BL5 operators or claim multiplier enrichment can remove this continuous
law difference. Stop local refinement aimed at equivalence. Physical adoption
requires a declared finite connection idealization and matched section-rotation/
shear/work evidence; no structural/external execution automatically follows.
