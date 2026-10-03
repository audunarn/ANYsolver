# Deforming S3 impact driver slice — 3 October 2026

Parent `90e21716`; exact changed sources, environment, scoped commands, outcomes,
resources and isolated wheel identity are in
[source.json](contact_c6_deforming_s3_driver_20261003/source.json) and
[raw.zip](contact_c6_deforming_s3_driver_20261003/raw.zip). This is development
evidence. Existing acceptance identities, failed evidence and consumed authorities
remain unchanged.

## Implementation and verification

The prior fixed-projection profile now also has a named coupled two-target-slope
fixture with independent full modal mass and pressure moments. A separate normal
nodal S3 profile retains source deformation and all target normal modes. Shared
Newmark receives the full general Jet2 work and tangent. No affine pressure
coordinate or independent force/dynamics owner is substituted.

Twenty-nine successful scoped outcomes cover 26 unique cases: the new target
two-slope case, nonlinear gap/force/tangent/wrench, original polarity, hidden
approach controls, nonlinear coupled reference, exact admission, exclusive flags,
V13 active/open restart and identity/budget rejection, second-face proof cutback,
in-proof cancellation, initial dtype rejection, one temporal halving and one old
V12 active restart regression. Repeats resolve actual code/verification changes.
All runs used 180 s/953 MiB caps, JIT disabled, Numba and both BLAS pools at one
thread; imported solver modules resolve to the owned worktree and runtime errors
are empty. Failed test outcomes below remain in the packet.

The independent geometry oracle uses analytic P1 integration of source-normal
projection onto the target plane and complex-step derivatives, not the production
kernel. Coupled Newmark uses an independent nonlinear root solve. Continuous
DOP853 uses the same independent contact force, rtol2e-11/maxstep10 µs. The accepted
structural operator is input, not independently requalified shell stiffness.

| Same mechanical fixture | 25 µs | 12.5 µs |
|---|---:|---:|
| States / cutbacks | 121 / 0 | 241 / 0 |
| Displacement error / 200 µm | 0.04845% | 0.01212% |
| Velocity error / 0.1 m/s | 0.4702% | 0.1183% |
| Reachable-coordinate energy defect | 0.07343% | 0.04507% |
| Conservative minimum gap | −12.2198 µm | −12.2132 µm |

The source varies normally by165.59 nm and the target by10.0496 µm in the default
installed example; momentum error is8.88e-16 kg m/s. These quantities demonstrate
that this is not the prior uniform-source fixture. General nonlinear force work
is checked locally and through the independent trajectory, with separate
regularization storage reporting.

## Failures and review disposition

- `local_a`: two test failures accessed a nonexistent result-field name; the
  polarity control passed. Correcting the test to the existing
  `normalized_weighted_gap_m` field made both independent local checks pass.
- `open_h`: a new test compared the existing immutable gap tuple directly with a
  scalar. Explicit array conversion fixes that test; the unchanged open/released
  V13 restart route passes in `open_i`.
- `impact_c`: displacement-coordinate Newton exhausted nine cutbacks at2.375 ms.
  One same-input corrective experiment used the existing acceleration-coordinate
  Newmark equations. It passes the independent nonlinear reference without a
  tolerance/resource increase. Roundoff amplification is the diagnosed cause;
  no separate timing claim is made.
- Supporting read-only review found that a global open-endpoint test could be
  suppressed by an already touching face. The implemented guard instead tracks
  each originally open corner pair through every exact subdivision; controls
  exercise both the kernel counterexample and actual mapped skins. It remains a
  corner-path guard, not a general weak-pressure-event certificate.
- Larger target corners can make bounds conservative outside projected overlap.
  Preserve this operational limit; do not silently soften or drop their checks.

Supporting OpenAI scrutiny is the same model family as the author. It does not
establish independent engineering acceptance. The final delta report is retained
alongside the packet.

## Installed artifact and remaining scope

Wheel SHA256 `fce7269612702ccfb9bff8a417c963071bbb513a203b33f168987852a3a4156e`.
Every result field and232 imported source hashes match current source. Source and
installed isolated examples took4.52/4.12 s and162402304/162471936 sampled bytes;
single observations establish compatibility, not balanced performance improvement.
Build/install commands and logs are retained. No no-contact performance gate,
release or publication claim is added.

Next close non-affine weak-pressure event exclusion/localization before broader
impact admission. Use this trajectory and independent force oracle to discriminate
path/event errors, rather than a new mesh or time sweep. Rotations, general sliding,
descriptor dynamics, nonlinear materials/friction, native impact and remaining
applications/programme capabilities are not established by this slice.

[Usage and explicit limits](../GENERAL_CONTACT_C6_DEFORMING_S3_DEV.md)
