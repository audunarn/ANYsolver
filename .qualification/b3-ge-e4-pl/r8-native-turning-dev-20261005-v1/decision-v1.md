# Native coupled turning discriminator

Decision: does the existing native physical tangent-plane route pass a genuine
accepted load turn and a finite descending segment on one mechanically defined
coupled arch, while preserving material/state ownership and turning-point restart?

Fixed fixture: smooth parabolic native arch, a=1m,h=.03m, two Q2 B3 members and
five tangent-aligned nodes at x=-1,-.5,0,.5,1; y=-.05. Rectangle .01 by .004m,
E210GPa,nu.3,elastic generalized response. Flat two-Q4 shell width .1m and
thickness20micrometres, same elastic constants. Three objective point bonds
at the two ends and elevated apex. Full six-coordinate shell endpoint supports;
no redundant beam supports, planar restrictions or partial rotation constraints.

Clamped shallow comparator f=(1-x*x)^2 gives B=32h/(15a), C=256/(105a),
kb_arch=128EIyy/(5a^3), rho=shellthickness*width/beamarea=.05.
P=kb_total*w+EA/(2a)*(-B*w+C*w*w/2)*(-B+C*w)+EA*rho*C*C*w^3/(4a).
It predicts stationary points w=.01157583m,P=91.0645N and w=.03842417m,
P=-35.7685N. These are explanatory strip/one-mode estimates, NOT numerical
acceptance bounds for the coarse mixed 3D beam/shell model. Edge-coupled shell
deformation and lateral bifurcations may differ; a load maximum alone does not
establish the first physical instability or stability of the descending branch.

One screen: at most48 accepted increments, normalized positive reference-volume
weights, metriclength1m,radius.003, downward apex translation orientation. Unit
downward dead-force direction; unchanged default equilibrium/compatibility checks.
Stop after a turn followed by three decreasing-load/increasing-displacement
increments and at least5percent load reduction from the observed maximum.
Fresh restore from the checkpoint just before the first load decline must
reproduce that next accepted checkpoint exactly. No parameter sweep.

Outcomes: accepted turn/restart -> retain scoped continuation evidence and assess
refinement/physical branch stability separately. Numerical failure -> preserve
prefix and diagnose actual residual/conditioning/chart issue; do not call it a
limit point. No turn within budget -> preserve complete path, distinguish model
stiffness/mesh/branch assumptions before any extension. Do not tune laws/supports
or relax tolerances to obtain a turn.

Limits600s/2GiB/affinity1/pools1/JIToff; one numerical job. Existing installed
solverwheel e66a4da0 reused after identity check. FormalF03/canary untouched.
Supporting OpenAI mechanical review; independent-family/scientific acceptance
remains open. No speedup, full G4D, external comparison or release claim.

## Interpreted first screen and one shell-only discriminator
48 accepted steps completed without turn: w=.011534315m,P=915.026287N.
Saved endpoint replay is byte-exact; apex point returns Fz902.139687N to beam,
roll=.19661351rad. Eccentric pose transport quantitatively explains lateral
beam motion: delta_y_beam=delta_y_shell-h*sin(roll); this is not by itself
lateral bifurcation evidence. Rotation dominates the path metric.
Supported lower-edge pitches at x=-1,0,1 are all zero in the coarse mesh.
Nonzero apex deflection therefore has no intermediate pitch samples to cancel
longitudinal transverse shear. The actual E4 MITC4 sampling equation supports
that representability obstruction. Four longitudinal Q4 cells introduce free
opposite pitch at x=+/- .5; beams, physical law, supports, ties, material and
normalized reference-volume metric construction stay unchanged. One bounded
48-step discriminator, same radius/load orientation. Compare overlapping physical
w and connection force/roll; equal step count is not a physical comparison.
A lower skin force with resolved pitch supports coarse trace stiffness as cause;
unchanged force/roll identifies a physical coupling or other discretization
explanation. No turn within budget triggers interpretation, not automatic further
refinement. No asymptotic convergence, stable branch or qualification claim.
