# Directional coupling preparation

Status: prepared, UNEXECUTED local production-adapter discriminator. No product
edits, imports, numerical checks, build or install were performed for this slice.
The current V19 product and all earlier evidence are unchanged.

Owned candidate:
`tests/test_general_contact_beam_s3_directional_coupling.py`

Future single selector:
`tests/test_general_contact_beam_s3_directional_coupling.py::test_production_nonzero_null_directional_coupling`

## Exact stored construction

Use m=256, delta=1/16384, X=(m*m-1)*delta, Y=4,
target rise=2*m*delta=1/32. Physical skin offset h=1/128, shell thickness
2*h=1/64, beam radius rho=1/128. All geometric construction operands are dyadic.
The material reference target is flat, director +z, reference offset zero.
The current target edge vectors are (X,0,rise) and (0,Y,0).
Its unnormalized normal is

    C = Y*delta*(-2*m, 0, m*m-1)
    |C| = Y*delta*(m*m+1).

The beam stations t=(1/4,5/16,3/8) use offset e=(-rho/m,0,rho),
with points skin0+t*edge1+(1/4)*edge2+e. Therefore
C.e=rho*|C| exactly, with positive orientation; all three source nodes have
the same exact represented gap zero. Reference beam z=1/32 and the independently
derived nodal displacements remain dyadic. The test explicitly refuses a fixture
construction that is not exactly representable as binary64.

This local pose has a current target slope rise/X about 0.0078126. It is not an
accepted dynamic state, a force-consistent transient initialization, or a claim
of finite-rotation admission. The test records its actual Z.T*Fstruct rather than
assuming that the pose lies on the algebraic equilibrium manifold.

## Real null coordinate and work

Model constraints tie the three physical target ry coordinates uniformly and
leave them free. They do not add rotary inertia. The actual assembled mass and
declared algebraic-basis services must establish that this uniform ry direction
belongs to the reduced mass null space. Beam ry has its genuine rho*Iy inertia.

For the formulation-owned affine skin, uniform target ry gives
delta skin=h*ry*ex and delta C=0. Thus

    delta g / delta ry = -n_x*h = 2*m*h/(m*m+1) > 0.

The virgin flat plane would give zero for this coupling. This test deliberately
uses a tilted local plane and tests actual production B*Z, rather than a
synthetic null coordinate alone.

The independent reference manually constructs each translation/rotation row of
the physical skin map and the Q2 source polynomial. It differentiates

    delta g = (delta E.C + E.delta C
               - (E.C)*(C.delta C)/(C.C)) / |C|.

Every global coefficient is compared exactly against production B/|C|. Unequal
target normal velocity tests normal variation as well as eccentric rotational
work. Both source and target coordinates and their Hessian cross blocks remain
represented. This is affine small-rotation nodal work, not an SO3 skin map or a
finite-rotation angular-momentum claim.

## Prepared development checks and prospective controls

The single test is prepared to check:

- exact full-touch geometry, positive orientation, complete map and nonzero B*Z;
- actual two-dimensional declared null space and mass action preservation;
- independent Q2 consistent beam translation/rotary mass and S3 normal lumped mass;
- independent 70-digit Decimal quadratic roots and degree-four directional
  integrals, compared to production D/H and their reported component bounds;
- safeguarded null velocity recovery using actual local structural tangent,
  fixed physical velocity modulo Z, and the existing 1e-9 residual gate;
- connected recover_directional_rates caller with the actual ordinary contact
  Hessian included in its supplied total tangent; comparison to the lower-level
  velocity independently checked by the Decimal operator tests single ordinary-H
  removal, null endpoint-velocity
  secant and unchanged physical acceleration mass action;
- nontrivial partial directional support and both-body cross blocks;
- actual one-sided force rates at h=(1e-6,3e-7,1e-7), normalized errors <=1e-5.
  Fixed fixture force-rate scale is epsilon*Lref*0.01 N/s; moment-rate scale is that
  value times the declared physical skin offset, in N*m/s;
- refusal to classify a representably nonzero perturbation as exact full touch,
  V19 result profile, and captured operator mutation refusal.

The structural tangent is a production assembly used by the local rate solve;
it is not relabelled as an independent structural formulation oracle. The
opened structural candidate is discarded through the existing lifecycle helper
in a finally block, with the virgin committed mapping checked unchanged. The
reference contact differential, integral and physical mass formulas are
independent of production contact geometry/integration services. Mixed-coordinate
component errors are not advertised as a single absolute N/m error norm.

## Execution boundary and remaining gate

This is development verification preparation, not registered engineering acceptance.
No test has run. AST/EOF/source checks cannot establish mechanical pass, runtime,
resource fit or actual import routing. C6 authority remains
178.22345029981807/180 s used, 1.7765497001819313 s remaining; no renewed authority
has been granted. Do not launch this selector under the consumed historical cap.
If later authorized, use one unique directional_coupling tag with a process-tree
watchdog, 953 MiB cap, JIT disabled, Numba and all pools one, complete source/input
hashes and effective import/runtime records. DIRECTIONAL_COUPLING_RESULT may name
a unique output JSON path for the local diagnostics.

The actual dynamic coupling gate still requires a physically consistent accepted
rotating target state, an assembled first-touch continuation with nonzero B*Z,
represented-path checks, transactional restart and the existing mechanical
criteria. This preparation and the previous flat first-touch result do not close
that gate. Installed V18 remains prior artifact evidence; no installed V19 or
new dynamic-result evidence is supplied here.
