# E03 complete-force equation audit — source controls verified

This additive diagnostic prepares one output-only candidate and independently
derivable force recovery. No source import, collection, test, numerical solve,
CCX run or build was performed by its author. It changes no frozen deck, reader,
physics, support, criterion or historical evidence. Every diagnostic remains
not qualified, not E03 accepted and unscored for response accuracy.

The existing coarse CCX process exited zero but its unchanged strict parser
refused common-origin physical force/moment balance. Saved ROOT-only RF summed
approximately `[0.16467345, 0, 4.99058843]` N under total applied `[0, 0, -1]` N.
That failure is preserved. Both original physical primaries were consumed;
remaining verification time does not authorize a new physical execution.

## Recovery contract and sign

`audit_equation_forces` requires complete three-component element internal nodal
forces `g`, complete declared applied forces `p`, coordinates, physical support
DOFs, equation coefficients `C`, explicit distinct dependent pivots and provenance.
Maps use positive integer node IDs, exactly the declared node inventory. Omitted
forces are refused; sparse applied-load metadata is explicitly expanded to zeros
by `e03_inputs`. Bounds are333nodes,48equation rows and24terms per row. The local
dense solve is at most48square; there is no production/global dense-solver claim.

Choose physical equation-action signs through

```text
g = p + r_SPC + C^T lambda
(C^T lambda)^T delta_u = lambda^T C delta_u = 0 for admissible delta_u
```

At dependent DOFs `D`, support reaction is zero. Recovery solves the full coupled
system `A lambda = (g-p)_D`, with `A = C_D^T`; it never assumes diagonal pivots.
Loads on pivots are allowed and subtracted. Then `a=C^T lambda`, support reaction
is `(g-p-a)` on the real supported DOFs, and that same residual on all other DOFs
is reported as free equilibrium residual. No multiplier is inferred from a global
force/moment deficit. No native multiplier is substituted for an external one.

The report includes each equation's six rigid-work coefficients, common-origin
force/moment wrenches of `g`, `p`, equation action, support reaction and free
residual, and the external support-plus-load balance. Moments use `x cross f`
about the same world origin. Nonzero observables remain visible; the diagnostic
does not turn them into passes or fit them away. SVD rank admission uses
`rows * binary64_epsilon * largest_singular_value`, a local numerical conditioning
guard, **not** an interface-stability or scientific-acceptance threshold.

Missing/nonfinite force data, invalid or duplicate pivots, pivots on supports,
duplicate/zero equation terms, singular/numerically dependent local systems and
intermediate arithmetic overflow are refused. Inputs and returned provenance are
detached; model and force hashes bind the exact declared arrays. `input_identity`
supplies those hashes without running the local force solve.

## Exact-release source evidence and remaining binary boundary

Root obtained the source archive from the author's official
[CCX2.23 source download](https://www.dhondt.de/ccx_2.23.src.tar.bz2) without executing
its contents. Three exact extracted files were inspected under
`.qualification/b3-ge-e4-pl/r8-e03-coarse-dev-20261007-v1/ccx-source-review-v1/CalculiX/ccx_2.23/src`:

* `results.c` calls `resultsforc` to construct the reduced matrix-system force.
* `resultsforc.c` subtracts coefficient-weighted MPC forces from independent
  nodal terms while constructing reduced force `f`, then restores them to `fn`
  at nodes connected to elements, including supported independent terms.
* `frd.c` writes `fn` as RF/FORC through `frdvector`.

This confirms the release-source distinction between uncondensed element nodal
`fn`, reduced-equation `f`, equation action and physical SPC reaction. Source
version and executable version labels do not establish that the pinned Windows
binary implements that source. Actual build/semantics correspondence remains
unproven. The present ROOT-only output therefore remains refused and is not
reinterpreted as recovered physical reaction.

Generic algebra admits an explicitly synthetic gradient producer for controls.
Saved CCX ingestion requires producer `CalculiX`, version `2.23`, field `RF/FORC`,
the pinned executable SHA256, exact model/force identities and semantics
`UNCONDENSED_ELEMENT_INTERNAL_NODAL_FORCE_GRADIENT`. It additionally requires an
independent confirmation record binding exact-release source and evidence SHA256,
review/reviewer IDs, evidence reference, exact binary/version and
`runtime_binary_correspondence=INDEPENDENTLY_CONFIRMED`. Missing, master-only or
cross-version confirmation is refused before RF parsing. Confirmation is caller
evidence to be independently reviewed by root; these fields do not prove its truth
or confer qualification. Current source inspection alone cannot populate that
runtime-confirmed record. Fictional records in synthetic controls are explicitly
not review or physical evidence.

Runtime correspondence may be checked by independently observed analytic
SPC/MPC control forces and work, under method
`independent_analytic_spc_mpc_observable_control` with `control_evidence_sha256`.
That method is admissible without byte-for-byte source-build identity. A verified
source build identity is another admissible method. Neither is currently adopted.
The confirmation must name its method, source-archive hash and exact inspected
source-file hashes, pinned binary hash and independently reviewed evidence.
These are evidence bindings, not a substitute for inspecting that evidence.

Inspected source-file SHA256:

* `resultsforc.c`: `26d324920e8ad16a2db0c736d524a03781880863e0cd089c0a4ce22d7410c505`
* `results.c`: `9113a4984342355ff15bb16a609c5bdb034183c951719b064037b3858eac24dd`
* `frd.c`: `6439bca2ae53c813ab6887c3c560dd15db5947fd8cf9b9f01ada5753d5ed9915`

## Connected output-only candidate

`prepare_complete_force_output(deck, metadata)` requires the exact original deck
hash and immutable metadata identity. It changes precisely one card:

```text
*NODE OUTPUT,DOUBLE,NSET=ROOT       -> *NODE OUTPUT,DOUBLE,NSET=PHYSICAL
RF                                  RF
```

The card remains at the same location. Byte-for-byte reversal verifies that all
geometry, elements, equations, material, supports, step and applied-load bytes
remain unchanged. The U/PHYSICAL output also remains unchanged. Detached candidate
metadata retains the original metadata, original/new deck hashes, all333force
output nodes and the original49physical support nodes separately. Output inventory
is never adopted as a new support condition. Preparation launches nothing.

`audit_saved_complete_force_output(case, prepared_metadata, frd, provenance=...)`
requires the exact level0/+offset metadata and independently confirmed CCX
provenance. It reuses the frozen strict DOUBLE inventory reader with a detached
projection: that reader's `root_nodes` slot supplies expected FORC node IDs only.
Recovery obtains the real support DOFs from original E03 metadata, never from
that projection. Complete U and complete FORCE for **all declared333nodes** are
required. The old49-node FORC inventory fails this reader contract. No automatic
physical execution, RF correction, scoring or comparison is exposed.

The next candidate needs the full333-node FORCE inventory, including all dependent
DOFs, to recover multipliers and inspect free residuals independently. Root-only
RF cannot determine omitted equation actions. Root must retain exact deck, binary,
version, byte outputs, provenance, source/installed bindings and supervised resource
receipts for any future run. **Fresh explicit physical authority is required**;
neither this tooling nor remaining240s accounting authorizes another solve.

Prepared source controls cover coupled pivots, loaded pivots, signs, offset moments,
free residuals, complete-force inventory, refusals, detached mutation, provenance,
overflow, exact output-only changes and strict saved-output inventory. The author
ran no checks. Root subsequently verified47 nonphysical controls at da690490:
all PASS, no failures/errors/skips,11.6249994 process-wall seconds, peak sampled
RSS197730304 bytes. Two effective runtime records and11 frozen inputs checked;
812 loaded files independently rehashed. CPU0/thread1/JIT off. Shared allowance
now57.3187615/240s used,182.6812385s remaining; controls20.7585858/30s used.
Raw root-audit-result-v1.json and audit-controls-v1 remain beside earlier failed
physical evidence. No installed rebuild or physical rerun was performed. Actual
CCX force recovery and runtime semantics remain unverified. Root owns independent
semantics adjudication and any next exact-output execution decision. Scientific
tolerances and full E03/GE/convergence requirements remain unchanged and OPEN.
