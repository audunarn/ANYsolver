# Opt-in external solid blocks — development candidate

`anysolver.SolidModel` explicitly wraps an optional native `FEModel`. Native
node numbering and element kernels are unchanged. Use `SolidModel()` for
all-solid models, or `SolidModel(native_model)` for native and external blocks.
It is intentionally not a FEModel subclass: unsupported native workflows must
not silently ignore solid regions.

The optional dependency extra is `ANYsolver[solids]`, referring to
`ANYsolid[skfem]`. These local candidates have not been published. Native
shell/beam installation adds no ANYsolid or scikit-fem dependency by default.

Register a region with `model.add_region(name, mesh, material, order=2)` or an
explicit prepared backend. `region.prescribe(group, values, components)` and
`prescribe_dofs` declare fixed coefficient values. `region.set_load(case, rhs)`
stores a copied force vector; named load cases are then passed to
`model.solve_static(cases, native_load_cases=...)`. Repeated names are permitted
only when their positional native-load semantics agree. `solve_linear` and
`solve_linear_many` dispatch the explicit wrapper to this path.

The result owns separate native/region slices, multiplier coefficients,
support reactions, interface forces and diagnostics. Backend coefficients are
not interchangeable with native six-DOF node vectors. Recover solid tensors
through `region.prepared.recover(result.region_coefficients(name)[:, case])`.
See ANYsolid/examples/host_all_solid.py for a controlled all-solid example.

The current direct constrained path uses the existing SuperLU factorization
handle and cache. Uncoupled real solid regions must have supports removing all
physical component rigid modes. Free-free solid solves and direct solid-solid
connections are not enabled. Nonlinear, modal and transient entry points refuse
the wrapper before native-model observation.

`ShellEdgeTrace` admits exact production E4-PL Q4 and small-linear S3 V2D on an ordered,
straight, planar edge chain. `anysolid.coupling.build_weak_connector` constructs
an unqualified weak five-section-mode candidate with explicit multiplier
breakpoints. Its use requires `research_coupling=True`; this is an experiment
opt-in, not an acceptance waiver. Production coupling is NO_GO. Native geometry,
director, thickness and DOF map changes require rebuilding the trace/operator.

The approved registered policy is selected by supplying a case-name mapping of
ResidualScales(length, force, displacement, interface_displacements=...) to
SolidModel or solve_static. References must be positive, finite, immutable and
chosen prospectively from physical inputs/reference solutions. Both local and
normwise checks retain 1e-9 thresholds. Native rotations use the registered
length scale; the policy refuses general multi-master reductions whose columns
do not have disjoint supports. Missing references retain the explicit legacy
path; invalid or inapplicable registered references do not silently fall back.
Legacy componentwise diagnostics and failed evidence remain visible.

The original coarse transverse case remains failed (72.19% versus 5%).
Subsequent registered axial-refined cases meet the same target (4.56% at Nx16,
1.41% at Nx32) with unchanged operators and tolerances. These are controlled
benchmark profiles, not universal mesh counts or arbitrary-mesh accuracy.
Current limitations include unqualified uniform stability and wider convergence,
physical nonzero-offset section consistency, S3, coupled multi-region and
engineering scaling. Consult ANYsolid/docs/WORKFLOW_1_HANDOFF.md. Full repository
CI and clean installed-host release qualification remain unexecuted.

The subsequent finite stability study completed all 18 operators and independent
references but failed the thin 16:16 modal amplification allocation
(5,645,155.4093 versus 5,000,000). Production remains NO_GO; see sibling ANYsolid
`docs/FINITE_STABILITY_RESULTS.md`. Four signed-reference-offset fixtures and
the scoped S3/multi-region physical cases pass; broader qualification remains
gated. Explicit strong controls use `add_interface(...,
diagnostic_strong_tying=True)` as well as research mode. Weak integrated and
strong point constraints cannot be mixed in one model; strong results are
marked `diagnostic_only_strong_tying`.

## Focused development checks

Latest continuation: the repaired connected beam patch passed two certificates
and both physical load cases. The adapter owner passed eight local Windows/
Ubuntu Python 3.11–3.14 snapshot cells. These results do not close the failed
transition reference convergence gate or required native NLG-007 verification
case. The warped-plastic-Q4 guard and required-case status remain unchanged.
See sibling ANYsolid `docs/WORKFLOW_1_HANDOFF.md` and `docs/PLATFORM_RESULTS.md`.

The separate Candidate B multiplier study subsequently passed all 18 registered
operator assessments and 12 fresh physical cases without changing any limit.
Candidate A remains failed. See sibling ANYsolid
`docs/REVISED_MULTIPLIER_RESULTS.md` for the finite accepted scope and remaining
Workflow 1 gates; production coupling remains NO_GO.

From the ANYsolver checkout, with the solid/backend test dependencies installed:

```console
python ../ANYsolid/tools/dev_checks.py host
python ../ANYsolid/tools/dev_checks.py coupling
python ../ANYsolid/tools/dev_checks.py full
```

These bounded source profiles record counts, identities and effective runtime
settings. `full` covers the ANYsolid suite and the registered solid integration modules;
it does not replace ANYsolver's portable regression CI or registered scientific
qualification. See the sibling ANYsolid `docs/DEVELOPMENT_TESTING.md` for the
impact table, timeout/JIT options and retained evidence paths.
