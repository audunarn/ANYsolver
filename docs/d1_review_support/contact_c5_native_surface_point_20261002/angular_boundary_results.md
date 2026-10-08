# Angular endpoint transitions — development geometry, 2 October 2026

Base `4fcaeb1e`; owned working-tree identity in `angular_boundary_source.json`.
Complete raw portable-run records are in `angular_boundary_raw.zip`.
Question: represent the actual stationary branch entering/leaving a captured
increment over the saved local angular band, without discarding uncertain bands.
This is geometry development, not material-integral or engineering acceptance.

## Implementation

At a captured time, straight round geometry gives the exact trigonometric form
N(angle)=q0+qc*cos(angle)+qs*sin(angle). Coefficients are calculated directly from
the actual source/target work path, not fitted to samples. Each coefficient uses
the existing pre-cancellation N error allowance; the total function control is
three times that allowance plus arithmetic rounding. Sine/cosine extrema bound
endpoint N over a sub-band, replacing only an explicitly selected norm-only
endpoint enclosure. Legacy paths without that selection remain unchanged.

Analytic simple zeros receive outward guards. Throughout |Q|<=error, the computed
polynomial's derivative magnitude is bounded below by
sqrt(amplitude²-(|q0|+error)²). Mean-value bounds and angle rounding contain the
perturbed zeros. Possible tangencies/degeneracies retain the whole unresolved
band. Selection-endpoint guards clip to the domain and remain represented.
Regular and unresolved bands cover the angular selection exactly; overlapping
guards retain all owners. Regular here means endpoint-root-free, not a proof
of the entire temporal path or friction history.

With explicit `_variable_endpoint_branches=True` and a bound angular partition,
strict N' establishes at most one root at each angle even if endpoint N intervals
include zero. Keep one potential branch. A point query returns an ordinary root,
a clamped endpoint witness, or an uncertain-boundary witness. For the last, the
possible root time differs by at most (|N|+Nerror)/min|N'|. Integrating the N/B²
bound gives the axial displacement allowance; quotient errors remain included.
The open predicate includes both actual component endpoints and every potential
witness. Clamped H is continuous at branch entry/exit: interior H_t=0, and the
clamped time is constant outside; its angular envelope uses the same bound.

Review found a real strict-clamp selection error: rounded |N| values can reverse
their order despite reliable signs. Strict same-sign endpoints now choose the
boundary from certified N and N' signs. Only uncertain endpoints use the closest
computed magnitude, with displacement allowance. The initial source is preserved
in `angular_boundary_initial_source.zip`; the review counterexample is a test.

## Focused checks

Eight distinct new controls pass by affected-evidence reuse:

1. Independently derived rotating plane/circle boundary at angle3pi/2: complete
   regular/uncertain/regular coverage, no dropped material band.
2. Exact tangent, degeneracy, root-free case and both selection-endpoint roots.
3. Saved-path direct polynomial agrees with actual endpoint N within its error;
   both observed endpoint-root locations lie inside the guards (representation
   consistency, not independent native mechanics).
4. Near-tangent simple polynomial: all27 bounded coefficient perturbations have
   both exact trigonometric zeros inside the guards.
5. Saved regular bands have complete temporal covers with branch counts0,1,0.
6. Independently derived clamped motion: absent/uncertain/interior branch cases,
   time/axial intervals, whole-time open/closed predicate and strict-mode rejection.
7. All saved bands, including both guards, retain bounded potential extrema.
8. Reviewer bounded-noise counterexample selects the correct strict endpoint.

The final correction reran only its analytical clamp and new counterexample:
2passed. Earlier unaffected geometry evidence is retained; no blanket final-run
claim or scientific independence claim follows. Owned OpenAI read-only review
confirmed the correction resolves its finding. Lower-tier workers were already
unavailable; no new availability probe or other-chat communication occurred.

All runs use explicit portable `--development` selectors, JIT off,180s/953MiB.
Saved effective OpenBLAS pools are1 and runtime errors absent. All five runs exit0;
complete elapsed ranges5.324–8.295s, sampled process-tree peaks184639488–189140992B.

## Saved geometry result and next action

Same saved origin/two increments/maps/laws/local field as the preceding slice.
Local xi[.72,.80], angle[3.19,3.20]. Endpoint guards:

| Captured time, segment2 | Angular guard | Width (rad) |
|---|---|---|
| t=0 | [3.1989934391775665,3.198994014637791] | 5.754602e-7 |
| t=1 | [3.199043714115627,3.1990442890703235] | 5.749547e-7 |

All five bands have potential branch counts0,1,1,1,0. Guard-center witnesses are
labelled boundary_uncertain; the intervening witness is stationary. Complete
uniform cover/preparation plus midpoint queries uses77shared support intervals
out of128. This does not claim that every possible angular query was executed. No material
query, residual/tangent/work integration, coupled owner or split restart ran.
The full local integral remains unpassed; no saved failure is converted into a pass.

Next: retain captured-endpoint force/tangent through real point replay; derive
complete-history uncertainty-strip work accounting. Verify an analytical boundary-
ending mixed patch before another unchanged saved local integral. Do not apply
the open-endpoint zero-force/zero-storage enclosure to closed captured endpoints,
omit guards, relax tolerances/resources or retry the full owner prematurely.
