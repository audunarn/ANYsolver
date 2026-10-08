# Native–S3 supporting source review

## Disposition

Complete bounded source review of frozen `author_source_check_v1.json`, SHA256 `2659c2ba69aa0fbdeb4a88f64d4923dbf6dfb8d57c5dcf3a6ce7cb7e6d446711`, and current files matching all15 listed hashes. Seven owned files and two public export dependencies are integrated. No remaining confirmed source blocker in the reviewed slice after the repairs below. **Implemented but numerically unverified**: eight fixtures exist; none has run. No solver/reference imports, numerical jobs, tests/builds, product edits, Git or sibling access by reviewer. Same-family support only, not independent engineering acceptance or release.

## Equations and owner paths

The complete60 common descriptor preserves native42 plus actual S3 formulation18. Native15+shell9 translations are physical; native27+shell9 rotations algebraic. Actual S3 K/M are assembled through formulation slots; zero rotational mass does not suppress affine offset-skin W rotational columns. One residual/tangent includes native elastic/finite inertia, shell Kq/Ma and joint contact. Native own42 contact Hessian is spatial-work converted; both native/shell crossblocks and shell18 diagonal remain. Physical shell stage chart is h²/4, velocity h/2, acceleration1; shell algebraic eta has full unit chart. The endpoint independently projects algebraic rows at fixed physical endpoint and solves physical acceleration. Native cell/nodal finite frame conventions stay distinct.

Structural shell energy .5q.K.q, translation kinetic and penalty storage are separate. Shell P/H now gather actual node DOF slots; zero rate slots are explicitly noninertial placeholders, not skin velocities. Physical force sign is negative potential gradient; internal residual positive gradient; moments share zero origin.

Profile admission is exact: one disjoint free native and one exact centered elastic isotropic S3 V2D, top/+1 polarity with ordered outward director, no generalized section/plasticity/loads/supports/activity, native zero half-cell lift, explicit absolute shell translation and <=.05rad rotation limits. Native zero lift is the reference's factor .5t(t-1) times its shared coefficient, enabling affine physical chords; both native material cells are covered via all three nodal endpoints. This is a small-motion shell development route, not finite shell qualification.

## Consequential findings and repair review

1. **Noncontracting scalar norm bound, repaired.** Original 3*cmax² rejected constant axis-aligned touch unless penetration allowance >=(1-1/sqrt(3))*R. Current componentwise squared Bernstein envelopes at owner294/306 contract to actual normal/edge norms. Positive signed height and each inward rim numerator are checked before squaring; allowed penetration<R makes required height positive. Test `test_touch_constant_plane_tight_budget_and_shared_two_leg_cap` uses P=1e-3R and zero-motion touch; it is unexecuted.
2. **Permuted-node H ledger, repaired.** Original q/Mv reshape in global insertion order was paired with material-node-order positions. Current owner213–217 gathers translations by each actual node DOF list. Permuted-insertion fixture explicitly makes slots noncanonical and compares physical P/H. No numerical PASS claimed.
3. **Inverted initial/direct capsule side, repaired.** Geometry admission now uses exact rational current/reference normals with positive orientation and nondegenerate area before kernel gap/rim. Both initialization and direct restore call it; shared restore admits before issuing state. The trusted-digest inverted-skin fixture constructs a descriptor-consistent bad pose and requires refusal/rollback. It remains unexecuted.
4. **Two-leg aggregate work cap, repaired.** Both legs now share one visited ledger; cap is checked before each interval pop. No second-leg allowance reset. Per-leg counts sum to exact aggregate; the discriminator exhausts the shared cap and requires refusal count unchanged.
5. **Shell physical replay correspondence, repaired after author finding.** Default-preserving reference-pose/match hooks now include shell9 translations. Reference replay resets those physical slots to zero while preserving algebraic shell projection slots; initial displacement is reapplied and matched to trusted contract. Each endpoint matches physical advance from saved predecessor/unknown; actual full stage is reconstructed and compared; endpoint algebraic balance and full contact path/work extras are replayed. Trusted initial translation tamper recomputes digest/accounting but must fail initial physical contract, avoiding a checksum-only discriminator. Fresh split restart plus genuine additional step is required by the unexecuted fixture.

## Swept geometry proof reviewed

Each actual previous->stage and stage->projected-endpoint leg uses affine shell skin/native physical coordinates. N has degree2, signed height degree3 and rim numerator degree4. Exact Fraction power-to-local Bernstein conversion is algebraically correct; full polynomial hulls, not sample signs, enclose each interval. Orientation/area gates are positive before denominator-free squared clearance tests. Positive inward numerator divided by |N||edge| is the projected physical rim distance. Component error propagation covers normal, relative point and edge products; two explicit uniform arithmetic envelopes cover sampled-to-exact and exact-to-rounded family. Complete temporal subdivisions cover both legs; endpoint geometry admission includes actual offset rotations. The saved minimum is honestly labelled a proved threshold floor, not an evaluated minimum. Unresolved enclosure/cap refuses through retryable path failure; transactional trial rollback removes disposable candidates.

## Legacy and test evidence boundary

Shared defaults keep ConnectedState/old graph element-count admission; state field enumeration is owner-specific only for the new route. Native resultant slicing retains the same old length. Existing midpoint arithmetic moved into a private chart hook without changing its default operations. Default physical reset/match hooks reproduce the previous native comparisons; shell additions are overrides. Additive public exports do not change default selectors. Source review supports this preservation; exact historical legacy result/capsule parity after these hooks is still a required prospective check, not measured here.

Eight planned source fixtures cover actual mass/open equations and permuted momentum; full60 two-epsilon FD/contact-isolated work/offset rotations/crossblocks; actual two-step impact/projected path; fresh split restart and trusted tamper; tight touch/shared cap; interior-leg penetration/wrong side; descriptor-consistent inverted capsule/small-motion refusal; side/mutation/cancellation/trial rollback. Cancellation fixture is precancelled and path failure is fault injection, so it must not be advertised as measured in-flight active-contact cancellation. Numerical initialization/descriptor convergence, retained algebraic block admission, derivative assertions, actual impact, complete restart/tamper, CLI/export/runtime/install and historical connected/pair compatibility all remain unexecuted. A prospective480s estimate grants no execution authority.

No temporal/spatial/section convergence, native friction, general curved-reference beam, finite shell motion, arbitrary sides/polarity or independent acceptance follows from this source. No exact angular momentum/energy invariant is claimed for the small-strain shell/descriptor method.

## Exact final file identities

- `src/anysolver/_ge_beam3_native_shell_contact.py` — `791447c155f4b45db21fcb6ff4f7cd7bafcfdfd25ebd246d743eace5b7284bf6`

- `src/anysolver/general_contact/native_transient_shell.py` — `0cbbb335e71cb0a82a0e94cc58e4e51b0f0d7483a9947afe7975da52279d8d27`

- `src/anysolver/_ge_beam3_connected_dynamic.py` — `fc479d74504544e02a3f86145f7c7a7c63aa1baee620b37a4227f83140c792d6`

- `src/anysolver/_ge_beam3_connected_trajectory.py` — `f6869a6c67908767b70612b3b893cdc4d4aeaf1c1100893b0c2fc4b054db9e19`

- `tests/test_general_contact_native_transient_shell.py` — `00d4e2c0ae5064ac95700dfe909195033854618ee786a8683422cf1ad0b340b8`

- `examples/general_contact_native_shell_impact_dev.py` — `f8507e00603dfa273e567d4d56201b2b2bc47bd2b091c4ca0896d62f2eea0925`

- `docs/GENERAL_CONTACT_NATIVE_SHELL_TRANSIENT_DEV.md` — `6fc1b73d2e9caca54cd179c61960a3b23e5819401130deab0dd3c734e1022dd1`

- `src/anysolver/__init__.py` — `f5e1f33cf0e991e2968dd28dff64ffe10d80c4e1f4fd2d4a32094b651b1e9447`

- `src/anysolver/general_contact/__init__.py` — `03d2e676fb056b7b6191bcc7604b496f742897731ab8ddfd0f0cfd7a8678ffee`

- `src/anysolver/general_contact/native_retained_line_s3.py` — `d7d1ca7a88a3c0573b62792ef6538a5e22575430c13766fdc5476e18c5dd4c25`

- `src/anysolver/general_contact/native_retained_line_s3_work.py` — `470c036e015c6e18181233cf1a36b3ee6a74e9b42e36a769d53aa37b73c3633c`

- `src/anysolver/general_contact/s3_skin_work.py` — `6a90f38d00ec2e6d81c8baa22742d76927527711c5c569a2ad4a8c794159d184`

- `src/anysolver/general_contact/overlap.py` — `3c6d98ac0e346669cff3f423d52367766e12d7c9a9d476f761fda2bf1c62deca`

- `src/anysolver/e4_pl_s3_v2d_element.py` — `13ba4b7ba3a34df714ab0a981e770a005242a88bf175dc6328bd3ebcaad90a59`

- `src/anysolver/_native_midpoint_controller.py` — `ed9352bfc4e883367b1c9712d997581391f579657075371c39920b8342042b45`