# F09 B2 weak-shear graph exploration: narrow supported pass

21 September 2026. **Unregistered local exploration, not F09
qualification.** `scripts/probe_b3_ge_e4_pl_g0_f09_graph.py`
assembles one or two straight unit-length physical-flexibility B2
members from their rounded local tangents into a small sparse graph.
It fixes the root and applies a transverse tip force `P=GA=A/2` with
`E=1`, `nu=0`, `ky=1`, `EIz=1`. An independent Timoshenko cantilever
formula supplies tip displacement `v=P L^3/3+P L/GA`, tip rotation
`rz=P L^2/2`, support shear `-P`, support moment `-PL`, and work
`P v/2`. Physical force and moment residuals use separate scales.

For one and two members at `A=1e-4` and extreme `A=2^-80`, all four
sparse LU solves returned finite responses. The largest reported tip
relative error was `2.23e-16`; the extreme cases gave `v=1 m` and
`2 m`, positive energy `2.068e-25 J` and `4.136e-25 J`, and the
expected tiny physical rotations and reactions. This refutes any
blanket assertion that a rounded local matrix necessarily fails
*every* constrained graph solve at that shear ratio.

Independent read-only review confirmed the cantilever formula,
section/DOF signs, duplicate sparse accumulation and support wrench.
The reviewer noted that `P=GA` makes the tip response shear dominated:
the much smaller bending displacement cannot be resolved in binary64
at the resulting total displacement. The root clamp removes free-free
rank questions, and only one y/rz load branch, simple collinear graph
and fixed section axis were screened. Same-matrix energy/residual
checks are not independent; the analytical tip/rotation/support
relations are the independent checks. No graph conditioning range,
mixed-frame or shell-attachment accuracy, full-rank stability,
general load response, mass, or geometric stiffness follows.

**Status:** useful narrow feasibility result; F09 remains open.
Register a more adversarial high-precision graph comparison with
independent physical-scale targets, orientation/reversal, mixed loads,
free-free physical modes, support/attachment maps and a declared
condition/failure policy before claiming graph qualification.
