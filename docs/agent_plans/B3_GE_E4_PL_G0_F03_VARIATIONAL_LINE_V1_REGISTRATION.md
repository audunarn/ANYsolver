# F03 independent variational line-law pilot registration

21 September 2026. Status: **registered exploratory comparison only**.
F03/G0B remain open. Freeze the source, runner and this registration at a
clean integration commit before the exclusive execution. The purpose is
to discriminate a continuum-work-conjugate weak line law from finite
station ties on an independently assembled classical membrane/beam model.
It does not select a native mortar test space or supply the required
converged physical target by itself.

The source
`scripts/probe_b3_ge_e4_pl_g0_f03_variational_line_v1.py` uses the
separately assembled classical plane-stress Q4/CST panel of thickness
`.07 m`, the exact-static *trial-space* stiffness of a conventional
Timoshenko beam with `EA=210 GPa·.01 m²`, `EI=210 GPa·8.333333e−6 m⁴`,
and `k=G·.008 m²`, and the centered four-host pose fit at
`(s±.2,±.23) m`. Both a distributed beam load and the line-multiplier
traction act by virtual work on the same interior beam trial functions.
There is no q-only particular pasted onto a station-tie solution. The
unrepresented load/traction particular must be resolved by independent
beam-subcell refinement; this is a conforming variational approximation,
not an exact continuous-field solution at finite subcell count.

`weak-p0` and `weak-p1` use exact multipliers with local constant and
continuous linear test functions over eight reference line cells. The
integrals split at the union of beam subcells, shell host/triangle
boundaries and multiplier-cell boundaries. Four-point Gauss exactly
integrates the polynomial trial/test line action on each split interval;
an independent six-point assembly checks that claim. `station` ties
the nine *mortar-cell endpoints* including the root; at four beam
subcells per mortar cell these are only nine of 33 beam nodes.
`station-no-root` ties only endpoints one through eight. They are distinct finite models: the
root point row materially affects the response, so no law difference
will be attributed solely to weak versus point integration. Shell x
ends are fixed, and the beam root physical pose is fixed in every case.

Inventory: for Q4 and S3-V2D and both smooth and signed sine load,
`(Ns,Ny,Nm)=(8,4,8)`. At one beam subcell per mortar cell run both weak
laws; at four subcells run both weak laws and both station conventions.
Add `(Ns,Ny,Nm,subcells)=(16,8,8,4)` with both shell types and both
loads for the two weak laws. This is **32 distinct cases**: 24 at the
first shell mesh and eight simultaneous shell length/width controls.
The fixed eight-cell multiplier resolution deliberately cannot prove
line-law convergence. A later registered comparison must refine its
space and independently resolve beam/shell and transverse directions.

The source reports translated and yaw gaps separately. Its sampled
pointwise maximum is only a lower bound; the scaled summary converts
yaw by `.46 m` and divides by the frozen
`U=1e6 N/(210e9 Pa·.07 m)`. Integrated weak residuals have displacement
times length units (and yaw times length); station residuals have point
displacement/rotation units. Compare only their **own** dimensionless
normalized residual, not raw row values across laws. The KKT multiplier
is dual to the corresponding constraint row. Record nodal/line work,
shell and beam energy, support force and moment, full interface work,
matrix size/nnz, row rank, physical tip and station motions, and sampled
gaps. Row-normalized Gram rank is not a signed native inf-sup test.

Numerical screen for each case: finite result, full independent row rank
at relative `1e−12`; free equilibrium, both global force components,
moment and doubled-energy work balance each `≤1e−8` relative to their
declared scale; interface-work cancellation `≤1e−8 J`; normalized weak
moment/station residual `≤1e−9`; and signed-load force/moment integral
errors `≤1e−6 N/Nm`. Preflight compares four- and six-point coupling
integrals for both shell types and weak spaces to `1e−11` relative and
checks the independent beam cantilever energy/flexibility and rigid
four-host patch. These are assembly checks, **not** physical acceptance.

Before execution, disclosed unregistered smoke at Q4 `8/4/8`, four beam
subcells and smooth load gave tip approximately `43.51 µm` P0,
`38.37 µm` P1, `25.26 µm` station including root, and `47.75 µm`
station excluding root. P0's sampled transverse gap was about `26 µm`
and yaw about `58 µrad`. These large law and boundary-policy differences
motivate the pilot; they are not qualification data. In adjudication,
report all cases and pairwise changes without selecting a favorable law.
At any fixed matched case, more than `5%` tip spread between P0/P1 or
sampled physical gap above `0.05 U` is an explicit warning that the
pilot does not yet supply a line-independent physical target. Passing
these exploratory screens would still require multi-level convergence,
an independent external or resolved target, native signed stability and
six-channel eccentric mechanics for F03.

The supervisor `scripts/run_b3_ge_e4_pl_g0_f03_variational_line_v1.py`
uses an exclusive evidence root, committed-clean source/provenance and
preflight before root creation, serial child solves, one BLAS/Numba
thread, sampled child RSS limit 8 GiB, 900 s per case, 3,600 s total,
and 0.5 s sampling. It writes the manifest, preflight, per-case stdout,
stderr and flushed records. Sampled RSS is not a hard process-tree peak.
Keep every failure and incomplete run; never overwrite the root. An
independent pre-execution mechanics/code review and post-run evidence
audit are required before interpretation. Do not describe this classical
planar pilot as native B3/E4-PL qualification or promote G1 from it.
