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
