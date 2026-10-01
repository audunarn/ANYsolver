# Non-follower shared-hotspot gate

This successor gate addresses the remaining representative-suite shortfall after
the follower-validation candidate passed mechanics and case-level regression
guards but delivered only a 1.41% representative median improvement.

The diagnostic stage profiles the installed `b67517d1` wheel on the four frozen
non-follower cases. It uses the existing representative builder and profile
runner, one unprofiled warm solve and one profile per case, serial execution,
and one numerical thread. Profile time is diagnostic and cannot be substituted
for the formal paired timing evidence.

An implementation candidate is eligible only when the registered shared-path
rule is satisfied and the proposed change preserves equations, tolerances,
defaults, physical evaluation counts, and state-lifetime guards. A three-pair
installed-wheel screen may advance a candidate, but promotion still requires
the existing seven-pair representative gate: 10% median improvement, no case
worse than 5%, and complete physical equivalence.

The exact inventory, identities, limits, selection rule, screen rule, and
terminal outcomes are registered in
`docs/reference_cases/nonlinear_static_nonfollower_profile_gate.json`.
