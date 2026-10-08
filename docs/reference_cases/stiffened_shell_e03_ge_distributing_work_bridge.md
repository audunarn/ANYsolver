# E03 GE distributing reference-linear work bridge

Status: **IMPLEMENTED_UNVERIFIED — source candidate, all controls unrun**.
This is OpenAI fallback implementation because Mistral and the local worker are
unavailable. It supplies a local map for the existing distinct finite GE
director/planar-polar footprint law. It does not supply the GE point reference,
change any product source, remove the owner's flat-footprint/curved-reference
guard, admit a public curved workflow, or establish scientific acceptance.

The implementation is [r8_e03_ge_distributing_work_bridge.py](../../scripts/r8_e03_ge_distributing_work_bridge.py).
The prepared controls are [test_stiffened_shell_e03_ge_distributing_work_bridge.py](../../tests/test_stiffened_shell_e03_ge_distributing_work_bridge.py).
They include separate actual-native local derivative controls. No imports, tests,
native evaluation, physical solve, CCX job or build were executed for this slice.

## Reference assumptions and independent map

Declare positive rectangle lengths W,H and thickness h, an origin O, and a proper
orthonormal material frame R=[a,b,n]. The rectangle is a uniform Q4 grid with
1–8 subdivisions per direction. Each reference mid-plane node x_i has a material
corresponding lower/upper face pair x_i^- = x_i-h*n/2 and x_i^+ = x_i+h*n/2.
Inputs and maps are independently owned, immutable binary64 arrays. The factory
refuses direct record construction, nonfinite data, reflected frames, collapsed
geometry and ill-resolved coordinates. There is no global assembled dense object;
the local pose map has six rows and at most 486 columns.

For face translations u_i^-,u_i^+, define

```
u_i^0 = (u_i^- + u_i^+)/2
delta d_i = (I-n*n^T)(u_i^+ - u_i^-)/h
delta omega_i = n cross delta d_i
t = sum_i w_i u_i^0
omega = sum_i w_i delta omega_i
        + n/2 sum_i (g_xi b - g_yi a)^T u_i^0
```

The w_i and g_xi,g_yi are exact rectangular Q4 area-mean and area-mean derivative
weights represented in binary64. These equations independently define P with
[t;omega]=P*u_faces, using lower samples first, then upper samples. The director
tilt follows the through-thickness material fiber variation. A geometric normal
slope in u^0 does not replace that independent director: transverse shear remains
independent. Nodal rotation about n contributes nothing to the director, while
the aggregate normal spin comes from the planar polar yaw. All six aggregate pose
channels remain; no drill-only stiffness, normal-spin penalty or rigid patch is
introduced. Normal thickness extension and nonrigid local modes remain outside
the aggregate pose without being constrained by this map.

Differentiating the existing finite construction at its reference gives these
same channels: its mean director sets n, and its projected material gradients
give normal yaw `(b·delta a - a·delta b)/2`. This bridge is only that reference
derivative. It does not replace the native finite law or its director, projected
rank and orientation admission checks away from reference.

The map uses nominal h only after checking the *measured binary64* pair separation:
`max(abs((x_plus-x_minus)/h-n)) <= 256*eps`. Recovered coordinates and pair
midpoint errors are expressed in the declared local frame and divided by W,H,h
in the a,b,n directions respectively, then compared with the same `256*eps`
bound. Individual edge lengths prevent a long edge from concealing narrow-edge
distortion amplified by its yaw gradient. Thickness scales the normal component
because it resolves the independent material face-pair trace. Frame orthogonality
and determinant errors must also be within `256*eps`. These dimension-normalized
input representation checks are not a scientific comparison tolerance or a
universal proved bound on recovered wrench or other output errors. A large origin with a thin,
ill-resolved face separation refuses with a request to rebase local geometry.
Transpose work is an algebraic identity of the stored map, subject to arithmetic
roundoff when evaluated. Physical rigid-mode and wrench identities are algebraic
in ideal geometry; the prepared controls assessing their implementation remain
unrun. The product's proper-rotation admission is unchanged.

## Offset, row frames and dual actions

For beam-centroid offset r in world coordinates, define

```
E(r) = [[I, -[r]cross], [0, I]]
c_world = [t_beam; omega_beam] - E(r)*P*u_faces
C_world = [-E(r)*P, I]
[f_faces; wrench_beam] = C_world^T * lambda_world
```

Thus the shell force/moment is `-E(r)^T*lambda_world` at O. Together with the
beam wrench at O+r, total force and total moment about any common origin cancel.
For any admissible sampled increment, nodal work equals
`lambda_world^T*C_world*delta u`. `forces` recovers the transpose of the standalone
pose map; `connection_actions` recovers the signed offset connection actions;
`resultant` integrates physical sample forces about a caller-declared origin.
No raw native multiplier is labelled a world wrench.

The deferred native oracle compiles the existing flat-XY footprint, then evaluates
an actual common rigid configuration R,O with native spatial left-rotation
coordinates. The sampled tangent is compared with
`J_native = T*C_world`, `T=diag(R^T,R^T)` at that configuration. Its dual is
`lambda_world=T^T*lambda_native`. The oracle returns the evaluated shell frame,
row transform and constraints, and prepared controls also differentiate the
actual native configurations. This prevents assuming that raw native rows are
world rows at an arbitrary frame. At least two hosts and six nodes are required
by that existing prototype; the independent map itself permits a single facet.

## Remaining physical boundary and prospective checks

For a curved solid external reference, the still-unestablished equation is

```
delta d_i = (I-n_i*n_i^T)
            (u_solid(X_i^+) - u_solid(X_i^-))/h_i
```

at *material-corresponding* face pairs and with the same mid-plane trace,
reference frame, footprint quadrature and independent native director channels.
This rectangle construction alone cannot identify those traces on a curved solid,
justify averaging across facet creases, establish shell/solid constitutive
convergence, or create missing independent GE point rotation/drill equivalence.
No CCX distributing deck or full E03 comparison is supplied. The GE point E03
reference obstruction and mandatory programme scope remain open. Adoption of a
curved physical law, public admission and qualification remain root decisions.

The statically enumerated test count is 38, including six actual-native tangent
or directional-derivative cases and one native-domain refusal. None were run.
Prepared controls cover six rigid modes in three frames; transpose wrench/work
and both eccentric signs; independent director versus geometric normal;
normal-spin treatment and retained local deformation; finite native tangent and
directional derivative at actual common rigid poses; nonfinite/degenerate
refusal; large-origin and off-origin narrow-direction representation refusal,
resolved extreme-aspect geometry; sealed construction and mutation
isolation. Under fresh explicit execution authority, a prospective focused
command is `python -m pytest tests/test_stiffened_shell_e03_ge_distributing_work_bridge.py -q`.
Neither that command nor any other check was run here. Passing these controls
would establish only assigned local source criteria, not curved owner admission,
GE point reference equivalence, E03 acceptance, G6B or release.
