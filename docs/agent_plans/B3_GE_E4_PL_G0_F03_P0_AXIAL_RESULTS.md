# F03 classical P0 axial screen: six-case exploratory result

22 September 2026. The source-frozen P0 norm screen at
`05f766783b4131edcbf391c904ef0b9d3172af73` completed six of six
registered **classical small-strain, unloaded** cases once. This is
`EXPLORATORY_COMPLETE_NOT_QUALIFIED`: no native multiplier policy, loaded
response, signed retained-yaw result, or G0B/F03 gate is accepted.

The registration is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-p0-axial-registration-v1/registration.json`
(SHA-256 `d8d10ffcd85480458866704d4037d386899cdf2d5ef58ea30b908c7fabad6ebb`).
Raw cases and their receipt are at
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-p0-axial-cases-v1/`
(receipt SHA-256 `c8e516834b6822edd787a886e27be80690978b88c30db9dfd820f1609d697c8c`).
The previous classical P1 axial patch adjudication is separately preserved
with SHA-256 `290621987a79011f0607d7b771f8f323b7cce9d0a04090077ac35ca43ac0436f`.
The read-only independent evidence review found no identity or registered
terminal blocker; it did not reassemble or rerun the matrices. Its decision
is recorded at
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-p0-axial-adjudication-v1/adjudication.json`
(SHA-256 `93a4a94ef52cc2761dedc442de8486e3f8d909a505a864025e3e70a33b5e65bd`).

| Topology | Nm=8 beta bracket | Nm=16 beta bracket | Nm=32 beta bracket |
|---|---:|---:|---:|
| Q4 | [0.46419157, 0.46419288] | [0.36295685, 0.36296427] | [0.25970005, 0.25975996] |
| CST-CB | [0.45863306, 0.45863435] | [0.35362747, 0.35363391] | [0.26004562, 0.26010561] |

Here `Ns=16, Ny=8, Nb=64` are fixed and only P0 mortar resolution changes.
The finite-mode analytic lower/upper dual Gram uses modes 0..1023. The
maximum relative beta enclosure width is `0.000231`, maximum primal solve
residual `5.06e-13`, and maximum generalized eigen residual `1.44e-13`.
All six sparse supported-energy screens found no negative mode; this is a
numerical screen, not an arbitrary-matrix positivity certificate. The
largest per-case elapsed time was `0.324 s` and sampled end RSS `67.6 MB`,
within the registered **post-case observational** thresholds of 60 s and
1 GiB. They are not hard resource limits.

The lower P0 beta at Nm32 than Nm8 on both fixed primal meshes means this
norm-only change does not remove the observed small-patch axial sensitivity.
The earlier P1 discrete norm gave different Nm8 values and similar Nm32
values; those are different spaces/norm definitions and cannot be called a
controlled physical performance comparison. This six-case sequence is not
a joint shell/beam/interface refinement proof, and the native yaw jump and
six-channel attachment work remain unresolved. Earlier failed loaded P0
and coarse-P1 screens are neither retried nor overridden.

Next F03 work requires a prospective physical connection law or revised
trace contract that can handle native retained variables and discontinuous
yaw while passing the registered loaded, work, rank, refinement, and
drilling/transverse-shear gates. External 3D footprint decks are a separate
unexecuted reference feasibility fixture, not qualification of that law.
