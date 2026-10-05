# F06 loaded-transport V1: bounded failure diagnosis

No numerical job or source edit was performed. This reads the frozen V1 evidence and current origin-state definitions; it proposes a diagnostic recorder, not an assertion bypass or passing result.

## What the saved run establishes

V1 has two failures. Frozen test_case.py SHA256 is 649bec0d27b41d9df2d6458dd02e9f57f420c22d4f0ddb46a8d3ad4073207e92; identity.json reports 387 installed product modules matched. Q4 completed prefix, actual reset, direct restore and all final branch physical/material comparisons, then failed shell rotation coverage. Its XML records:

- control shell maximum loaded rotation: .048120687138725096 rad;
- control shell maximum actual consecutive-increment commutator: 1.4133716695172652e-6 rad.

The .05 rotation assertion is first, but the already recorded commutator also misses the unchanged 1e-5 floor. Beam/other-branch coverage was not reached and is not recorded.

S3 completed the numerical branches and passed exact prefix/reset/restore material fingerprints. The first final control-versus-reset comparison failed at the whole-origin fingerprint, before subsequent final field comparisons. The hashes are control 209428b1cd0f9bd245441de2fcd784d4fa83e16aec50378f6e508e8a31d6e1d0 versus reset 8006ee7d429a6898edc1938fefdcb78b4501b7bee78c3281d19310778072a2eb. No origin trees or differing leaves were retained. Therefore V1 cannot distinguish constitutive-history error from recomputed floating-point differences; it cannot be called a material parity pass.

## Whole-origin hash is broader than irreversible history

The fingerprint serializes both driver._shell_origins and driver._beam_origins. The S3 V2D origin required-key manifest includes:

- true material history: plastic_strain and alpha;
- newly evaluated endpoint/constitutive data: committed_total_u, committed_constitutive_u, layer_strain, layer_stress, station_generalized_strain and station_generalized_resultant;
- immutable model/initial-field metadata and a state_integrity_sha256 derived from the complete state.

FinitePointDriver._accepted_shell_material_origins seals each accepted S3 candidate from the independently computed local_q. The V2D response fills strain/stress/generalized arrays and the two committed-u arrays; seal_solver_integrated_nonlinear_state records local_q and regenerates its integrity digest. Equivalent physical states reached in different charts need not produce bit-identical recalculated endpoint arrays after a new Newton solve.

At the same accepted predecessor, reset changes only the shell chart representation and keeps origin objects untouched; exact origin equality remains the correct invariant. Direct byte restore of that predecessor also retains the exact material content. After a **new accepted increment**, exact equality of the entire sealed origin is stronger than physical material-history invariance, and a digest cannot identify which role failed. This is an explanation to test, not a diagnosis that the observed discrepancy is harmless.

Current fixture is elastic: no shell J2 curve and beam yield threshold 1e20. S3 plastic_strain/alpha and beam GeneralizedHistory.plastic/accumulated should remain their exact zero histories. Any nonzero irreversible field is consequential here and must not be normalized away.

## Concrete recorder and comparisons

At prefix, immediately after reset, after restore, and after final continuation of **all three branches**, detach the complete origin trees and save them even on assertion failure. Record before comparison; a finally block writes data and failure metadata and re-raises the original failure. Retain the full hash as a diagnostic and keep all existing mechanical/coverage assertions. Do not stop at the first hash mismatch or omit later physical metrics from the diagnostic record.

For every differing leaf record its full path, schema/shape/type, raw left/right values (arrays on disk), maximum absolute difference/index, and applicable unit-normalized difference. Check all leaves: metadata and digest changes are reported, not silently filtered. Use this field treatment:

| Fields | Comparison / independent scale |
|---|---|
| Schema, formulation/layout/material mode, element/node IDs, element_identity_sha256, num_layers, solver_kinematics, initial_field_provenance | Exact structural/metadata equality |
| initial_generalized_prestrain, initial_generalized_resultant | Exact prescribed input equality; zero inputs remain exact zero |
| S3 plastic_strain, alpha; beam section_identity, plastic, accumulated | Exact elastic history/identity invariants for this fixture; preserve normalized high/low pairing in beam history |
| committed_total_u, committed_constitutive_u | Element-local coordinate triples: translation /L, rotation in rad; compare in the same declared local frame |
| layer_strain | Dimensionless engineering strain |
| layer_stress | Pa /E, with E from the frozen material; also verify elastic stress increment is the material matrix times the corresponding strain increment |
| station_generalized_strain, initial_generalized_prestrain if diagnostically expanded | Membrane/shear dimensionless; curvature times L (order: membrane3, curvature3, shear2) |
| station_generalized_resultant | Membrane force /(E t), bending moment /(E t³/L), shear force /(G t); t and G=E/[2(1+nu)] are frozen physical inputs |
| state_integrity_sha256 and any content-dependent activity witnesses | Each state must independently validate; differing content digests are diagnostic consequences, not interchangeable metadata identities |

The existing dimensionless physical 1e-9 criterion provides the prospective scale for endpoint/strain/resultant comparisons; it must be stated before the diagnostic, not chosen from observed differences. Derived stress consistency and existing physical force/reaction/gap/work tests remain independent checks. Elastic zero irreversible histories and exact predecessor transport are not replaced by tolerances. The complete V2D state validator, including activity witnesses, must still accept each branch separately.

Branch positions/frames, multipliers, reactions, retained resultants and point actions must also be recorded before material assertions; record every coverage scalar before asserting either floor. V1 currently does not tell whether those final S3 comparisons pass. A large material difference, nonzero plastic history, failed state validation, or unexplained stress/strain inconsistency requires product/path investigation; small derived differences alone may explain the hash failure but do not repair missing coverage.

## Is target 1.25 sufficient?

The rotation deficit is only about 3.9%, but commutation needs about a 7.08-fold increase. Thus this is not solely a near-boundary angle miss. A proportional linear angle estimate gives .06015 rad at 1.25, but predicts no commutation at all; noncommutation comes from changing physical increment axes.

For a smooth proportional path theta(t)=a t+b t²+..., leading commutators are third order. With the fixed prefix (.125,.5), replacing final target 1 by 1.25 gives the leading consecutive-increment bracket coefficient ratio
\[
 \frac{(.5-.125)(1.25-.5)(1.25-.125)}
 {(.5-.125)(1-.5)(1-.125)}=\frac{27}{14}\approx1.93.
\]
That heuristic would yield only about 2.7e-6 rad, still below 1e-5. Appending 1.25 after 1 is a different increment sequence and does not establish the needed increase either. This asymptotic estimate is not a load-response oracle or a proof that 1.25 fails, but there is no defensible assertion of success from V1.

Conclusion: preserve the failed coverage; do not justify a 1.25 run as a known threshold repair. The next already scheduled mechanical discriminator should record actual physical increment axes/commutators and complete material leaves. Its outcome can determine whether a genuinely different path/mechanism is required. The current finite owner forbids load-pattern replacement, so a direction-switched staged load cannot be silently simulated. No changed coverage floor, repeated execution, material pass or F06 acceptance follows from this diagnosis.
