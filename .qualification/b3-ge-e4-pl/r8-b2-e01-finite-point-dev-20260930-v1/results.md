# Matched finite-vertex B2 reference — fixed development comparison

**Decision:** retain the declared B2 point map for this model. Independent
connection rows and native beam actions agree. The sampled same-state assembled-
force differences are allocated to the shell contributions, whose formulations
include numerical drilling behavior under the stated supports. Do not uniquely
blame drilling or generalize this to every operator state. Do not tune the
connection to compensate. This does not
identify the physically correct shell result or accept M3/E01 accuracy.

Exact fixture: two unit-square Q4 cells, two1m positive-x scalar physical B2
members, beam-axis eccentricity±0.1m, zero section offset, station.5 finite-vertex
point ports. Shell nodes1/4 and beam101 fixed in all6 coordinates; four other
shell normal rotations fixed. E210GPa,nu.3,h.07m,A.01m², stated Iy/Iz/J and
shear factors. Each force channel1000N and moment channel100Nm is separate.
`inputs.json` records geometry, frames, ports, constraints, supports and measures.
This is distinct from GE nodal pose, BL5, classical axial and historical F5 laws.

Installed native product wheel6a44aa11... passed12/12 fixed public solves. Its
two C maps agree with the independently derived covariance/force-method rows
to4.4408921e-16. OpenSees3.8.0/Python3.12.14 controls pass all6 analytical beam
compliances (worst5.93e-16 versus1e-10). All12 fresh-process panels pass physical
equilibrium, reconstructed ground/interface wrench and work predicates, worst
normalized check2.1553e-13. Raw states, element covectors, physical multipliers,
scaled checks, logs, binaries/runtime/source hashes and commands are retained.
External covectors come from the global force response; physical multipliers
are recovered through free beam equilibrium. Raw nodeReaction is not substituted.

| Channel | Tip-pose difference | Energy difference | Interface-action difference |
|---|---:|---:|---:|
| Fx |0.1837%|0.0188%|0.2416%|
| Fy |2.0534%|2.8973%|9.6361%|
| Fz |0.0170%|0.0390%|0.0645%|
| Mx |1.0103%|0.0649%|1.0068%|
| My |0.0050%|0.0050%|0.0821%|
| Mz |0.3365%|0.2047%|10.2708%|

Both eccentricity signs have these magnitudes. Pose norms use translation/2m
and rotation; wrench norms use force and moment/2m. The comparison includes
complete vectors and energy, not unstable division by an individually zero
response. At the same external displacement, native beam covectors match the
external element covectors within5.69e-16 of load scales. The assembled operator
difference is consequently in the shell contribution at these sampled states. Large
individual shell covector differences do not by themselves establish erroneous
torque transfer, drilling dependence, or physical formulation failure.

Failures preserved: V1 omitted one beam restraint flag and stopped before any
external solve. V2 repaired only that input; all6 controls and Fx passed, then
the same static Fy operator failed factorization after repeated domain wipes.
Identical Fy in a fresh process passed. V3 therefore isolates each panel in a
fresh process; all12 passed. Runtime-history/numbering/backend sensitivity is
demonstrated, but its internal cause is unallocated. It is not a native mechanics
failure. No penalty, invented inertia, tolerance relaxation or estimated solution.

V1 native12/12 are reused: all fixture/port/section functions stayed AST-identical.
V2 changes only external beam_control (sixth fixed flag); V3 changes only main
(one named case per process). V2 analytical controls are reused at their original
source/runtime identity. These are bounded development repeats after identified
input/execution defects, not renewed formal F03 authority.

The V3 isolated external campaign completed in3.6597621s, sampled peak39964672B,
under600s/8GiB. Numerical thread environment is1; the native process verifies
effective BLAS1/JIT off. No external BLAS-thread or performance claim is made.
The same-state allocation is a separate small local calculation, not a timed
qualification. The installed127-case suite/evidence is referenced, not rerun.

Next consequential reference work must preserve physical footprint extent and
distinguish shell discretization/stabilization or supported continuum response.
Blind host-cell refinement would change the connection. No automatic refinement
campaign follows. Converged1% matched accuracy, broader torque/shear/drilling,
curved/spectral/nonlinear references, mandatory CalculiX and M3/G0–G6 remain open.

Primary interpretation support: [ASDShellQ4 global force response](https://github.com/OpenSees/OpenSeesDocumentation/blob/master/source/user/manual/model/elements/ASDShellQ4.rst)
and [elastic Timoshenko element contract](https://opensees.berkeley.edu/wiki/index.php/Elastic_Timoshenko_Beam_Column_Element).
These references specify interfaces; executed controls provide numerical evidence.
