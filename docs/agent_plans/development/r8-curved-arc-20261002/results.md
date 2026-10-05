# Curved elastic point arc lifecycle

2 October 2026, base3937f8eb plus this commit. IMPLEMENTED_NOT_QUALIFIED.

The existing physical tangent-plane controller now admits the explicit curved
elastic Q4/full-pose-point route. Its distinct mechanical checkpoint kind and
policy omit shell plastic arrays. Existing coupled-material arc identities and
fields remain unchanged. The same atomic predecessor checks, cancellation,
physical path condition and endpoint replay apply. Generalized beam histories
must remain elastic; no artificial J2 material or BL5 substitution is used.

The bounded curved control completes cancel-after-first-step, fresh restore and
continued stepping with byte-identical checkpoints. Its final endpoint agrees
with a separate force-control solve (displacements rtol1e-7/atol1e-11,
resultants rtol1e-7/atol1e-8). Equilibrium and compatibility retain 1e-8/1e-9.
Correctly framed nonelastic beam history is rejected without committing state;
positive accepted plastic histories are zero. Wrong arc policy is rejected.

Source v1:1passed; v2:13passed including material arc regression. Installed final:
**22passed in48.75s**, 50.77s supervised,188157952bytes peak process tree.
Limits600s/1GiB; runtime verified1thread/JIToff and actual installed imports.
All412modules match wheel/site/source. Wheel SHA256:
`6086fd4edb4246ab77a2c67fb898965e4e71d8020d4c0494b59bbbcb5dbe70b0`.
`checks-v1.zip` retains runner, artifacts, tests, logs and whitelisted execution
metadata. Installed scope includes the changed route, material arc and
displacement-checkpoint regression. No performance gain is claimed.

Independent read review found no consequential regression and requested explicit
zero-history/nonelastic-restore assertions, included in the installed run.
This review is not independent scientific qualification.

No E04 roof solve, external comparison, first limit point, descending branch,
mesh-independent path or aggregate acceptance is implied. The earlier tiny-load
curved force-control failure remains open. Next implement the actual E04 owner
construction and bounded seed/continuation screen, then define a physically
matched external connection and bracket before capacity qualification.
