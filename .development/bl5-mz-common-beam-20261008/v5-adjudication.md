# BL5 Mz V5 exact-face development discriminator

The user authorized exactly one new beam-only comparison after the V4 ledger
closed. V5 ran once with the corrected C3D20 material-face interpolation.
The one-use receipt is `receipt-v5.json`; its 2.8735119000048144 s process
wall was below the 30 s cap, sampled peak process-tree RSS was 166604800 B,
CPU affinity was `[0]`, one numerical thread was effective, and JIT was
disabled. Exit code was zero and no time or memory limit stopped the run.
V1–V4 evidence and their CLOSED FAILED disposition are unchanged.

The reference beam-local slots 55, 58 and 130 now have exactly zero applied
load, as required by their analytically vanishing face traces. The resolved
beam's original-operator equilibrium ratio is `1.60713192925416e-12`; the
native beam's is `3.93849478349559e-12`. The coupled resolved preflight
reports `2.0509267766074977e-12` free-equilibrium ratio and
`4.235164736271502e-22` compatibility. Both beam-body results have status
`DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED` under unchanged checks.

With the same projected weak P0 density, the resolved C3D20 beam body has
paired work `2.40980605695025e-7 J`; the native retained-coordinate B3-GE
body has `1.74538504099805e-6 J`. Their ratio is `7.24284444370156` and
difference `1.50440443530302e-6 J`. The reference and native load wrenches
remain balanced at the saved ~1e-11 N/Nm scale; native virgin material energy
and work agree at the reported zero relative error. These are successful
development solves, not a validated same-body comparison: the C3D20 and
native beam primal spaces, retained half-cell fields and trace support differ.
The ratio alone cannot identify a connection-law, beam-operator, or physical
accuracy defect.

The next decision is to distinguish native beam-body compliance from
representation differences using an independently matched beam-body
reference or bounded convergence argument. Do not adjust the connection law
or multiplier space from this single ratio. No F03, old Fz retry, external
solver, mesh sweep, gate acceptance or release occurred. V5 is consumed;
its unused process-cap time is not transferable authority.
