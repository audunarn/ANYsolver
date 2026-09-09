# Four actual elastic spatial arch equilibria — diagnostic closeout

Source e43947c2337901ea50029586be17d0eefc85a56d, tree
3ed1b7c565a5ba8cb3101f4f7235f1d5d245dffe. Three research-only implementation
paths; no src mechanical/state/recovery/solver changes, aliases or defaults.

Disposition: PRIVATE_SPATIAL_ELASTIC_EQUILIBRIA_DIAGNOSTIC_ONLY.
Full goal ACTIVE; independent review PENDING, production_qualified=false.

## Concrete result

The unchanged20-macro clamped arch now has four resolved out-of-plane elastic
equilibria under a purely vertical crown force. These are full retained
nonlinear solves, not eigenvectors presented as equilibria. Prescribe lateral
translation at left-quarter node11, solve the vertical load factor and every
free equilibrium/compatibility equation, and recover160 stations per result.

| Absolute lateral control | Vertical load | Maximum absolute lateral displacement |
| --- | --- | --- |
| 0.003 | 0.02785612563003568 | 0.005915717179670111 |
| 0.006 | 0.027475446424564978 | 0.011831415568101664 |

Both signs produce each row. Small-amplitude equilibrium/compatibility metrics
are at most1.7562e-14 with correction7.6237e-13. Large-amplitude metrics are at
most1.2063e-13 with correction5.2067e-12. Maximum force/moment balance defect
4.588e-16. All satisfy the unchanged1e-11 bounds. Every trial retained virgin
elastic histories; no lateral force, stabilization or threshold adjustment.

## Reflection and limitations

A separate standard-library postprocessor checks polar position reflection
S=diag(1,1,-1), proper nodal/station frame mapping S*Q*D with D=diag(1,-1,1),
cell rotation mapping S*R*S, and local work-conjugate strain/resultant mapping
diag(1,-1,1,-1,1,-1). It imports no solver or mechanics. At each amplitude,
positive/negative loads, positions, nodal/cell/station frames and all station
strains/resultants have zero reported difference after the transforms.

This same-author reflection audit is NOT independent source-equation operator
reconstruction, branch uniqueness/stability proof or continuum error evidence.
It is stronger than a zero in-plane residual alone but cannot establish a
physical loading path from the undeformed state. Four separate elastic
equilibrium initializations are not an authenticated continuation history.
No initializer result is accepted by a restart owner; no accepted state issued.

## Source and preserved failure

Every worker independently authenticated and replayed the original four-record
N20 onset checkpoint432367bytes, SHA256
f45e617c272aba490db5cd1ef93fc543462aaf5c104557cbd1c47defebe76d45.
It used only its elastic mechanical fields as a numerical guess. The completed
onset programme was not rerun as a new scientific campaign or reclassified.

Original9f467e7 smoke failed before spatial Newton: the ordinary control
owner's virgin genesis border is singular for lateral displacement driven by
vertical force.35.6724seconds,172105728bytes peak, empty Job tree. No spatial
output exists for that failed smoke. Source and complete stderr are preserved.
Successor uses a distinct guarded trial-only wrapper, without genesis/stage/
checkpoint/restore methods. A regression confirms the original history owner's
singular-border rejection is unchanged. It is not bypassed for accepted states.

## Separate inventories and runtime

Initial admission suite13passed; its shared pytest temp-link cleanup emitted a
permission warning, recorded without deleting that historical directory.
Successor admission/history-boundary suite17passed in2.64seconds, fresh basetemp.
Reflection suite2passed in0.070seconds, including10 mutation subcases for load,
geometry, frames, strains, resultants, history, coverage and amplitude.

Successful positive-small smoke54.0437seconds,peak177106944bytes.
Three remaining signed/amplitude workers overlapped, each55.48..55.77seconds,
maximum176697344bytes. All exited0 with empty child trees. Limits600seconds,
24GiB, one numerical thread, max3workers,1800seconds/wave and existing120second
context/CPU-inactivity safeguards retained. No automatic retries. No formal
two-cycle qualification wave was run or claimed for these diagnostics.

## Preservation and next gate

External archive:
C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-spatial-equilibrium-e43947c-20260909

42 entries reverified by bytes/SHA256; all original runs retained.
Manifest6140bytes SHA256
ed4f312a75fd6f91e6e7ead0634235a376950aa750ba76bd8cfcfc36ec462d9c.
Audit2194bytes SHA256
56e7beeb57f4b274f9d9cffddb861bb2b89c6b8dbef800b0f6bea102b9647166.
Reflection2292bytes SHA256
08dc919fe4b32a9f9f40fb7f677a6b3433202384474eda925ab0ba5d9e217565.
Canonical status: docs/reference_cases/ge_beam3_spatial_equilibrium_status.json.

Next obtain independent spatial source-equation/refinement comparisons and a
properly authenticated elastic-seed-to-continuation handoff. Keep the initializer
separate from plastic history. Then trace spatial branches and test supported
restart/cancellation and their physical work. No need to repeat the completed
onset or native-analysis campaigns. Remaining full qualification includes wider
solver/material/dynamic parity, reviewed installed explicit selection and
objective eccentric/curved beam-shell connections. Main and the user's ANYmesher
work remain untouched. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED; no publication.
