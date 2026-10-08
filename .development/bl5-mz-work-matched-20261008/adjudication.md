# BL5 work-matched Mz development result — 8 October 2026

The original three-edge BL5 probe transferred a +1 N m tip moment, but its
saved `C.T @ lambda` shell field is the algebraic constraint covector. Under
the native KKT convention, the **physically exerted** shell interface action
is `-C.T @ lambda`: +1 N m. The raw probe and original decision note are
unchanged. Its -1 N m support moment balances the +1 N m exerted interface.

The new case uses the already declared 1 m by .2 m flat panel, .02 m shell,
.04 m by .06 m resolved bar and the same five-channel weak material-director
trace used by the existing Fz reference. The native bar has the admitted
elastic physical-fibre section. A +1 N m native nodal Mz is paired with
resolved-bar end traction `t_x=-Mz*y/I_z`, integrated consistently on both
physical x=1 bar faces. The traction has zero resultant force and unit Mz
work on the six rigid bar fields. It preserves local section deformation and
therefore does not make the two body discretizations identical.

Five bounded attempts are retained. V1 failed the continuum equilibrium
gate without decomposed diagnostics. V2 exposed a 631.6 active-row ratio:
floating quadrature had left tiny nonzero loads on mathematically unloaded
odd-symmetry rows. The analytical y-odd parity of the exact traction and
symmetric geometry was enforced on nodal loads in V3; maximum correction
was 1.78e-15 N. V3 passed but displayed the native algebraic covector as an
exerted interface action. V4 corrected that sign label. V5 passed with
separate shell/beam internal and interface-work accounting. No equilibrium,
compatibility, work or physical tolerance was changed. The per-attempt
receipts remain immutable; `cumulative-ledger-v1.json` records the complete
12.582444100014982 s process-wall use of the 90 s development allowance.
The final case used CPU0, one loaded numerical thread, disabled JIT, and
165,392,384 sampled peak RSS bytes, under the 2 GiB/60 s per-process limits.

Final V5: applied end wrench is +1 N m Mz; both shell interface exerted
wrenches are +1 N m Mz, and both physical support moments are -1 N m within
3.1e-11 N m (continuum) and 3.5e-13 N m (native). Continuum free-equilibrium
ratio is 2.05e-12 and native 1.10e-13; scaled constraint gaps are
8.76e-22 and 1.30e-23. Separate body virtual-work errors are at most
1.65e-11 relative to applied work.

The work-conjugate tip rotation is 6.445248134408049e-7 rad for resolved
continuum and 1.8863005195465056e-6 rad for native beam/shell, a large
1.2417757061057007e-6 rad difference. The net energy difference is located
primarily in **beam-side internal work**: native exceeds resolved continuum
by 1.3265412179e-6 J, while native shell work is 8.4765511814e-8 J lower.
This is an attribution of the calculated work difference by body, not proof
that the native beam law itself is wrong: the interface force distributions,
retained half-cell ports and body discretizations differ. In particular,
common five-channel virtual work does not identify the two discrete spaces.

Decision: keep BL5 as experimental. The next discriminator is a common
physical beam-side action/port comparison using one saved multiplier density
and the existing body-port machinery, while holding section, supports and
end work fixed. It must decide whether the beam work difference follows the
body operator under the same action or from the different interface action
distribution. Do not run another mesh refinement or assert physical accuracy
from the present response difference. F03, M2, G0 and mandatory executed
external comparisons remain open; no production capability or release claim.

Authoritative raw data: `case-v5/result.json`, all five unique stdout/stderr
and receipts, and `cumulative-ledger-v1.json`. The final source is
`scripts/r8_bl5_mz_work_matched_dev.py` at the source hash in receipt V5.
