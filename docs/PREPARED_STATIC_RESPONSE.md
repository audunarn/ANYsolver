# Prepared source responses (M8 development candidate)

`prepare_static_response_evaluator(model, patterns, *, baseline_load_case=None,
**prepared_options)` owns the structural snapshot and private factor used by
`prepare_static_evaluator`. `patterns` is a plain dict in declared column order.
`PatternCase(case_id, coefficients, time=None, *, canonical_load_case=None)`
accepts a sparse named plain dict or dense plain list/tuple/real ndarray. Streams
may mix PatternCase and StaticCase. Source packets are owned at ingress; later
model/load mutation cannot alter the library. Existing recovery, envelope,
resource, cancellation, transactional publication and close contracts apply.

For physical stiffness K, constraint map T and prescribed offset u0, the baseline
solves T.T(F0-Ku0); homogeneous source columns solve T.T Fj using the same supported
or free-free augmented operator. The owner retains full F and reduced q/free-free
lambda columns and its factor. The baseline and prescribed offset are added once.
Algebraic source columns may be individually unbalanced; each physical requested
combination must pass the existing rigid-body compatibility policy. Every library
column and physical case retains actual backward-error certification at 1e-10.

**Detailed stress and all envelope cases use canonical direct solves and staged
per-case recovery.** Each canonical solve receives one contiguous RHS column,
independent of ingress/yield batch size. This preserves the established numerical
layout. Governing cases replay canonically without an unproved contender bound.
Displacement/reaction-only cases may reconstruct q/lambda from active columns;
reaction values and complete diagnostics always use actual Ku-F, preserving
fixed/slave/master separation and keeping augmented multipliers distinct.

Canonical source stress components were originally prepared and superposed, but
focused historical counterexamples reproduced principal-stress failures at the
unchanged 1e-12/1e-12 criterion despite algebraic backward errors near 1e-17.
The component-output library is therefore removed from the current candidate;
its failed source and evidence are preserved. No component-response speed or
qualification claim is made. A reviewed output-error bound would be needed to
restore that route. Canonical native local recovery recipes remain available.

When canonical_load_case is supplied, its original-time native assembled F is
authoritative for compatibility, certification and fallback. Any bitwise source
F discrepancy forces canonical solve/recovery. Without that packet,
F0+sum(coeff_j*Fj) defines the requested load. A failing reconstruction equation
certificate also falls back. No cheap residual or source-equivalence certificate
is claimed.

Diagnostics separate numeric library payload, Python metadata, canonical stress
cases, canonical envelope cases, reconstructed cases, direct cases and fallback
counts. compiled_detailed_responses and compiled_envelope_responses are false;
reaction_execution is actual_full_Ku_minus_F_diagnostics. Preparation, native
loads and all canonical replay costs belong to complete-workload measurements.
No benchmark or promotion claim accompanies this implementation.

The memory policy includes snapshot, retained factor, full-F/q library, owned
names/index containers and ndarray base chains, preparation workspaces and
bounded case packets. Aliases are deduplicated; numeric and metadata bytes are
reported separately. PatternCase labels are validated as plain strings and their
retained size is counted before copying case inputs. Close releases names/index
and numeric library storage. These are storage estimates, not process RSS.

Fixed coefficient-only streams retain bounded multi-case batching under a memory
cap. A large native packet encountered after smaller packets have entered an
unfinished block can fit alone but exceed that block's remaining allowance. The
unfinished block is then refused before copying the large packet; earlier
published blocks remain valid. Use batch_size=1 for such variable-size streams.
Flushing while holding a mutable provider record across yield would change
ownership semantics, and copying an over-budget pending packet would violate
resource policy. Neither behavior is introduced silently.

Cancellation token callbacks run outside owned native spans. Actual remaining
preparation boundaries revalidate response and native executable authority after
the callback; modified helper code is refused before private computation or
publication. No inactive component-preparation callback is retained.

## M16 opt-in certified library route

`prepare_static_response_evaluator(..., stress_execution="certified_library")`
reconstructs stress and envelope outputs from verified per-element affine output
columns instead of replaying a canonical solve and recovery per case. Source
agreement is term-scaled (1e-12), the state keeps the 1e-10 backward-error
certificate against the actual load, reactions stay actual Ku-F, and envelope
governors are labelled `certified_response_values`. The default
`stress_execution="canonical"` is the behaviour described above, unchanged.
Contract, criteria and assessment: `PREPARED_STATIC_M16_CERTIFIED_ROUTE.md`.
No performance claim accompanies this route yet.

## M17 opt-in vectorized route

`stress_execution="certified_vectorized"` evaluates every recovered element
from probed, verified affine maps with one batched product per schema group and
case, and folds whole-model envelopes into arrays. Same certificates, source
agreement and governor labelling as M16. See `PREPARED_STATIC_M17_VECTORIZED_ROUTE.md`.
