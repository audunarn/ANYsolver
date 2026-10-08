# E02 reference recovery feasibility — bounded decision

Question: can explicit CalculiX rigid-body reference/rotation nodes recover
complete physical support forces and moments without the earlier shell-clamp
RF omission? One C3D20R solid has two rigid opposite faces. Separate reference
nodes belong to neither face; dummy rotation nodes belong to no element.
The eccentric force is (0,100,-50) N at (1,0,0.2) m, with direct couple
(10,-4,5) Nm. Root reference origin is (0,0,0).

The [CalculiX manual's rigid-body convention](https://www.feacluster.com/CalculiX/ccx_2.18/doc/ccx/node320.html)
defines dummy translations as rotation coordinates and their forces as moments;
it warns against reference nodes belonging to the body when requesting RF.
The documented2.18 convention is verified here on the pinned2.23 executable,
SHA25627a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f.

V2 completes one linear step without warnings/errors. Printed root force is
(-1.724487e-10,-100,50) N; root moment (10,-46,-105) Nm agrees with the expected
-(r cross F+M). Printed rigid-face displacement mapping has maximum absolute
gap2e-14m. Final-load work pairing F dot u_REF+M dot theta_ROT is
3.32122418e-5J. Positivity is not an independent energy check; linear-ramp work
would be half that final pairing. V1's default-minimum-increment warning remains
retained; V2 explicitly supplies the same1e-6 minimum selected automatically by
V1. Physical outputs are unchanged.

Independent Read review found no sign/unit/membership blocker for using this
route in a future matched-reference experiment. It identified a material
precision limit: DAT prints seven significant digits. The zero printed moment
error does not prove underlying1e-8 relative balance; near105Nm, half a printed
unit is about5e-5Nm (about4.8e-7 relative). Existing scientific criteria remain
unchanged. Higher-resolution data or a justified uncertainty-aware comparison
is required wherever the mandatory tighter criterion applies. Do not turn the
script's rounded-data guard into scientific acceptance.

Observed V2 process time0.039s; memory/thread samples were missed because the
process completed before sampling. The retained zeros mean UNOBSERVED, not zero
memory or threads. Solver stdout reports one CPU for matrix/stress work and
Spooles; this is not lifetime thread/resource qualification. Configured stop
budgets60s/1GiB are recorded; no peak-memory qualification is claimed.

Decision: use the explicit outside-body controls in the planned physical rigid-
footprint reference and retain the precision requirement. This single-element
solid control is not a plate/beam/footprint accuracy comparison, native
equivalence, drilling-independence proof or E02/F03 pass. It does not consume
formal F03 authority. The matched geometry/connection/observables still need
definition and execution; no extra BL5 refinement is launched.
