# Curved distributed-load continuum comparison

Parent: `0d3046c690d96f0febe8a03b2334fd656c14c2b4`. No runtime mechanics,
section, mass, state, load module, public adapter, default or historical evidence
is changed. This wave adds an independent-algorithm reference and comparison.

## Source and reference problem

The static continuum equations are equations (20)–(23) of
[Humer–Steinbrecher–Pechstein, version 1](https://arxiv.org/html/2605.04573v1#S2.SS4):
spatial force balance, spatial moment balance, material pull-back and virtual
work. Use the already declared curved-moment fixture's parabolic reference and
fully coupled positive-definite elastic section, with zero natural stress.
The new BVP is separately reconstructed and imports no native beam mechanics,
recovery, cached stiffness or legacy operators. Authorship and independent
review remain explicitly pending; this is not a multiprecision certificate.

Freeze `t in [-1,1]`, `r0=(t,0.15*(1-t^2),0)`, physical second director `+z`,
and spatial line force `(0.3,-0.2,0.1)` per reference arclength. Clamp the root
position and complete director triad; leave the tip force and moment zero.
Load targets are `0.25, 0.5, 1.0`. Native meshes have exactly 1, 2 and 4 macros.
All three meshes use the existing physical-fibre elastic fixture with its
unchanged four-point rule per cell. No loads or coefficients are selected from
the comparison results.

In the continuum, `n=f*(L-s)`, `m_s=-r_s cross n`,
`r_s=Q*(e1+gamma)`, `Q_s=Q*hat(kappa0+kappa)`, with the complete coupled elastic
relation `[gamma,kappa]=C^-1*[Q^T*n,Q^T*m]`. Integrate physical directors directly
without projection. The parabolic reference arclength is evaluated analytically.
An energy accumulator has zero root value. Tip moment is a boundary condition.

Use independent collocation profiles BVP7 (tolerance `1e-7`, at most 1025 mesh
nodes) and BVP9 (`1e-9`, 4097 nodes), each capped at 4000 RHS calls and 60 seconds.
The reference checks director orthogonality, boundary/differential residuals,
positive axial stretch, zero-load curved geometry, exact distributed axial
loading, and independently integrated load lever-arm balance. Numerical BVP
Jacobian estimation is reference-side only; no production frame derivative is
introduced or changed.

## Comparison and execution

First run the complete small rehearsal. After freezing, run one contained wave:
three native paths, six reference solves, nine state/recovery records and 168
station records. Sample each reference at all exact declared native stations;
do not interpolate historical samples. Save complete native checkpoints,
recovery arrays and both reference profiles externally. Independently reconstruct
the discrete load's force and moment work using the prior rational-Q2 oracle.
Require native equilibrium/action–reaction `1e-11` and profile differences
`1e-7`; report continuum response/field errors and refinement trends as
diagnostics, not an element qualification or a tuned pass threshold.

Use a clean source guard before imports and after cleanup. Every output is
exclusive; canonical summary is promoted only after worker completion,
successful semantic/hash checks and full process-tree cleanup. One numerical
thread, 24 GiB process-tree memory, 600 seconds wall and 120 seconds inactivity
per wave; native contexts retain 120 seconds. There are no automatic retries.
Preserve failures and partial logs; never fabricate a completed aggregate.

The initial reference-only inventory passed 13 tests in 0.60 pytest seconds
(2.012 supervised seconds), at
`C:/Users/AUDUNA~1/AppData/Local/Temp/ge-beam3-dead-line-reference-xavt84n1`.
This is separate from the complete rehearsal inventory and the frozen wave.
