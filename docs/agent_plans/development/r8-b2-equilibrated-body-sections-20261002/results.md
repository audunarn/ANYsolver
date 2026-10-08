# Experimental B2 body-load section recovery — 2 October 2026

The installed public B2 workflow now preserves typed body-load context and
returns separate equilibrated member resultants and strains, including sided
interior attachment jumps. Raw nodal loads retain the existing result types,
nodal constitutive recovery and equations. This is development evidence;
M4/G4A, aggregate qualification and the complete programme remain open.

Source base: `7c91e4a546c59b09937418a0b1ce5fd262f56497`; the exact changed
sources, test and example are in `raw-v1.zip` under `candidate/`. The delivery
commit also contains this interpretation and the independent review.

## Mechanical contract and implementation

Local ordering is `[N,Vy,Vz,T,My,Mz]`, with strains
`[u',v'-rz,w'+ry,rx',ry',rz']`. For external distributed force/couple `(p,c)`
per reference length and the local axial unit vector `ex`, equilibrium gives
`n'=-p` and `m'=-ex×n-c`. An interior external point wrench `(P,Q)` produces
right-minus-left jumps `(-P,-Q)`. An offset point contributes the axis moment
`Q_axis=Q_port+d×P`. End tractions are `(-n(0),-m(0),n(L),m(L))`.

The existing KKT convention is `K u + C.T lambda = applied`. The beam action
of an attachment is therefore the negative transpose variation map, not raw
multiplier channels. Compilation retains the existing beam pose differential,
maps `-D_beam.T lambda` to the member frame and shifts its moment to the axis.
Only strictly interior attachments become section jumps; endpoint attachments
remain nodal actions.

The existing polynomial station trace supplies an exact local equivalent-load
integral, compiled once. Reconstruction uses
`t_e=K_e u_e-f_body-sum(J_axis(a).T W_axis)` and the equilibrium equations.
Exact stored-input end-traction closure is checked before float conversion.
Compliance maps the resultants to section strains. Independent segmented
quadrature verifies end-to-end kinematic compatibility, including coupled
sections and multiple point actions. No global dense operator is introduced.

These fields are statically admissible reconstruction, separately labelled
`B2_REFERENCE_EQUILIBRATED_MEMBER_FIELDS_V1_DEV`. They do **not** reconstruct
a loaded interior pose satisfying the point constraints. Such a pose generally
has a load-dependent bubble; inserting it into an attachment trace changes its
constraint RHS and multiplier compliance. That requires a reviewed mechanical
extension, retained as an M4/G4A obligation. Existing nodal strains, resultants
and `internal_strain_energy` keep their original meanings; the energy is not
the reconstructed loaded-field energy.

Typed `B2ReferenceBodyLoad` values bind acceleration, node inventories and
equivalent load to a compiled model identity. The identity includes the actual
point-wrench pullbacks. Batch fingerprints cover this metadata as well as the
applied vector. Typed successful result variants add owned section fields for
selected members/stations; failure status and complete-case cancellation remain
unchanged. Byte-backed local arrays and immutable public tuples isolate callers.
No existing formulation, tolerance, public default or version is changed.

## Executed checks and retained failures

Focused source checks used the existing portable development runner with
JIT disabled, a 600-second limit and 1 GiB process-tree memory ceiling.
Source v1 passed 32/32. Expanded fixtures exposed two retained failures:

- Moving footprint attachment points onto a clamped endpoint produced dependent
  supported rows. Preflight rejected that fixture; it was not an admitted test.
- Moving points to the opposite endpoint exposed the existing
  `panel mixed-load resolution insufficient` status for centered inertia and
  acceleration `(0.1,-0.2,-0.3)`. Raw and typed loads fail alike. The regression
  preserves that failure and verifies endpoint actions are not counted twice.

The admitted original footprint with physical off-center inertia passes typed
recovery and batching. The two repaired fixture/status checks passed 2/2; the
metadata-mutation check passed 1/1. The endpoint resolution issue remains named
`B2_ENDPOINT_POINT_MIXED_LOAD_RESOLUTION`; it is not a mechanics pass or a
permanent exclusion. A future diagnosis must distinguish genuine conditioning
from load-preparation or overly conservative resolution effects before repair.

The first installed candidate passed 262/262 before review's provenance fixes.
It is retained as its own source-bound artifact. The **final installed candidate
passed 263/263** across twelve affected modules: physical operator, Q4/S3 point
laws, affine batch, Q4/mixed panel, footprints, body loads, new section recovery,
and reference modal regressions. Controls include fixed-end nonzero stresses,
equilibrium derivatives, offset signs, sided jumps, strain integration, exact
raw/typed state parity, mutation isolation, model mismatch, failed solves and
selected complete-case cancellation.

All three installed public examples (Q4, mixed and S3) completed 1/10/100 typed
cases with one eligible factorization, selected section fields and balanced
3449.9808 N total weight. These examples have different attachment hosts; they
are not an accuracy comparison of equivalent discretizations.

## Artifact and run identity

- Final wheel SHA256:
  `4c14d0942410f97b6e2ab397eb0d4e567cbff4169c05b391c5685c4df40d3b7c`.
- All 391 solver Python modules were bound between source, wheel and isolated
  installed site; actual solver imports came from that site.
- Windows, Python 3.14.2; NumPy 2.4.6, SciPy 1.17.1, Numba 0.65.1,
  ANYmaterial 0.2.0, pytest 9.0.3, threadpoolctl 3.6.0, psutil 7.2.2.
- Actual numerical thread count: one; JIT disabled. Test route elapsed
  28.2790469 s; sampled process-tree peak RSS 194392064 bytes. These are run
  records, not a performance improvement or scale qualification.
- Immutable raw archive: 121 members, 4474604 bytes; SHA256
  `44757fcddf37633f10fa284d14002fa6772f0601cd829b4d7d50d01fd586dd3d`.
  [Inventory](raw-v1.json) binds each payload. It includes both wheels, source
  failures, commands, helpers, fixture manifests, identities, logs and examples.
  Known historical credential values were scanned in memory without printing
  or copying the contaminated historical archive; the new payload scan was clear.

Independent Read review's two provenance findings were repaired and rechecked;
see [review](review.md). This was a separate OpenAI reviewer, not different-model-
family acceptance. ANYfem code and persistence were unchanged and not retested.
Consumer typed-load persistence, loaded interior pose, GE gravity, distributed
load/attachment physical validation, Linux/platform acceptance and the full
G0–G6 obligations remain open. Formal F03 authority was not consumed. No push,
merge, publication, protected-script execution or repeat scientific campaign.
