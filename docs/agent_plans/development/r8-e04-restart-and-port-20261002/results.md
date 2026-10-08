# Actual E04 turning-point restart and finite external-port investigation

2 October 2026. Base c927770f. Product source unchanged: all 412 modules matched
installed wheel 6086fd4edb4246ab77a2c67fb898965e4e71d8020d4c0494b59bbbcb5dbe70b0.
Development evidence only; no aggregate gate closes.

The actual 4x4 roof restarts at arc step 13, the previously observed coarse maximum
2206.307106 N / 9.439122 mm central downward motion. Both the live owner and a fresh
restored owner continue three descending steps to 2126.204976 N / 11.254809 mm.
Every continued checkpoint is byte-identical; final displacement, resultants and
history are exactly equal. The complete installed route took 77.06 s and sampled
165003264 bytes process-tree peak, inside 600 s / 1 GiB. Runtime checks confirm one
numerical thread and JIT off. The same coarse geometry, density bookkeeping,
six-channel nodal pose bonds and section idealization from the previous
[roof evidence](../r8-e04-roof-20261002/results.md) apply. This closes this bounded
restart discriminator, not converged capacity, refinement, imperfections or G4D.

A pinned CalculiX 2.23 nonlinear RIGID BODY control prescribes translation
(.01,-.02,.03) m and rotation vector (.4,-.3,.2) rad on an element-free rigid
marker triad with the E04 section frame and .01905 m offset. Its marker motion
matches analytic Rodrigues kinematics within output-rounding bounds. The
reported REF/ROT RF values are zero and cannot validate the expected physical
support wrench or coordinate-dual moment. This is a kinematic building block,
not an E04 beam/shell or footprint reference.

The free rigid carrier on nine known Cartesian grounded springs fails with exit
201 at the 200-increment limit, reaching only load fraction .02135127. Preserve
this as FAILED execution. The last accepted prefix is near its independently
derived energy-minimizing proper-Procrustes solution (maximum marker difference
2.52794e-7 m), but moment residuals up to 1.81321e-7 Nm exceed their printed
rounding explanation. No full-load or work-validation claim follows. The oracle
is a global energy minimum; another incremental stationary branch would need
interpretation, not automatic rejection. No automatic rerun or enlarged budget.

Offline energy stationarity, rigid distances, coordinate-dual work, CRLF-only
identity normalization, incomplete-time and failed-output rejection passed four
checks; five unchanged roof geometry checks passed in the initial focused batch.
Independent source review found the parser's initial rounding flag overstated an
outer rotation bound; the flag now explicitly reports bound compatibility. The
strict byte parser also initially rejected CRLF-only input; its failure and
corrected replays are preserved. No product tolerance changed.

External executable SHA256:
27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f.
The [official CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf) restricts U1
to static small-deformation linear elasticity and disallows original beam/shell
nodes in RIGID BODY. Thus neither this marker control nor existing affine-MPC
references supplies an exact finite beam/shell connector. Preserve the external
comparison as open. Next useful external action requires a demonstrably matched
finite section/port route or an explicit engineering comparator; do not infer
roof capacity agreement from this control or repeat its failed run by default.

`runs-v1.zip` preserves raw successful and failed outputs, original runners,
reviewed source, parser failure, offline checks and whitelisted execution
metadata. SHA256: 8e64c2ecdf7f2ad0ebedcbec5374b2a75ed7ada5cec3544a16737c94baabfed2. No full environment maps are included. Independent
OpenAI development review is not the still-required cross-family/scientific
acceptance. Formal F03 remains unconsumed; no main/push/release action occurred.
