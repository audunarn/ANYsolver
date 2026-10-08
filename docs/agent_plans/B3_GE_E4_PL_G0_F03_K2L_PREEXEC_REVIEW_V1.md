# Independent F03-K2L preexecution review

21 September 2026. Read-only independent mechanics and evidence-grammar
review of the K2L design, probe, runner and supervisor. The reviewer did
not modify source or execute a registered diagnostic.

The first review identified five preexecution issues: the whitened map
was dimensional, near-cutoff singular vectors were treated as exact native
null modes, the promised reconstruction metric was missing, nonfinite or
degenerate results could bypass typed disposition, and the candidate
grammar had no supervisor. The first correction explicitly divides the
mass-whitened work-scaled map by `u*√L0`, records a common relative cutoff,
separates native physical/retained images, uses a cutoff uncertainty band,
and records projection/orthogonality/reconstruction diagnostics. It also
adds typed mass/reference/assembly outcomes and an external supervisor.

A subsequent review found that the supervisor did not verify the reported
cutoff against the full singular spectrum, while nonfinite reference and
mass metrics could reach JSON serialization. The final correction
recomputes `τ=1e-10 σmax(A)` independently, validates ordered spectra and
rank ranges, and checks finiteness before serializing invalid candidate
records. A deliberate mutated-cutoff smoke is rejected. Q4 coarse/fine
and S3 sample meshes pass the JSON/grammar smoke. The design explicitly
leaves a fully transformed metre/millimetre invariance case outstanding;
K2L makes no quantitative stability claim.

The reviewer found no remaining source-visible P1/P2 blocker for the
**bounded load-independent 26-mesh/78-candidate rank diagnostic**. This
review does not endorse the algebraic shell-restriction count as a locking
proof, uniform inf-sup result, six-channel attachment, or F03/G0B
acceptance. Freeze this review and all source/dependency/evidence
identities with the clean commit before a one-shot run. Independently
adjudicate the immutable output and physical interpretation afterward.
