# Q4/Q4 monolithic force-loaded bending outcome

The installed ordinary force solve now completes the genuine two-body Q4/Q4 bending fixture using supported-force monolithic contact. The coupled proof, alternate positive scale, fresh active restart, public refusal checks, impacted legacy controls and current CLI pass. This is bounded development evidence; engineering acceptance and release are not established.

## Implementation and mechanical scope

Four product files change. `core.py` admits the exact augmented+monolithic Q4/Q4 selection; `s3_patch_static.py` supplies `Q4_Q4_PATCH_REFINED_MONOLITHIC_AUGMENTED_STATIC_DEV_V0` and connects its original-bilinear chart/whole-face/error-enclosed path guards; `s3_patch_augmented.py` admits Q4/Q4 to the existing fixed-supported-force quotient derivative; `static_path.py` connects the profile and reports `Q4_Q4_PATCH_REFINED_MONOLITHIC_PATH_STATIC_DEV_V0`.

The existing ordinary dead-load-to-zero-control path hook, semismooth engine, Jet2 kernel, elements, work maps and automatic compiler are unchanged. No public signature/default changes. Original 24-coordinate bilateral Q4 geometry, pointwise reference Jacobian, shared fine-Q1 support and all six material-node pressure IDs remain authoritative. The new exact profile requires augmented+monolithic, whole-face, exact fine-Q1 support and the existing explicit derivative controls. Friction, finite-rotation/corotational structural routes, warped reference faces, arc, transient and selfcontact are refused. Small free rx/ry use the inherited linearized director skin map; reference orientation semantics are unchanged.

For S>0, gbar=w/S and p=z/S. The existing fixed-z work gives `Ru=Rstruct-Dgbar.T*z`; its tangent includes moving support and both-body projection/normal Hessians. It is not a fixed-multiplier augmented tangent. The coupled crossblock is `-Dgbar.T`. The existing complementarity is `C=z-max(0,z-c*gbar)`, with constant positive `c=regularization*full_reference_Q1_support`. All supported force rows remain. No pressure mode was dropped.

The physical fixture retains the prior two upper/four lower Q4 topology, total -1e-4 N upper end load, upper left clamp, lower corner normal supports and minimal inplane anchors. There is no common-source-uz guide. Rotations and independent target normal coordinates remain free. Skin positions use `reference_skin+u+offset*(theta cross reference_director)` with -.025/+ .025 m offsets. The nominal reference skins are coplanar; their represented binary heights differ by approximately -1.735e-18 m. This is not a finite-rotation or deformed-normal offset formulation.

Ordinary force controls are the supported structural defaults, explicit tolerance1e-12, two increments and maximum12 iterations. The inherited explicit pressure_tolerance1e-8 Pa satisfies augmented admission and binds restart; monolithic acceptance uses the force residual C, not that pressure control. There is no claim that every inherited augmented option is used as a semismooth convergence gate.

## Actual numerical evidence

Frozen equilibrium/wrench gates are 1e-6 with separate positive scales Fref=1e-4 N and Mref=1e-4 Nm about origin (0,0,0). Complementarity is L1(C)/Fref<=1e-8. The gap gate remains50um; directional gates remain1e-5.

| Check | Observed result |
| --- | --- |
| Independent matched contact operator error | 6.938893903907228e-17 |
| Independent hard-contact linear reference equilibrium | 1.0508260548186068e-14 |
| Contact coupled u/z directional errors, two h | 8.563439876087744e-9 / 1.9865784545139206e-8 |
| Full structural/contact Ru directional errors | 5.691543005665896e-14 / 1.358898028148091e-13 |
| Complementarity C directional errors | 6.262989965027587e-10 / 1.2596546514644035e-9 |
| Actual full free-coordinate equilibrium | 9.416990668789461e-15 |
| Actual full L1(C)/Fref | 1.2911771464110076e-12 |
| Independent authoritative binary-pose gap lower bound | -2.581388703799186um |
| Upper displacement range / lower normal displacement norm | 2.3815770700308454um / 2.990251289171019um |
| Upper / lower rotation norms | 7.4721289235658705e-6 / 1.6091828440908927e-5 rad |
| Rotational skin displacement norm | 4.43550767402423e-7 m |
| Physical-skin force / moment errors | 3.3881318308080934e-16 / 2.4432169137235566e-16 |
| Structural-coordinate moment error | 1.5553254916049162e-7 |
| Fresh resume u / z endpoint difference | exactly0 / exactly0 |
| Frozen alternate c2000 versus c1000 u / z difference | exactly0 / exactly0 |

The two active supported forces are 4.203079084741908e-5 N and 9.651624133642396e-5 N; the other four are zero and every support remains positive. All z>=0. The full coupled proof varies both authoritative bodies' displacement coordinates and z, checks contact separately from structural Ru to prevent structural stiffness masking contact errors, preserves smooth active masks and checks the declared complementarity kink rule on a one-sided ray. The kink control is a complementarity-rule check, not a new global nonsmooth geometry qualification.

Independent Fraction Q1 integrals supply shared support/gap rows. The reference enumerates64 hard-contact active sets with `H=G_free*K_free^-1*G_free.T`, without a penalty diagonal. The qualified structural K is reused explicitly. All six support-weighted finite-reference compliance modes are detected; this does not establish universal pressure stability or inf-sup convergence.

The actual nonlinear displacement differs from that linear reference by 1.965417431654545e-6 relatively. It is reported separately, without a 1e-6 nonlinear/linear code-comparison claim or an unproved truncation allowance. The exact static gap proof uses the actual authoritative binary skin corners after independent skin reconstruction, all face pairs and all nodal/corner combinations of original Q1 geometry. It is a conservative all-material-pair sufficient bound, not an exact projected minimum or a new finite-rotation qualification.

Endpoint external work is 1.988314883822773e-10 J. Upper/lower instantaneous contact residual contractions are 1.7091593074857848e-10 J and -1.7091589106839773e-10 J. These are endpoint contractions, not integrated path work. The nonzero structural-coordinate moment deficit and its second-order rotational skin term are retained within the frozen gate.

## Restart, refusal and compatibility

Exact snapshot step inventories are full[1,2], alternate-c[1,2], prefix[1], resume[2]. Fresh resume reads its own active prefix checkpoint and binds the full report SHA-256. State retains normal supported forces and pressure-space identity. Actual public calls reject changed automatic provenance, continuation into the admitted historical penalty enforcement contract, altered checkpoint force content, friction and unsupported finite-rotation/arc routes. A direct manager refuses warped reference geometry; selfcontact validation refuses. The actual legacy-valid multiple-beam transient public branch refuses the static-only Q4 selector before pair inventory, manager allocation or boundary mutation.

Public precancellation and an intentionally exhausted one-iteration elastic trial preserve declared FEModel fields. The latter has no accepted increment or accepted-candidate commit, and returns zero accepted displacement. The commit trap establishes this bounded accepted-state behavior. The unchanged semismooth owner evaluates a structural trial before contact linearization; generic hidden material-trial rollback/nonlinear mutation qualification remains open.

Existing Q4/S3 monolithic mapped work/tangent and the unchanged Q4 penalty bending workflow pass against the current installed artifact. The ordinary force adapter, geometry/Jet2 equations, defaults and automatic serialization are reused by impact, not requalified broadly.

## Artifact and resources

Fresh private wheel SHA-256: `92f5da4ab8c3ff5da72b380d2a5fd95b63ec74eba400f11b888a5fab88261eec`. There are629 payloads: four changed and625 byte-identical to the prior immutable d23e40... wheel. Current source matches the four installed payloads. The installed CLI reports the actual new contact-path capability and completes.

Twelve guarded jobs used exactly148.24805949999427/600 process-wall seconds;451.75194050000573 remain, including the unused protected60-second final reserve. Maximum job21.09296410001116 s; peak sampled process-tree RSS199.8671875 MiB. Ten JUnit invocations comprise eight passes and two retained test failures; build and CLI are the other two jobs. All3286 private module imports authenticate against the current artifact, JIT disabled, Numba/pools1. No job is active.

Both retained failures are safety-test contract/setup errors: the first expected a later friction message despite an earlier correct public refusal; the second referenced nonexistent `ContactInteraction.source` instead of public `surface`. Corrective safety passed. No product repair, physical tuning or extra artifact was needed for either. Earlier bending and other scope failures remain preserved independently.

Raw evidence: `C:/ANYworkspaceWork/contact_q4_pair_monolithic_20261008/`, with immutable commands/source/input/build/install/runtime/full logs/results, ledger, CLOSURE.json and IMPACT.md. The metadata reconciler and lead inspector read/authenticate saved artifacts; neither replays mechanics. Lead scientific adoption/acceptance and Git delivery are separate.

## Recommended next connected delivery and concrete boundary

An existing zero-control ContactPathProgram can carry signed force waypoints for press/lift/repress and exercise monolithic active-set release/recontact, with a fresh restart at release. This needs no new driver. No cyclic solve or refinement was run in this scope.

Under the unchanged nominally coplanar fixture, globally strict positive opening clearance is impossible: clamped upper node1 retains physical point(.1,.1,.04-.025), which lies over the unloaded horizontal lower Q4 skin at z=-.01+.025. With z=0 and no lower load, the elastic lower body returns to its reference position; that upper boundary point has zero ideal clearance (a tiny negative represented-binary clearance), even while the free upper interior lifts. Thus a cyclic zero-pressure/interior-opening check can be meaningful, but cannot honestly claim strict separation of the entire footprint for this fixture. A next strict-opening deliverable needs lead adoption of a prospectively positive reference clearance, or an explicitly narrower touching-boundary/interior-opening definition; preserve this fixture unchanged and do not tune it after a failed opening gate.

Remaining programme obligations include spatial/pressure stability, independent nonlinear reference/truncation control, finite rotations/director evolution, general hidden material-trial rollback and engineering acceptance/release. The next bounded cycle should address the above opening boundary explicitly before execution.
