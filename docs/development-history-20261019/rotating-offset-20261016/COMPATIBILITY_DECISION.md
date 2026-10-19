# Rotating-offset attachment: compatibility decision

Date:2026-10-16. State: INSPECTION ONLY — STOPPED AT COMPATIBILITY GATE.
No rotating_offset_v1 API, attachment implementation or numerical execution.

## Decision and its limits

OpenAI does not adopt the conditional force interpretation required to proceed.
The approved plan requires the work pairing to be established before either
implementation or numerical checks. It preserves the1e-10 attachment/work
criteria and forbids widening this into a rotation-convention research campaign.
The source review establishes derivative consistency of an existing rotated
force residual. It does not establish exact finite-rotation work conjugacy of
the local deformational moment and the spatial moment inferred from that residual.
There is no adopted local-rotation bound or error allowance closing that gap.
The30degree bound concerns total attachment rotation; it does not bound this
separate local-deformation approximation.

This is an unmet compatibility prerequisite, not a numerical failure, a proof
that the proposed kinematic map is impossible, or a new finding of failure in
the previously tested small-rotation standard connection. No supported-use or
accuracy claim is changed. Existing source remains untouched.

## Source-backed distinction

Actual production dispatch is nonlinear_static.py:1507-1525 to
corotational.corotational_element_response. It is not the direct beam helper
in elements.py:4427. The generic wrapper uses local rotational coordinates
phi=Log(R_rig.T Exp(theta)) (corotational.py:238-285), evaluates the existing
element response, then rotates every force/moment block by R_rig
(corotational.py:373-405; corotational_performance.py:23-32,94-105).
Its consistent tangent differentiates THAT residual with respect to additive
rotation-vector coordinates (corotational.py:583-644). A derivative can be
consistent without its underlying residual being an energy gradient.

For a fixed extracted shell frame and local moment m conjugate to delta phi,
the exact spatial torque would be

    t = R_rig J_left(phi)^(-T) m
      = R_node J_right(phi)^(-T) m.

The implemented rotated moment is R_rig m. Their leading difference is
R_rig (phi cross m)/2, generally nonzero. This statement is an analytical
pairing distinction, not a measured whole-element accuracy estimate. It does
not by itself provide a complete replacement force/tangent: the frame also
depends on translations and a broader correction must account for that.

A profile-local transformation p=A(theta).T s, where A rotation blocks are
R_node J_right(theta), is an exact conversion IF s is adopted as the spatial
resultant. Then nonlinear elimination could use

    r = J.T p
    K = J.T Kp J + sum_a p[a] Hessian(g[a]),
    Kp = A.T Ks + derivative(A.T) applied to s.

That conditional algebra does not prove that the present local-moment output
has the exact spatial-work meaning the new claim requires. Merely multiplying
by A.T or rotating the offset is not an adjudication of that physical contract.
The existing finite-contact selector guards and retired sources are unchanged.

## Independent review and disagreement

Mistral inspected the actual wrapper, local rotation map, block rotation,
consistent tangent and affine solver projection with successful tools. Its
finish report recommends UNRESOLVED / conditional PASS and explicitly says
STOP is not established as a mathematical necessity. It proposes accepting
the inherited first-order local-moment approximation and later numerical
pairing checks. The full report is MISTRAL_FINISH_REPORT.md; its uncertainties
and recommendation remain preserved verbatim.

OpenAI agrees with the candidate transformation and the analytical distinction,
but does not adopt that extra approximation under this gate. Later numerical
checks cannot be used to bypass the user's prerequisite that the physical
pairing be resolved before numerical execution. Accordingly this bounded task
stops for an unresolved contract, not because the adapter was disproved.
There is no claim of reviewer consensus on feasibility or rejection.

Exact pairing would require a separately scoped decision on the corotational
force-output contract; approximate pairing would require an explicit physical
domain and error allowance. Neither change is adopted in this slice. No new
programme or further execution is launched automatically.

## Execution and availability

The first Mistral launch failed before inference because sandbox access to
its normal Vibe log was denied. The same authorized Read assignment ran with
normal log access. Its18turn inspection ended without a final recommendation;
a10turn bounded continuation completed the report. These are one source-gate
investigation and its handoff continuation, not implementation/repair attempts.
Useful source inspections prove worker availability. The initial report file
is explicitly marked incomplete; launcher exit0 alone is not treated as a gate.
READ process-wall time was not instrumented, so no precise worker-wall claim
is made. Numerical check budget consumed:0/1200seconds; all numerical
acceptance cases UNRUN because the prerequisite was not adopted. No check
budget is renewed or carried forward as an automatic future allowance.

Full raw worker logs, prompts, parent derivation, initial source hashes and
baseline dirty-file hashes remain in this directory. A receipt records final
preservation and changed paths. No commits, pushes, branch changes or owned
activity remain after closeout.
