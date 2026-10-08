# Accepted-state GE/Q4 six-pose-point buckling development

This experimental route captures an existing accepted finite equilibrium. It
keeps every shell coordinate, native nodal pose, two half-cell rotations and
eighteen resultants per member, plus every point multiplier. It neither uses
mass nor eliminates resultants, assumes SPD material stiffness, introduces
penalties, averages tangents or changes the static solve. Full G4B acceptance,
external agreement, completeness and nonlinear critical-load claims stay open.

The public API is `owner.buckling(GEPointBucklingRequest(expected_generation,
count=3, shift=1., bounds=(0.,1e12), max_iterations=600))`; types are exported
from `anysolver.stiffened_shell`. `point_buckling_capabilities` reports structural
definition/state admission separately from material capture validation. A
positive material eligibility claim is not made before the elastic-interior,
unchanged-history and yield-margin witnesses have been checked by local replay.

Admission currently requires the explicit objective Q4 pullback, flat elastic
Q4 sections, generalized retained GE members, supported six-pose points and
nodal dead translation forces. Shell or beam rotational supports must be full
triples; simple translation supports retain their declared provenance.
Historical corotational Q4, active plasticity/yield boundaries, physical fibre
sections, S3, external/staged loads, lines and footprints require separate
future contracts. These restrictions describe this operation, not permanent
programme exclusions. Virgin reference modes retain their existing API/schema.

The potential is shell energy plus `p^T k(a)-V*(p)` for each GE member,
`mu^T c(a)` for each point and negative dead-load work. The raw beam operator
supplies the full42 Hessian including `hessian_low`. Its material block is
`[[0,B^T],[B,-S]]`; its geometric block contains `sum(p_i Hess(k_i))` in the
24-kinematic-coordinate block. Material stiffness is consequently indefinite.

The Q4 local production kernel supplies material/stress-Hessian components.
With actual objective deformation map d, its material block is `D^T km D`;
its geometric block is `D^T kg D + sum(f_i Hess(d_i))`. The qualified linear
correction stays in km, and its corrected force participates in map curvature.
These are coordinate-covector Hessians, not spatial-row Newton tangents.

If P maps actual coordinate variations to spatial variations, `g=P^T r` and
`H=P^T J + (dP)^T r`. Shell rotations use their actual additive chart and
anchors. Native nodal/cell rotations use zero-centred left Exp updates. Point
`evaluate_ports(True,False)` includes the shell chart derivative but needs the
beam block `+0.5 skew(r_beam_rotation)` to complete its covector Hessian.
Nonzero accepted point multipliers contribute the actual constraint curvature.
No numerical symmetry repair is applied.

The sparse augmented pencil is `[[Km+lambda*G,C^T],[C,0]]`, where
`G=Gbeam+Gshell+sum(mu Hc)-Hexternal`. Translation dead loads have zero external
Hessian in this admission. The complete split must reconstruct the accepted
conservative KKT Hessian at lambda=1 before and after support restriction.
Lambda scales frozen accepted prestress at fixed configuration. It is not the
nonlinear equilibrium load parameter, lowest instability or a limit load.

The solve uses sparse coordinate congruence, general shift factorization and
Arnoldi inverse action, with all mixed variables retained. Requested positive
finite pairs nearest the shift are checked against the original unsymmetrized
pencil and actual point constraints using the existing congruence-scaled
backward-error measure and 1e-8 threshold. Singular/infinite, complex or
unresolved selected pairs give explicit failure. Pairs outside the requested
positive window are not reclassified as instabilities. No completeness is
claimed. Factor failures and cancellation return typed results without modes;
invalid/stale admission or mutation raises before publication.

Accepted arrays and sparse storage use immutable backing bytes. Material
predecessors are private immutable pickle bytes created from owned in-process
state; there is no external pickle-input route. Capture replays copies and
does not update accepted states or recovery caches. Cancellation/generation
checks inside local loops and Arnoldi are constant-time; full state, operator
and pencil integrity witnesses run at operation boundaries. Checkpoint bytes
must remain identical. The exposed full coordinates are coordinate variations.
`shell_coordinate_modes` retain additive angular variations;
`shell_spatial_modes` apply the actual accepted P. Native beam/cell angular
variations are spatial zero-Exp variations. Coordinate support reactions and
physical support wrenches are separately labeled; the latter use inverse
transpose of the actual shell chart. Resultant and multiplier modes remain
available with complete support provenance.

The new focused tests use at least two Q4 cells, two GE members and eccentric
six-pose points with nonzero accepted multiplier curvature. A bounded dense
full-mixed oracle independently scatters local Q4/GE potential derivatives and
direct point Jet2 derivatives in the actual mixed charts. It is capped at 256
coordinates and never used by production. A three-step fixed central-difference
plateau `(3e-6,1e-6,3e-7)` checks the actual `_advance` covector derivative from
one frozen accepted parent at the unchanged 1e-6 derivative criterion. Further
tests cover stress-sign changes, dense finite-factor agreement, immutable
ownership, stale generation, historical-policy/partial-support rejection,
infinite pairs, factor failure and cancellation.

`scripts/r8_ge_point_buckling_dev.py --output <fresh-directory> --case compression`
prepares one bounded connected development case; tension is a separate optional
case, not an automatically launched sweep. The runner records actual runtime,
imports, effective threadpools/JIT setting, checkpoint identity, sparse blocks,
mode recovery and failure status. Execution requires the orchestrator's single
600-second/2-GiB/one-affinity/one-pool/JIT-disabled supervisor. No protected
canary, F03 or qualification campaign is invoked. The implementation owner has
performed AST inspection only. Root's supervised initial evidence is preserved
under `.qualification/b3-ge-e4-pl/r8-ge-point-buckling-dev-20261005-v1`:
source checks passed 41 tests, installed checks passed 18 tests, and the installed
compression example completed. The independent Read review identified no blocking
correctness defect. These are development results for this experimental admitted
route; they do not establish qualification, a lowest instability, mode completeness
or closure of the full G4B programme. Additional focused tests now cover direct
unchanged-history/plastic/yield-margin admission, cancellation between inverse
actions, ARPACK nonconvergence, backend solve failure and model-provenance mutation.
Fresh versioned source-v2 and installed-v2 checks passed 18 tests each (4.60 s
and 4.50 s); the product bytes and installed wheel are unchanged. Initial v1
evidence is preserved. A test of the private history-admission predicate isolates
its rejection logic; it is not a new physical material qualification.
