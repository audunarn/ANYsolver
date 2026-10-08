# F03 finite-area distributing port: bounded mechanics preflight

22 September 2026. **Implemented as a separate experimental classical
connection, not a correction to the four-point reference or a selected
B3-GE/E4-PL production line law.** The earlier adverse 1% response and
reaction screens remain unchanged. G0B is open and G1 is barred.

The shell-side pose now averages the displacement field over four equal
square *material* pads centered at `(±.20, ±.23) m` relative to the line
station. A declared pad halfwidth `a` is fixed in physical metres during a
model; the numerical preflight admits `1e-4≤a≤.20 m`. That floor prevents
subresolution float clipping and is not a qualified physical pad-size
catalogue. The currently tested `.04 m` halfwidth is an illustrative
preflight geometry, **not** a size chosen to match a response or an accepted
engineering connection.

With `W_a` the four equal normalized pad-area weights and
`J_a=.20²+.23²+2a²/3`, the translational pose is
`T_s u=∫W_a(r)u(s+r)dr`, and the proper-fit yaw is
`Θ_s u=J_a⁻¹∫W_a(r)(r_x u_y−r_y u_x)dr`. The separate exact-multiplier
line work is `∫λ·[p_b−(T_s u, Θ_s u)]ds`, with `.46 m` multiplying the yaw
gap on **both** beam and shell sides. Its adjoint distributes shell load
over the actual pads. It retains the beam-root support but adds no shell
endpoint point row. The pad model differs mechanically from the four
isolated sample tracks, even when its width is small.

`_b3_e4_f03_area_port.py` clips each selected Q4 or checkerboard CST host
against each pad, integrates the bilinear/affine shape and first moment
with a degree-three triangle rule, checks complete per-pad area, and
returns a sparse physical pose. `_b3_e4_f03_area_line.py` splits at beam,
mortar, moving pad/grid and pad/diagonal events and assembles P0/P1 weak
rows. `_b3_e4_f03_area_loaded.py` solves small, elastically coupled
systems with the existing work-conjugate diagonal KKT scaling and
recovers physical support wrenches, energy, weak gap and a separate
continuous-field L² gap.

The next bounded feasibility experiment declares `a=.05 m` before examining
its response: the classical reference beam has area `.01 m²` and bending
inertia `8.333333333333333e-6 m⁴`, corresponding to a nominal `.1 m` square.
Four *separate* `.1 × .1 m` material patches are an illustrative connection
geometry with `.04 m²` total interface area, not a consequence of the beam
section or a real weld detail. This changes the physical model. The `.05 m`
choice must remain fixed for the experiment and may not be tuned to resolve
the adverse four-point reference results. The previous `.04 m` preflight
remains a test geometry.

The experimental runner `b3_e4_f03_area_feasibility.py` registers exact
source and environment identities before execution, supervises two bounded
mesh sizes per Q4/CST-CB topology with P1 and smooth load, and preserves
per-case raw output. Its terminal mesh is `(Ns,Ny,Nb,Nm)=(8,16,16,8)`;
each case has a 900-second limit and a 100-ms-sampled child-process RSS cap
of 8 GiB and runs single-threaded. The supervisor does not measure an
instantaneous or process-tree peak. Only algebraic balance, compatibility, and energy have
pass limits. It reports signed tip, three shell stations, root elastic/port/
load partition, and four beam-side physical-quarter resultants without
claiming response convergence. The integrated L² gap is not a pointwise
enclosure or endpoint certificate. A supervised case exit, however clean,
does not accept a physical reference or close G0B.
Four runner path tests cover spawn failure receipt, premature final
adjudication, corrupted child output, and a valid final decision. The
combined focused suite passes 65 tests after these additions.

The initial source-frozen `f03-area-feasibility-v1` registration at
`0c74d6c0` completed four supervised cases. Its final adjudication raised
`TypeError` because a local reaction variable shadowed the evidence-root
path; **no v1 acceptance decision exists**. Preserve its original raw
cases and `adjudication_failure.json`. The corrected runner requires a new
source identity and registration; v1 must not be relabeled or rerun.

The 36 new focused tests pass: rigid motions at the line ends and an
interior station; a general affine shear; a Q4 bilinear second-moment
identity; signed force, origin moment and virtual work; an analytic
nonconstant P1 multiplier moment; independently located rising and
falling CST-CB diagonal events; 6/8-point line quadrature parity; small
constraint rank; and Q4/CST-CB × P0/P1 × smooth/sine small coupled
equilibrium, compatibility, balance and energy identities. The combined
new and existing loaded/gap focused suite passed 58 tests before the
additional reversed-diagonal assertion; the 36 new tests passed again
after it. Independent mechanics review found no algebraic or work-sign
blocker **for this bounded preflight**. It did not accept a continuum
reference, physical convergence or a native formulation.

Before a new physical-reference gate can be registered, freeze a pad
width from the actual connection geometry rather than tuning it to the
Q4/CST contrast. Add an independent clipped-host integration oracle for
nonaffine checkerboard fields, wider meshes and multiplier ratios,
derivative/conditioning checks, and a source-frozen first-quarter
Q4/CST-CB response and operator-swap diagnostic. Then refine shell x/y,
beam and mortar independently and compare all signed response channels,
support partitions, port work and continuous gap against the unchanged
physical acceptance criteria. A small-mesh balance or one matching
response does not resolve the prior adverse reference. Preserve both
connection models and all failed or accepted historical evidence.
