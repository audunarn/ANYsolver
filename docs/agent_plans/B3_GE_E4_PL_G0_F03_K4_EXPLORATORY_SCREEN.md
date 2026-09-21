# F03-K4 channel-adapted span: unregistered adverse screen

21 September 2026. This is a disposable, **unregistered** mechanics
falsification probe, not single-use qualification evidence. The script
`scripts/probe_b3_ge_e4_pl_g0_f03_k4_channel_rank.py` combines free
native nodal P1 translation tests and all native cellwise P0 yaw tests
from already assembled physical weak rows. It extracts the matching
block Gram mass and unrestricted signed constraint rows, then uses
the existing retained KKT and fixed K2P smooth/sine loads. It reports
only supported rank, sampled station gap, shell energy, full/condensed
parity and force/moment balance. The physical trace factor and gap
Gram remain valid because the trace and overlay are unchanged.
Inherited P1 quadrature-error and row-incidence diagnostics are stale
for this combined row span and must be rebuilt before a registered trial.
Nine station gaps are
sampled lower bounds on the continuous maximum.

On Q4 and S3-V2D at beam input 8 and shell counts 1, 8, 64, all 24
combined rows have full native image rank, with zero algebraic
shell-only restrictions. Yet the Q4 coarse-shell sine case puts only
`9.5197e-7 J` into the physical shell; its sampled gap is small because
that response nearly suppresses the shell motion. Q4 smooth cases at
shell counts 8 and 64 show sampled gaps of `0.4710` and `0.4743`
times the fixed displacement scale, despite full rank and low solver
residuals. S3 smooth samples similarly stay near `0.44` under shell
refinement. The output was generated in one local exploration, not
frozen as an immutable gate. No independent continuum target is
present.

An independent read-only mechanics audit confirmed the row/mass
selection, signed KKT, actual fixed-load use and support recovery for
the quantities reported. It identified the stale inherited diagnostics
and sampled-gap limitation above. **Decision:** the simple
channel-adapted span does not resolve the adverse physical response
in this bounded fixture. Do not register this span as the next
production candidate without a materially different mechanics
argument. This finding does not prove that all channel-adapted mortar
constructions fail. F03/G0B remain open.
