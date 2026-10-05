# Local recovery implementation draft

This is a bounded manufactured-state helper, not a reference execution
protocol or physical acceptance. It neither solves equilibrium nor selects
a mesh, degree, multiplier space, condition certificate, or tolerance.
Existing consumed evidence and HOLD decisions remain unchanged.

`recover(grid,q,eta,budget)` takes an owned `CompiledGrid`, a copied finite
float64 free-coordinate vector (lifted from its exact bits) or bounded exact
Fraction vector, and an explicit **physical** three-component root dual eta.
It streams existing `ExactTrace` coefficients into owned exact local-tau
pose polynomials. Supported panel coordinates remain zero. Arbitrary
manufactured states need not satisfy the three root constraints; root pose
and transverse slope are observations. No slope constraint or eta inference
is introduced.

For each exact positive station interval, including intervals whose float
endpoints coincide, the helper retains the physical resultants

    N=EA*u', Q=GAs*(v'-theta), M=EI*theta'

and the complete functional

    density=(N', Q'+F0/L0, M'+Q), cosine=(0,F0/(4L0),0),
    root_atom=(N0,Q0,M0)-eta, tip_atom=-(NL,QL,ML).

The held represented frequency multiplies the cosine. Polynomial channels
have six local-tau coefficients (degree at most five for admitted Qp).
Exact pose and first-derivative continuity are mandatory at every internal
station: there are no internal atoms. Physical yaw density and atoms remain
moments, with no ell conversion here; the separate full-H1 norm divides
the third channel by held ell once per operand. Held J and gamma=Jgeom/J
are preserved. The total beam root reaction is **-eta**, not the root atom.

Station observations expose their side explicitly; second derivatives may
jump. Positive fixed bands report (Fx,Fy,M_origin), with the moment density
`s*mu_y+mu_theta`. A band containing s=0 or s=1 includes that external atom
once. Adjacent bands do not introduce or duplicate internal atoms.

`functional_work`, `beam_work`, and `load_work` retain physical virtual work.
The exact symbolic identity is

    <mu,w> + ab(b,w) - lb(w) + eta.w(0) = 0.

Tests include unrestricted endpoint values and derivatives. `Action`
stores its rational contribution and exact local polynomial cosine moments.
Identical moment terms cancel algebraically. Its optional Decimal display
uses fixed precision70, half-even rounding, and120 sine/cosine Taylor pairs
on local tau with the held frequency. It preserves tiny positive intervals
and signed values. This display is not an exact transcendental result, an
outward error enclosure, or a numerical qualification criterion.

For p>=2, six FE-admissible lifts are
`phi_left=(1.5-x)/2`, `phi_right=(x+.5)/2`, times each of
`(1,0),(0,1),(-y,x)`. Exact local shell bilinear forms and analytical pad
averages recover `as(q,lift)-<mu,A lift>`. These are declared **residual lift
actions** for arbitrary manufactured states, and support reactions only
after equilibrium and admitted-lift checks. Origin rotation preserves the
represented gamma rather than assuming exact unit torque gain. For p1,
quadratic rotation lifts are not FE-admissible: all six lift results are
explicitly unavailable, without claiming complete support recovery.

The synthetic work crosscheck independently uses the existing exact spatial
work oracle. Its constant-density limitation remains explicit; the cosine
component is not falsely included in that oracle comparison.

Required `RecoveryBudget` fields bound free DOFs, intervals, retained exact
integer bits, symbolic operation estimate, workspace estimate and the
existing per-trace budget. Fixed hard caps retain at most2048 intervals and
4096 bits per exact numerator/denominator; action aggregates have a separate
32,000,000-bit cap. Preflight includes all trace, local shell, retained pose,
resultant, density, and lift-action blocks. Estimates describe bounded
symbolic work/storage, not CPU-time, process RSS or factorization guarantees.
Coefficient contraction and retained-block checks reject excesses. No
fallback, clipping, hidden solve, or tolerance relaxation is implemented.

Independent implementation review remains required before any numerical
reference protocol incorporates this helper.
