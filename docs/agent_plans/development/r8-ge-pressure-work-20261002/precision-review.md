# Experimental shell-fit precision review

Independent read-only reviewer: /root/pressure_precision_review (OpenAI; no
different-family qualification claim). Reviewer did not implement the patch.

Initial finding: reconstructing only the largest quaternion column while retaining
old lower eigenvectors makes the derivative inverse inconsistent with the refined
quaternion. Root replaced that inverse by a bordered solve on the refined
quaternion's tangent space, using its Rayleigh eigenvalue. Legacy current-coordinate
path is unchanged; only explicit displacement-based stable translation changes.

Final source review: no source-level blocker for the experimental candidate.
Focused 26-pass log inspected. Required counterexamples covered include analytic
signed tiny rotations, normalized first/second derivatives, finite differences,
largest-component changes, repeated lower eigenvalues and the existing top-gap
rejection. The residual check at zero deformation is limited: it does not establish
accuracy for deformed near-collinear cases. No arbitrary production residual cutoff
was added; further near-gap accuracy evidence remains an obligation before broader
qualification. No physical acceptance thresholds or element equations changed.

The initial candidate test run retained six failures: three real pressure lifecycle
failures and three new-test numerical comparison issues. Two tests used an absolute
zero-component floor of 1e-28 for a 1e-7 rotation, below attainable covariance
roundoff; the revised bound is 32*eps*angle. The derivative test compared individual
near-zero Hessian entries; the revised test uses the existing normalized directional
criterion 1e-6 across three difference steps. Neither revision relaxes physical
acceptance. Raw initial failures and test-source snapshot are preserved.

The pressure workflow remains unaccepted. These reviews do not qualify installed
artifacts, complete load support, G4A or the full programme.
