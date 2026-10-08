# F03 local classical reference — independent design review

22 September 2026. **Mechanics foundation and implementation limitations
accepted; execution protocol remains open.**

- Design author: `f03_port_mechanics`.
- Independent reviewer: `finite_pad_axis_review`.
- Accepted draft: `B3_GE_E4_PL_G0_F03_LOCAL_REFERENCE_DESIGN_DRAFT.md`.
- Accepted file SHA-256:
  `36ce310a99df390fa95c83fd2e346315fb46cc795665f6e5de1ba747ddb4bc3b`.
- Initial reviewed draft SHA-256:
  `ef742db8a40d622dfbd0d2755bb5c0bd6a704b81ff784e97dd0e9a01ab4aa058`.

The reviewer accepted the fixed-pad H1-to-H2 mapping, three independent
root constraints with free root slope, conforming C0 admissibility,
translated station breakpoints, continuity of beam section resultants
and absence of artificial internal beam atoms. The interior stress-jump
convention and integration-by-parts signs are consistent.

The first review required explicit limitations before implementation.
The author added them, and the reviewer confirmed their presence:

1. A fixed physical footprint can intersect increasingly many unknowns
   under refinement. Registration must bound active trace support,
   restricted-beam nonzeros, factorization fill, workspace and cost.
   Sparse storage alone does not establish linear complexity.
2. Distinct positive rational station intervals can have identical rounded
   endpoints. Preserve them; prohibit snapping or silent omission. Their
   local-coordinate/high-precision evaluation treatment needs review.
3. The stated geometry construction assumes axis-aligned rectangles.
   General quadrilaterals need another proof. Balanced refinement alone
   does not establish continuity at hanging nodes; conforming closure or
   exact trace constraints are required.
4. A support lifting reaction includes supported/free boundary work minus
   volume-residual and interior-jump work, with a common moment origin.
5. The dual norm compares the complete interface functional, including
   endpoint atoms. A separately verified piecewise norm contract must
   replace any assumption that the frozen global-polynomial helper already
   accepts piecewise fields.

The final review was read-only. It performed no computation, altered no
state, and granted no scientific execution authority. Polynomial degrees,
mesh hierarchy, collapsed-coordinate interval treatment, norm evaluation,
resource limits and case inventory remain open for a concrete protocol.

Physical acceptance criteria remain unchanged. This design does not select
a native production space, qualify the classical reference, close G0B or
permit G1. The spatial evidence supporting the investigation is separately
sealed in `f03-spatial-residual-v1`; it must not be extended or replayed.
