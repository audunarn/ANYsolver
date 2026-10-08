# Native retained-coordinate normalization — 3 October 2026

**IMPLEMENTED_NOT_QUALIFIED.** Explicit opt-in normalization is delivered for
the curved-Q4 material point route. Existing profiles, defaults, checkpoint
meanings, mechanics, material laws and physical tolerances remain unchanged.
Source parents: solver `1cb98e95`, consumer `b6ad370`; final installed source
identities are in the raw artifact manifests.

## Decision and evidence

The native retained layout is six cell rotations followed by six force and
twelve moment coordinates. The older curved normalization treats the eighteen
resultant coordinates as three six-component wrenches. A bounded SI physical
similitude comparison used length factors 0.1, 1 and 10, with unchanged forces,
stress laws and Young's modulus divided by the squared factor, transformed
generalized stiffness/yield metric, reference geometry and inertia. This is not
an arbitrary unit-metadata conversion or a qualified spectral inertia test.

The existing native-role scale builder is homogeneous to `2.22e-16` relative
error. The old arrangement mis-scales eighteen coordinates over two elements,
with maximum relative ratio error 9.0 at both nonunit factors. All six numerical
force/arc routes reached equilibrium. Their physically normalized outputs agreed
across length factors within `3.50e-11` in the reported maximum-component relative
measures. Thus there is a dimensional normalization defect, but this screen
does **not** demonstrate wrong equilibrium, a convergence gain or formulation
failure in the old route.

The probe's final work-inventory reporter accessed `ArcResult.attempts` instead
of `increment_attempts`. Its six raw rows retain that reporting failure. Seed and
arc outputs had already been written. A separate interpretation records this
exact limitation and the completed numerical routes; no solve was repeated to
repair the reporter and no missing work count is invented.

## Product and compatibility

On the existing `LinearDefinition`, select
`retained_scale_policy="native_force_moment_roles_v1"`. Default `"profile"`
preserves the prior arrangement and original model identities. Nondefault
selection is admitted only for the explicit curved material point reference
policy. It reuses the native-role builder already used by other admitted routes;
no element operator or constitutive update changes. The selected policy is
retained in the owned definition, advertised in capabilities and bound to a
distinct compiled model identity. Force and arc snapshots reject incompatible
scale-policy owners before publication. Virgin reference construction preserves
the option without transporting loaded histories.

The existing ANYfem point consumer accepts the same explicit keyword. Its new
strict record is
`anyfem.experimental-ge-curved-q4-point-panel-material-native-scale-v3`.
Older records omit the field and retain their original round-trip/dispatch.
Missing, unsupported or misplaced policy fields fail explicitly, as does an
installed solver lacking this definition contract. Native Project persistence
uses the existing consumer/factory and preserves the selected model identity.

## Checks actually run

Repaired focused solver source suite: **4 passed**, 65.504 s / 181,903,360 sampled
process-tree peak bytes. A final force-checkpoint identity assertion was added
after that source run and verified in the installed route. Source consumer checks
had nine passes and two filename-fixture failures; only those two were repaired
and repeated, giving **11 distinct source passes**.

Installed solver: **7 distinct checks passed**. Six passed in the first execution;
one correctly rejected an incompatible force snapshot but its message assertion
expected the wrong wording. After correcting the assertion, only that check was
repeated. Coverage includes:

- Native coordinate-role homogeneity at factors 0.1, 1 and 10.
- Simultaneous shell/beam yielding, two arc increments, physical response
  similarity, exact continued checkpoints and detailed station/material restart.
- Force and arc policy mismatch rejection, unchanged default model identity,
  invalid selection and virgin reference preservation of a loaded source.
- Affected legacy/default material admission, optional elastic shell arc and
  historical flat-panel identity/linear solve/recovery/checkpoint controls.

Solver wheel SHA256:
`780e77539f6c511026ff626485af7d583cc5562f7f4c7452e0fbc45222489e34`.
All **413** source/wheel/site modules matched. First execution: 88.073 s /
184,999,936 bytes. Corrected-assertion-only execution: 13.326 s / 179,904,512 bytes.

Installed ANYfem: **12 passed**, 24.615 s / 202,043,392 bytes. This includes old
records, new optional-J2 native records, strict negatives, native Project
save/reopen, an explicit nonrigid virgin reference, simultaneous yielding and
exact detailed material arc restart through the new paired solver artifact.
Consumer wheel SHA256:
`937eb59f99fc72463af3daad8c7363755fb957648f81d7647591305af61d3374`.
All **98** consumer source/wheel/site modules matched. Actual imports, one-thread
numerical pools/Numba and disabled JIT were checked. All jobs stayed within
600 s / 1 GiB. Timings are verification costs, not optimization measurements.

The first solver implementation lost the new field while copying the owned
definition; restart detected the mismatch. Compilation now retains the field.
A reference fixture initially translated shell hosts without translating free
beam nodes; the existing native tangent/frame guard correctly rejected it. Both
failed executions remain retained, along with the consumer filename errors and
installed message assertion. No failed scientific gate was relabelled passed.

## Review and boundary

Integration-owner review traced native ordering, dimensional congruence,
definition ownership, identity binding and strict consumer framing. This and the
native/same-code checks do not satisfy independent scientific acceptance; optional
cross-family reviewers remain unavailable. The scalar option is immutable,
operator preparation remains compiled once, and mutable state/recovery ownership
is covered by the continued/restarted routes.

No physical-material roof capacity, refinement-independent continuation, arbitrary
unit systems, external nonlinear agreement, new attachment law or aggregate
G0–G6 gate is accepted. No main merge, publication, new global framework, default
change, formal F03 run or external repeat occurred. A bounded declared material
roof route is the next application decision, not another normalization sweep.

[Summary and execution identities](summary-v1.json),
[installed physical outputs](physical-outputs-v1.json),
[raw diagnostic, interpretations, source, runners, artifacts and failures](raw-evidence-v1.zip).
Raw SHA256:
`780228a372a19ab985bdc248284342978145f66f95bde0d899b06d26279f31ca`.
Environment maps and contaminated historical evidence were excluded.
