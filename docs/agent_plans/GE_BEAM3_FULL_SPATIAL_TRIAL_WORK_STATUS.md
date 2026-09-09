# Full spatial continuum trial-work diagnostic completed

Frozen commit 9555a25fe6748c1132eb36ae8ed798515976501a,
tree 657d17dbb13068139adae63c4958eab78999d4dc. Four research-only files.
The complete targeted test inventory passed: 27 tests in 0.38 seconds.
An earlier 26-test inventory passed before the saved-input parsing test was
added; these inventories overlap and are not additive. Diff check passed.
No production implementation, B2/B3/S3/Q4 mechanics, section state, recovery,
API, package, version or default change.

## Scientific result and limits

Both saved +/-0.0065 continuum equilibria admit a numerically resolved negative
second-work direction in the complete six-component spatial trial space.
All components were available; no planar restriction or quarterspan numerical
controller was imposed as a physical support. The sine trial fields are continuous
through all reference segments and vanish at both physical clamps.

| Sine modes per component | Dimension | Positive-endpoint lowest Ritz value |
| --- | ---: | ---: |
| 8 | 48 | -0.04506928042160116 |
| 16 | 96 | -0.04961026927057638 |
| 24 | 144 | -0.04984621205525211 |

The separately evaluated selected trial, not the eigensolver estimate, is the
work witness. Positive-endpoint 64/128-point quadratures give
-0.0498462122520339 and -0.04984621225168194. Negative-endpoint quadratures give
-0.049846212251854545 and -0.049846212251565464. Relative quadrature differences
are below 7.1e-12. Cross-product direct work agreed with matrix work at the
unchanged normalized 1e-11 threshold. Integrated finite-rotation energy
differences, independently evaluated with matrix exponentials/Frechet derivatives,
give extrapolated second variations -0.04984621221135419 and
-0.049846212236363124. Normalized directional errors are below 3.842e-11,
well below the unchanged 1e-7 requirement. Both negative-work margins exceed
100 times the respective directional discrepancies.

The L2 trial Gram matrix is a normalization device, not physical mass. The Ritz
values are neither frequencies nor buckling load factors. Raw Hessians, Gram
matrices, coefficients, direct work and potential samples are saved externally.
Raw symmetry was checked before disclosed roundoff symmetrization for eigh.
No coefficients, reference fields, continuum equations or tolerances were tuned.

This is numerical continuum instability evidence for the two particular elastic
equilibria, not a beam-element correctness failure. The earlier native negative
work at +/-0.006 remains preserved, but it concerns different states. A same-state
native capture at +/-0.0065 is still required before claiming that the discrete
and continuum stability results agree. No full continuum Morse index, interval
certificate, stable postbuckling branch or independent author review is claimed.

## Process and preservation

Positive smoke completed in 1.312s; negative and the two replicas completed in
1.415s each. Wave approximately three seconds. Peak recorded process-tree memory
152367104 bytes. Four successful zero exits, all Windows Job trees empty, no
timeout, memory failure or retry. Each child one numerical thread; maximum three
concurrent; frozen 60-second inner, 600-second/24-GiB child and 1800-second wave
bounds retained. Source and runtime guards passed before/after evaluation.
Native and continuum equilibrium solvers were not rerun.

Both same-sign trial-work replica pairs were byte-identical. Read-only independent
saved-data arithmetic used Python Fraction to evaluate each stored 144-dimensional
matrix's quadratic work exactly. Both signs were negative, and each L2 norm agreed
with one to within 1e-11. It also recomputed the saved finite differences and
checked process receipts, replica bytes, canonical parsing and aggregate hashes.
This proves the sign of the rounded saved-matrix work exactly, not an exact or
interval sign for the continuous differential operator. The auditor did not
reintegrate the continuum or independently author the mechanical theory.

External archive:
C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-spatial-trial-9555a25-20260909.
34 manifest-bound files plus manifest, verified by exact path extent, byte count
and SHA-256 in both exclusive staging and external copies. Original TEMP retained.

Manifest 4461 bytes, SHA-256
7b994d3dda0bafeb3714b238b69e48619217d5df2b90fdbe5a62215ba14b81eb.
Saved audit 962 bytes, SHA-256
10cd86d5f38f7987cba0e1311c6da0d6c54defd0fc3ec5ea49030164bc129ccf.
Positive trial-work 596186 bytes, SHA-256
5feda98ccba52eecdd88272002ee3961264f1afd9d11f8f4edab8cc499bec8f6.
Negative trial-work 596048 bytes, SHA-256
feeb287a52d5a1f05a5d88d95ecfffef64467b6c260923a782b74bf8b899341b.

## Next gate

Freeze a separate actual-owner native operator capture at the same accepted
+/-0.0065 checkpoints under the precise geometric-work policy. Do not advance,
relabel or add targets to the existing continuation programme. Verify that the
capture removes only physical end clamps, not the numerical controller, and
retains internal rotation and algebraic variables consistently. Compare admissible
spatial work and signs with this reference; do not equate differently normalized
Ritz values with frequencies or use a planar determinant to infer full inertia.

Full nonlinear/material/state/solver parity, broader geometries/slenderness,
independent author review, installed opt-in selection and objective eccentric/
curved beam-shell connections remain open. No activation or release.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
