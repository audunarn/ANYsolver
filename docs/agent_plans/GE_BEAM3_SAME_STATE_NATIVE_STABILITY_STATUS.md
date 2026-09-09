# Native and continuum instability signs agree at continued endpoints

Frozen implementation a4a723010155e25bc511d483d081cee64d377d42,
tree c2f61725bfa1c42d2e9705a9afb9f25619ce3c38. Three research-only paths;
no changes to native mechanics, sections, recovery, state laws, defaults or versions.
Targeted suite: 23 tests passed in 7.26 seconds (12 new capture/binding tests and
11 existing scaled-inertia tests). Includes an actual precise-policy small-model
endpoint capture versus full stationary Schur complement. Diff check passed.

## Scientific outcome

Each accepted precise-policy N24 checkpoint at prescribed +/-0.0065 was restored
by its actual owner without advancing or changing history. The original one-target
programme, source seed, checkpoint bytes, and model policy remained bound.
All 438 kinematic/internal coordinates and 432 stationary resultant coordinates
were captured. Only 12 physical end clamps were removed: 426 free coordinates,
including numerical control DOF74. No auxiliary continuation row or load column
was included in physical stiffness.

Both signs have native inertia (425 positive, 1 negative, no unresolved pivot)
at zero spectral shift. This result agrees at 80 and 100 decimal digits, with
identical pivot indices and sizes. Both precision replicas are byte-identical;
both actual capture replicas are byte-identical. There are 285 positive-mass
coordinates and 141 massless nodal-rotation coordinates; the algebraic stiffness
and physical mass positivity checks passed. No negative algebraic modes were
discarded. Positive diagonal congruence preserves quadratic work; no factor
entries or pivots were dropped or modified.

For positive/80, the full-matrix reconstruction bound is
5.1669806550667889533401738832460549453403678272909605211767925448566669234881851e-80,
well below 1e-60; maximum front12,13009 updates. Raw geometric skew normalized
1.4733889534452279118679389364457352743173931587041450087668386910672209785768590e-19
passed the 1e-11 guard. Exact raw symmetry is not claimed: the symmetric energy
representation uses (H+H^T)/2, preserving x^T H x.

The separately preserved full-spatial continuum trial also has negative work at
each corresponding +/-0.0065 endpoint. "Same state" here means the same prescribed
displacement endpoint and case, not byte-identical discrete/continuum fields:
native load0.027309374581706167 differs from continuum load~0.02713556026763412,
within the earlier accepted engineering comparison. The sign comparison does not
establish equal continuum Morse index, eigenvalues, mode shapes, stable postbuckling
or a physical loading path from rest. In particular, the continuum trial Gram is
not physical mass and its Ritz values cannot be used as frequencies.

## Process outcome and administrative correction

All twelve scientific workers succeeded, exited zero and left empty Windows Job
trees. Capture times: positive smoke66.105s; positive replica73.447s; negative
73.849s; negative replica73.548s. Eight audit processes each took3.326-3.427s.
Worker wave elapsed150.077s, peak569765888bytes, maximum3concurrent. One numerical
thread each; original owner120s, child600s/24GiB and wave1800s bounds retained.
No workers were retried, no checkpoints advanced and no historical runs repeated.

The original external coordinator FAILED after all workers completed. Its final
comparison accessed nonexistent result key `permutation`; the frozen audit returns
`pivot_indices`. Original run.py, raw outputs and KeyError transcript are preserved;
the original complete.json remains absent. This was not a scientific worker failure.

A separate standard-library saved-output reader corrected only that field lookup,
verified all twelve receipts and bounds, original frozen source, exact input/output
bindings, replica bytes, precision agreement and full426pivot partition. Its test
used an actual426dimensional audit result and five mutations. Reader SHA-256
5c7cdbea656c0617446b051b8d7ce01cdfb5892743e17e25c24026a1388f4169.
It wrote a new exclusive administrative adjudication, explicitly recording that
the original coordinator failed and workers were not rerun. This correction did
not change the frozen worker, mechanics, audit arithmetic, protocol or evidence.
It is not independent author review of the mechanical formulation.

## Preservation

External root:
C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-next-native-a4a7230-20260909.
70 manifest-bound files plus manifest; original TEMP and exclusive local staging
retained. Both archive copies verified by exact file extent, byte counts and hashes.
Manifest9200bytes SHA-256
4ac11c904afd59613a8e74056594de6bfd9172bd68c1c295ba2d2509e70c6a13.
Separate adjudication2486bytes SHA-256
d80b67e419f4de5b00d9a4182da5873f63f84a00aa79e63a485a0ae463777d2c.

Positive packet17015492bytes SHA-256
889aca7681298fdb426736fd5d5ab3ef009b84ac9347fb4f54741dabb30ff75b.
Negative packet17012913bytes SHA-256
ab91b219f750421bf5a90b85aec62e74cc97d541477e1a84b429f857c4d4bcf9.
Positive80 audit40442bytes SHA-256
dc17831f25809a375ac3e54e1422b44900afaf8768d264bcfefe71850bc35aac.
Positive100 audit49046bytes SHA-256
97647b0af71f82e258f9bd7c4eaa1d0730a47a1f043f1eaa243fc511abf0d05a.
Negative80 audit40443bytes SHA-256
7d43a542e0df47ae722e2da3c824a03766f0c7307299ec470f3879979338768c.
Negative100 audit49047bytes SHA-256
0514d223db7610641e9bd3371483961660ac290ae108a3456bfd21d67bf0a57b.

## Next and remaining work

Use these saved factors and complete continuum fields for a separately frozen
current-rest physical-mass spectral comparison. Derive matching spatial inertia
and eliminate only verified-positive algebraic trace stiffness; independently
verify eigenpair residuals and work. Do not compare L2-normalized trial values
with physical frequencies. Saved-factor processing should not require another
owner capture or nonlinear equilibrium solve.

The overall goal remains incomplete: broader geometric/slenderness and state/
material/solver parity, physical nonlinear loading paths, independent mechanical
review, installed explicit selection and objective eccentric/curved beam-shell
connections still require completion. No production activation, release or alias
change follows from this local instability-sign agreement.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
