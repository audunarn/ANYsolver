# Independent read-only review — C1 F5 common weak work

**Reviewer:** `c1_preopen_evidence_review` (independent of the runner author)
**Reviewed source:** `16d8274a`, `scripts/b3_e4_f03_c1_factor5_common_weak_work.py`
**Reviewed evidence:** `.qualification/b3-ge-e4-pl/f03-c1-factor5-common-weak-work-dev-20260926-v1/result.json`

No calculation blocker was found. The recovered solid action is bar-on-plate
and the native `-Cᵀλ` action is load on the shell, so their signs agree.
The shell reference virtual field `(uy=.0675h, uz=yh, rx=h)` gives top-face
`uy=.05h`, matching the solid bottom face. The two linear x hats are
continuous at `.95 m` and are representable by both Q4 and Q20 traces.
Multiplying their action difference by `.05 m` gives the first x moment
about `.95 m`. Reviewed source/input hashes match, and the F5 recovered
wrench differs from independent printed supports by at most
`5.77e-5 N/Nm`. The pre-opened combined direction permits linear
superposition of the saved native Mx and Fz cases.

The reviewer identified one interpretation overstatement: small differences
in two common hats would not leave *only* one-sided B3 modes. Higher-order
continuous modes and shell director/shear work would also remain. The v2
diagnostic corrects that wording and adds the limitation; numerical outputs
are unchanged from v1. The reviewer also confirmed that the F4 shell-action
replay must remain unresolved because its reconstructed solid Fz differs
from printed support by `1.96 N`. Neither result selects P0/P1/dual or
closes G0B.
