# F03 next prerequisite: independent physical response and signed stability

21 September 2026. Read-only mechanics decision after K2P, K2L, K3 and the
unregistered K4 channel-adapted screen. **No new candidate is registered and
F03/G0B are not accepted.** Historical evidence remains unchanged.

At eight native beam half-cells, the supported planar lifted trace has 16
independent nodal translation coordinates and eight retained cell-yaw
coordinates. K2L found shell-only compatibility restrictions for the
27-row P1-beam and fine shell-grid spaces. K4 instead selected the 24 native
translation/yaw rows and obtained full native row rank with zero shell-only
restrictions. Nevertheless, the coarse Q4 sine load transferred only
`9.5197e-7 J` of active shell work; the smooth shell-refinement samples
kept a gap near `0.47` of the fixed displacement scale. These are real
physical-response concerns in the bounded model, not a rank diagnosis.

An invertible change of multiplier basis, including an exact Riesz-dual
reweighting of K4's same row span, leaves the kernel of the constraint map
unchanged. It cannot change that displacement solution. A next candidate
must alter the actual local test span or mechanical trace, with a derived
patch and work argument; rebranding K4 rows is not a new experiment.

Before freezing it, establish two independent references:

1. A resolved physical load-response target for the same section, shell
   surface, boundary frames, four-point pose map, signed smooth and sine
   continuum loads, and attachment interval. Compare Q4 and S3-V2D at
   `N_b=8,N_s=1` and `N_b=8,N_s=64`, with at least three **joint**
   refinement levels as well as the reciprocal fixed-side reaches. Record
   shell and beam station motions, shell/beam strain energy, support force
   and moment, trace work, and a continuous or certified upper bound on
   pointwise gap; nine sampled stations alone give only a lower bound.
   An independently implemented resolved operator or an executed external
   model must document its own idealization and convergence. Reusing the
   candidate KKT solution as its reference is circular.
2. A justified discrete norm for the exact native retained, signed saddle
   operator and a dual physical trace norm. If internal coordinates `r`
   are condensed *for analysis*, retain the trace columns `C_r` and the
   induced multiplier block. For blocks `K_pp,K_pr,K_rp,K_rr,C_p,C_r`, the
   reduced system has `K_e=K_pp-K_pr K_rr^-1 K_rp`,
   `C_l=C_p-C_r K_rr^-1 K_rp`,
   `C_u=C_p^T-K_pr K_rr^-1 C_r^T`, and
   `-S_r=-C_r K_rr^-1 C_r^T` in its lower-right block. Neither a
   physical-only positive-definite Schur floor nor raw mixed-unit KKT
   singular values prove a uniform inf-sup bound. The norm must account
   for cell-yaw jumps and physical translation/rotation scales and be
   checked over the registered mesh-ratio/refinement range.

The next local sparse candidate must preserve fixed reference
correspondence and actual native/shell trace derivatives. Its overlay
incidence, compact multiplier support and memory growth must be measured;
a model-wide inverse Gram is not a sparse local dual. Falsify it against
both physical references, continuous gaps, traction jumps, support
reactions, shear/torque transfer, and the full retained system, not rank
or equilibrium alone. Only after the reference, norms, candidate equations,
mesh inventory, tolerances and resource bounds are frozen should a new
single-use F03 registration be reviewed and executed.

Independent read-only mechanics review supplied the native 24-dimensional
count, the kernel argument, the signed-block caveat, and the specific
adverse cases. It proposed **no evidence-supported new space**. G1
production integration therefore remains barred by G0B.

The subsequent independent membrane suboperator screen is recorded in
`B3_GE_E4_PL_G0_F03_MEMBRANE_REFERENCE_SCREEN_V1.md`. S3's in-plane block
matches an independently assembled constant-strain triangle, while E4-PL's
stationary-condensed Q4 differs materially from a classical bilinear Q4 at
fixed mesh. A standard Q4 or CPS4 result may be an independently converged
continuum comparator, but not a same-discrete-operator replacement. This
changes the required reference construction; it does not select a line law.

The CalculiX U1 beam-only execution feasibility record is
`B3_GE_E4_PL_G0_F03_CCX_U1_FEASIBILITY_V1.md`. U1 tip translation approaches
an analytical Timoshenko target over five meshes, but no mixed deck has run
and the exploratory nodal `RF` output is not a verified support reaction.
The external route remains an auxiliary comparator until its coupled
idealization, balance, energies, gap and joint-refinement evidence are
executed and reviewed.

The first coupled stock CalculiX 2.23 U1+CPS attempt then failed in
preprocessing, as preserved in `B3_GE_E4_PL_G0_F03_CCX_MIXED_FAILURE_V1.md`.
It produced no displacement or coupling evidence. A new external route
requires its own corrected executable identity or a distinct validated
idealization; the failed source/deck/result must not be overwritten.

The independent classical-membrane/Timoshenko exploratory response and
its v1/v2 numerical limitations are preserved in
`B3_GE_E4_PL_G0_F03_RESOLVED_CONTINUUM_SCREEN_V2.md`. A scaled collocation
solve can have excellent balance and full constraint row rank while locking
the coarse Q4 physical response almost completely. Its affine beam load
and trace are not the exact interior field. The continuum-reference and
signed-stability prerequisites above remain open.

The follow-up homogeneous exact-static Timoshenko-field screen is recorded
separately in `B3_GE_E4_PL_G0_F03_RESOLVED_CONTINUUM_SCREEN_V3.md`.
Virtual-work-consistent beam loads and interior station poses remove the
v1/v2 affine-field inconsistency, but Q4's coarse fixed-beam reach still
locks and joint refinement has not converged. Finite collocation remains a
different attachment law. This is exploratory reference work, not a new
F03 candidate or G0 pass.

The unregistered joint/one-sided classical continuum v4 refinement is
preserved in `B3_GE_E4_PL_G0_F03_RESOLVED_REFINEMENT_V4.md`. Signed sine
tip responses approach each other, but smooth loading and off-station yaw
gaps are not yet converged under the tested joint x/y/beam refinement.
Treat algebraic balance and small tied-station gaps as necessary, not as
proof of physical line attachment adequacy.

An independent continuously integrated *finite spring* sensitivity screen
is preserved in `B3_GE_E4_PL_G0_F03_CONTINUOUS_PENALTY_V1.md`. It has
sparse local traces and balanced work, but stiffness and mesh refinement
materially change the tip response. It cannot replace the production exact
multiplier or establish a physical reference by parameter tuning.

`B3_GE_E4_PL_G0_F03_STRONG_TRACE_INCOMPATIBILITY.md` derives a local
finite-space no-go: for the homogeneous exact-static conventional beam
field, exact polynomial-coefficient equality to the affine Q4/S3
four-sample position and yaw removes beam shear and bending on each
overlay interval. Independent mechanics review checked the derivation and
its load/native-formulation limits. Do not use strong coefficient tying
as the replacement physical oracle; seek a stable weak span instead.

The distinct coarse P1-beam weak space received its first complete
physical screen in `B3_GE_E4_PL_G0_F03_COARSE_P1_V1.md`. Its 15-row native
KKT is locally well solved for Q4/S3 and both signed loads, but fixed-beam
pointwise gaps remain about half the displacement scale after shell-only
refinement. Independent review rejected space selection from its rank or
equilibrium evidence. Historical K3 already covered P0-beam; an
unexecuted duplicate P0 runner was removed without consuming a new run.

Stock CalculiX B31/CPS is executable as a *different* mixed idealization:
the 12-case three-level external inventory and independent review are
recorded in `B3_GE_E4_PL_G0_F03_CCX_B31_REFINEMENT_V1_RESULTS.md`.
Smooth tips are nonmonotone and signed-load tips still move materially.
The width mesh, B31 shear/section law, finite station ties, yaw, reaction
and continuous gap are not a converged native physical target. Its raw
stored input-byte hashes are distinct from the generator's LF content
hashes, as adjudicated without altering the original records.

The local discontinuous biorthogonal-translation/P0-yaw weak span was
falsified on four adverse planar meshes after independent pre-execution
review; see `B3_GE_E4_PL_G0_F03_LOCAL_DUAL_V1_RESULTS.md`. It is genuinely
different from K4's assembled row span, with full native rank and accurate
equilibrium, but fixed-beam smooth gaps remain around half the displacement
scale on fine shell meshes. Coarse signed-load improvement did not persist
under shell refinement. Do not select this span from its rank or from the
coarse response. The independent physical target and signed retained norm
requirements in items 1–2 above remain unchanged; G0B remains open.

Two independent signed/trace norm diagnostics now sharpen item 2 without
closing it. `B3_GE_E4_PL_G0_F03_SIGNED_NORM_V1_RESULTS.md` retains the
exact native signed block and induced multiplier term: both K4 and local
dual have positive finite floors, but their operator-adapted constraint
floors roughly halve and signed KKT floors roughly quarter on three
joint mesh doublings. `B3_GE_E4_PL_G0_F03_BROKEN_TRACE_V1_RESULTS.md`
adds a broken physical trace graph with explicit cell-yaw jumps; its
finite-mesh continuity upper bound rises from about 80 to 124 on the
finest joint level. Fixed-beam shell-only refinement is nearly flat.
These are not uniform physical stability proofs or a line-law selection.
Next derive and test the actual dual of a mesh-local broken/jump trace
space, norm equivalence, mode shapes and physical response against an
independently converged reference before registering another F03 candidate.

The subsequent registered `B3_GE_E4_PL_G0_F03_TRACE_DUAL_V1_RESULTS.md`
computes an exact **discrete-image** dual using a global pseudoinverse of
the broken trace graph. Ten bounded cases and all three graph-eigenvalue
cutoffs completed with consistent source-bound evidence. In that norm,
the full signed KKT floor drops from about .26 to .035 on joint
4/4→16/16 refinement for both spaces and shell types, while it stays
around .11 under fixed-beam shell-only refinement. This sharpens the
beam-side mode concern but is not a mesh-local physical dual, uniform
proof or cure for the observed gaps. The independent converged response,
local norm derivation, mode interpretation and six-channel connection
work above remain prerequisites; F03/G0B remain open.

The independent classical comparator received a versioned sparse-trace
refinement through 128 panel-width and beam cells; see
`B3_GE_E4_PL_G0_F03_RESOLVED_SPARSE_V5_RESULTS.md`. All sixteen cases
completed and the four 64-cell anchors reproduced v4 to roundoff.
Preregistered comparator convergence nevertheless fails: Q4 smooth
96→128 tip changes 1.403%, beam energy 11.258%, scaled gap is 3.075%
of tip, and the width-cross control changes tip 1.032%; S3 smooth gap
is 2.246% and width-cross tip 1.622%. Even sine beam energy remains
mesh-sensitive. The finite-station classical comparison therefore
does not supply the independently converged and mechanically matched
F03 response target. Preserve its complete evidence and do not infer
native B3/E4-PL line-law acceptance from its algebraic balance.

The reviewed `B3_GE_E4_PL_G0_F03_WEAK_MODE_V1_RESULTS.md` reconstructs
the signed normalized KKT's weakest mode rather than inferring its cause
from a scalar floor. At joint 16/16 the mode is roughly 99.9% retained
in that norm, with opposing positive/negative retained action and
alternating yaw-row coefficients. The multiplier component is tiny;
the separately weakest signed Schur eigenvalue stays positive, about
.41 K4 and .57 local dual. This suggests a signed retained/high-frequency
mode mechanism but does not identify a physical loaded instability or
prove that alternation caused the decline. A changed *local test span*
still needs derived work/rank arguments and direct adverse-response and
stability falsification; mere K4 reweighting remains insufficient.
