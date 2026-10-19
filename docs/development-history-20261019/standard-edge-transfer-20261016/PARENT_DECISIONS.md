# Adopted contract decisions (parent/OpenAI)

Source survey exposes a compatibility boundary: tests/test_constraint_audit.py::
test_valid_eccentric_beam_shell_coupling_is_feasible uses masters x=0,1,2,3,
beam x=4 and r=(0,0,0.2), with uniform weights. It is an intentionally valid
algebraic constraint fixture even though xb != sum(Ni xi)+r. Existing explicit
one-to-one eccentricity also is an override, not forced to coordinate difference.
Therefore DO NOT add universal coordinate/offset consistency rejection in these
public classes. Check physically matched records in production/manufactured
geometry tests; document that explicit offsets define the algebraic attachment.
ANYmesher continues to own physical projection and its tolerance. This resolves
Fable's source-dependent geometry hypothesis without changing valid API inputs.

Partition of unity: no configurable weight tolerance exists on the element.
Use dimensionless coefficient tolerance already in the solver only if it matches
existing standard generated records and stated semantics; do not borrow a length
tolerance for dimensionless sums. If no established relevant tolerance exists,
report the specific issue for parent adoption; shape/count/finite/ref checks
proceed independently. Preserve array alias and caller updates.

Resume adoption: use absolute dimensionless partition-of-unity tolerance 1e-10
(rtol=0), matching the existing constraint residual scale. This is a prospective
input-admission threshold, not a changed scientific acceptance threshold. Existing
shape records are surveyed/generated baseline cases and must remain admitted.
Do not renormalize. Finite sums must satisfy |sum(Ni)-1|<=1e-10. Revalidate mutable
inputs during emission so later corruption cannot silently bypass admission.
