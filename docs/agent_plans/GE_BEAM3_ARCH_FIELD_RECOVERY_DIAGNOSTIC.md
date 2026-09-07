# Preserved arch nodal geometry and station-recovery diagnostic

Base: `df5a0bc5ed5b392c95e3f3fa1787663a00acc0a8`, tree
`1a647aa76d9facd78d880744e5301359d59b14fd`. Twelve-macro load errors are below
1%, but load agreement is not field, state or complete engineering qualification.
This successor does not alter any native mechanics, section, controller,
quadrature, tolerance, public selector or beam/shell default.

## Frozen inputs and new scope

Read only the existing six- and twelve-macro four-target checkpoints:

- Six: 141,754 bytes, SHA-256
  `20a1a48cf6e2dfdc669c4f2d823deb89a9da8c6560ab716eb32e95b1b917a940`.
- Twelve: 278,640 bytes, SHA-256
  `ca95e88b6d354c3aeeb4bcebc1f49791cb3b1cef0781644f3be0e696e3a33683`.

Preserve their original directories, requests, failures and result records.
No native equilibrium solve is rerun. Reevaluate physical recovery from saved
cell rotations, retained resultants and exactly virgin histories, requiring
each reconstructed recovery packet to reproduce its saved SHA-256. Reject
nonzero or mismatching history; never replace a plastic tangent with elasticity.

The separate continuum BVP remains the locally mapped planar specialization
in `GE_BEAM3_CURVED_P5_ARCH_REFERENCE_DEVELOPMENT.md` (Bali et al., DOI
10.1002/nme.6994). This is same-author independent-algorithm development, not
independent scientific review or a newly hash-bound PDF authority. The source
site returned a browser check during this successor; no new source inspection
is claimed. Existing exact BVP equations and controls are retained.

Add an explicit saved-sample parameter to the research BVP only. Default 129
sites remain unchanged. Custom sites must be finite, strictly increasing,
contain -1 and 0, and number at most 4,097. Evaluate the already resolved
collocation polynomial directly, never interpolate the old 129 saved values.
The fixed sample union contains those original sites plus every six/twelve
node and native recovery station reflected to the left half. No adaptation
based on a comparison error is allowed.

Run BVP7 and BVP9 at each existing crown target .01/.025/.04/.055, continuing
within each profile. This is eight reference solves and zero native global
solves. Save all new reference fields and recovered native packets externally.
Report the profile disagreement instead of assuming the reference exact.

## Components and metrics

The physical material second director is +z. For planar continuum force
(Fx,Fy), tangent angle theta and positive-z moment M:

    N = Fx*cos(theta) + Fy*sin(theta)
    V = -Fx*sin(theta) + Fy*cos(theta)
    strain = [N/EA, 0, -V/GA, 0, M/EI, 0]

The negative third-component shear follows e3 = e1 cross e2. Reflecting the
right half reverses x, theta and Fy, but preserves Fx and M. Verify these
conventions by reconstructing spatial force/moment and virtual work. Do not
compare untransported local components as spatial quantities.

Compare nodal positions and nodal material frames. At all 48/96 recovery
stations per target compare strains, physical spatial forces/moments and
current recovered frames. Report the strain-difference energy norm using the
nominal diagonal section [1e6,4e5,4e5,80,100,100], and the integrated native
elastic energy versus the independent BVP quadrature. Also report reference
energy integrated on the native rule to distinguish comparison quadrature
error. Nominal section arithmetic is not an exact dyadic section certificate.
No claim of continuous pointwise geometry or same-equilibrium-branch identity
is implied by nodal geometry and station samples.

Summary validation recomputes every metric from the saved fields and checks
native recovery hashes against preserved checkpoints. This is publication
validation, not a separately authored checker. No metric may confer production
qualification: status remains `DEVELOPMENT_COMPARISON_NOT_QUALIFICATION` and
independent review remains pending, regardless of error size.

## Execution and boundaries

Freeze source before the new `ge_beam3_arch_field_probe` invocation. Use fresh
external output `C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-arch-fields-20260907-v1`.
Active Normal-token scheduling applies, with no new global resource request.
Preserve all historical requests and other owners' locks.

Require clean exact commit and runtime checks before evaluation and after the
worker; one numerical thread; 24-GiB complete Windows Job; 600-second wall and
120-second inactivity bounds; unchanged per-reference 60-second/2,000-callback
and profile mesh limits. Emit initialization, reference, recovery and completion
checkpoints. Prove complete Job cleanup before exclusive same-volume promotion.
No automatic retry, no partial canonical output, no unbounded continuation.

Small sampling, sign/work, hash/mutation, strict-JSON and mocked process tests
precede the run. Preserve source/test hashes and the test report. Record the
actual outcome, including any discrepancy. B2/B3, Q4/S3, public routing, state
and restart formats, dependency metadata and historical evidence are unchanged.
Broad material/load/modal/recovery parity, curved engineering coverage,
independent review and objective beam-shell connection remain required.
