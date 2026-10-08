# G0 F07 native physical descriptor development slice

**Decision and boundary.** The prior F07 four-coordinate descriptor identity did
not establish that actual native beam and E4 shell mass can coexist with
massless retained and joint-multiplier coordinates. The bounded discriminator
is one straight, supported Q4 shell plus one native B3 member at an unloaded
conservative current-rest state. This is development evidence only; it does not
select an interface or change G0B/G1 admission.

**Competing outcomes.** If the coupled mass carries the known rigid translation
work and leaves algebraic rows exactly massless, a physical descriptor design is
feasible for this case. If either fails, the mass assembly or coordinate lift
needs correction before any modal qualification. The test uses the existing
native coupled owner and mass assembly without altering its operators.

**Executed check.** `tests/test_b3_e4_g0_f07_native_physical_descriptor.py`
constructs the owner, captures its physical mass and exact joint tangent, then
checks an independent rigid translation energy. Unit shell area, thickness
0.2, density 2 give mass 0.4; beam length 2 and translational sectional mass
2 per length give mass 4.0. It verifies positive mass for the six physical
cell coordinates and exact zero kinetic-factor columns for six algebraic
retained coordinates. The six multiplier mass rows are also exactly zero.
An independent generalized QZ calculation on the full constrained descriptor
has 24 finite and 18 infinite roots; its lowest three agree with the native
factor modes within `rtol=1e-10, atol=1e-10`.

**Result.** Direct invocation of the test function passed after the final
assertions, with `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, and
`MKL_NUM_THREADS=1`. The captured mass work was 4.4; the full mass matrix was
48 by 48, the joint constraint rank was six, and the reduced physical mass
rank was 24. Source baseline was
`103357f870e5712ee61405ee4d5d5f293f0bdc3a`; the coupled mass source
SHA-256 was
`8e3784868fce5bfbc786e0a736e044b87f46bef8198df1665adca24679a61296`.
The test file SHA-256 was
`b011cb4d0e7efcd75de6dfa71056221f24e497ca060b56c84e10537bc3b93109`.
The normal `pytest -q` collection produced no output for about 90 seconds and
was stopped; it is not counted as a pass. The direct invocation passed.
After that preserved stalled attempt, integration reran exactly this file via
the worktree `.venv` with `PYTHONPATH=src;tests;.`, `NUMBA_DISABLE_JIT=1` and
one BLAS/OMP/MKL thread. Pytest reported `1 passed in 2.57s`; this is the
qualified check for this bounded development slice, not F07 acceptance.

**Remaining F07 work.** This one-case result does not qualify a mixed Q4/S3
interface, free-free rigid modes, loaded/prestressed spectra, mesh convergence,
modal range, release behavior, or buckling. The shared checkpoint and frozen
execution authorities remain unchanged.
