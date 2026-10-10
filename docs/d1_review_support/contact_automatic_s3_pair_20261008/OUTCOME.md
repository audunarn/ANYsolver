# Automatic S3 pair development workflow

Delivered installed ordinary static press / 20mm actuator slide / open / recontact, automatically selecting the **lower** coarser S3 pressure side (.5m^2 median versus upper .25m^2). Full/explicit/prefix/resume accepted snapshot inventories are exactly4/4/3/1. No new contact equation, manager, geometry fallback, or default was needed. Product change is only narrow explicit predictor eligibility in core.py for the existing S3 projected profile, jet2_s3_dev, whole_face, nested enforcement and no rigid body. Existing Q4 eligibility is unchanged.

## Declared model and controls

Upper six physical nodes retain prior coordinates, material E100000Pa/nu.3, thickness.05m, transverse actuator tie and free other five ux. Four admitted S3-V2D triangles replace two Q4s. Lower two admitted S3-V2D triangles retain fixed xy/rotations, supports7/8/10uz and free9uz. Both explicitly use -z directors and clockwise node order. Upper reference-side top is its physical bottom; lower reference-side bottom with offset-.01 is its physical top. Upper bottom referencez=.03m, lower topz=.015m. Node-ID aligned reference/current positions and **full work maps** equal the declared +z physical representation. This proves skin-map correspondence; it does not prove full structural director-polarity equivalence. The unchanged +z/coarser-lower orientation tuple remains unsupported and is tested to refuse. No runtime normal flip or role fallback occurs.

P1 source interpolation and projected weak-gap nonpotential residual/tangent are the existing S3 law (the historical pressure_space setting spelling does not create Q1 triangle interpolation). All positive supports remain retained. k1000, gap50um and all scientific limits unchanged. Explicit control_projection_dev is selected and reported in executed output, using the already certified fixed-map affine manager before candidate evaluation. Physical path (ux,uz)m: (0,0),(0,-.015005),(.02,-.015005),(.02,0),(.02,-.015005), one increment per segment. Only upper node1 has prescribed20mm ux; the other five remain equilibrium unknowns and each is gated above10mm.

## Independent geometry and work checks

For each of eight face pairs and every accepted snapshot, construct binary physical poses independently from declared offsets. Directors/rotations and lowerxy are fixed; upper target height is explicitly constant. Lower oriented raw normal N has Nz<0 and clockwise nondegenerate source triangles. Orthogonally project upper vertices onto the lower source plane using exact Fractions, clip exact projected triangles in XY, and lift intersection vertices to that plane. At a vertex p, target q=p+lambda N with lambda=(upperz-pz)/Nz, so source-normal gap is C sqrt(N.N), C=(pz-upperz)/Nz. Affine gap extrema occur at clipped vertices. Negative admission is checked exactly by C^2*(N.N)<=Fraction(50um)^2; opening is strictly C>0 at **every** vertex. Floating radical values are approximate display only, not proven enclosures. Shoelace area is projected-XY/reference measure, not physical tilted area.

The smooth discriminator independently integrates exact P1 support and coefficient C over rational polygon triangles; multiply the exact weighted coefficient by sqrt(N.N) for comparison with production s3_overlap_derivatives at identical material points. All8 pairs match support within2.46e-17m^2 and weighted normal gap within5.44e-20m^3. Both-body directional tangent relative errors3.96e-11 and1.19e-10 for h1e-7/3e-8, below1e-5. Lower source normals actually tilt: accepted press normalXY squared5.69e-10, not horizontal-only. The unsafe control is **endpoint/path refusal**, not a new through-crossing qualification.

Existing S3 swept bound encloses quadratic normal controls about the midpoint with radius d, norm lower||Nm||-d>0, mutual-normal lower Nm_a.Nm_b-||Nm_a||d_b-||Nm_b||d_a-d_a*d_b>0 and gap variation2d_a*max||D||/normlower over all affine vertex differences. Manager processes every pair and recursively subdivides its fixed-map affine physical path. Its128eps and unenclosed midpoint arithmetic remain a development confidence limitation; this milestone does not claim directed finiteprecision/D1 coverage qualification.

## Observed evidence

Installed full/explicit/separated-prefix/fresh-resume, provenance/selector/tamper refusal, public precancel/frictionless-route refusal, historical default automatic identity, and actual CLI passed. Resumed endpoint and per-phase response parity are exact in reported fields. Resumed-endpoint all-free equilibrium normalized error5.8644e-9<=1e-6 at positive.02N scale. Wrench balance maximum1.22e-17<=1e-6 with .02N/.02Nm scales. Physical lower9uz=-16.6861um at recontact, then return~0 on opening. Independent minimum gap~-5um in press/recontact, strictly positive15mm opening, zero pressure/storage on opening. Actuator/support reactions and both physical bodies' instantaneous residual work are nonzero and balance. Work is not path-integrated storage/energy.

One safety test setup failure is preserved: invalid friction keyword plus missing baseline environment. Corrected to actual public contact_friction option and immutable baseline, then both cases passed. No solver or mechanics failure occurred. Older full/explicit/prefix/resume report labels used source to mean physical upper actuator; METADATA_ERRATUM.json binds original hashes and corrects role names without overwriting/rerunning them. FEModel repr comparisons prove declared fields unchanged, not a full hidden-state audit.

## Usage and artifacts

From the checkout with the private installed candidate on PYTHONPATH:

```powershell
$env:NUMBA_DISABLE_JIT='1'; $env:NUMBA_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'; $env:OPENBLAS_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
$env:PYTHONPATH='C:/ANYworkspaceWork/contact_automatic_s3_pair_20261008/candidate/site'
C:/Python/Python314/python.exe examples/general_contact_automatic_s3_pair.py
```

Raw root C:/ANYworkspaceWork/contact_automatic_s3_pair_20261008 contains PROSPECTIVE, source checkpoints, immutable632input candidate,627payload wheel/private install, per-attempt commands/inputs/hashes/fullstdoutstderr/JUnit/effective runtime/RSS, ledger, outputs, metadata erratum and CLOSURE.json. WheelSHA b72734a42a8782ef6e9da1bfe011d8dad1015d6d10f7bb48792ac52859c74284. Ten jobs used64.44131170000765/360 process seconds,295.55868829999235 remaining; max12.73405s/job, peak191.81MiB. JIToff/Numba1/pools1/private imports verified. Old scopes unchanged, no active job. Lead released60 final reserve after reviewed discriminator/full evidence. Prior Q4 mechanics reused by source impact plus installed historical identity check; no broad suite replay.

Status: verified against assigned bounded development criteria; independent lead review/acceptance remains separate. No generic arbitrary-pose/director/friction/native/finite-rotation contact qualification or release claim.

Supporting source review is in SUPPORTING_REVIEW_20261008.md. Its low report-label finding is resolved by future upper/lower actuator/work labels and the hash-bound erratum; no mechanics rerun for labels. Formula review found no concrete defect and its finiteprecision confidence limit is retained. This is same-family supporting scrutiny, not independent engineering acceptance. RECOVERED_REFERENCE_PROVENANCE.json records hashes and recovered unchanged source/baseline inputs for the historical identity safety check; those two files were referenced by the recorded command/environment but absent from its original eight-file snapshot inventory. Recovery is explicit, not presented as execution-time capture.
