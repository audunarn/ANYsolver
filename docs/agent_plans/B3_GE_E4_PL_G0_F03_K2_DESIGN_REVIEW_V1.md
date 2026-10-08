# F03-K2 design review, before registration

21 September 2026. Independent read-only F03 mechanics review of
[`B3_GE_E4_PL_G0_F03_K2_DESIGN.md`](B3_GE_E4_PL_G0_F03_K2_DESIGN.md).
No K2 candidate was run or registered. The reviewer found the proposed
conditional β-square dimensionally consistent and the full retained `-S_r`
distinction intact. The fixed smooth load matches the current native lifted
trace load. The old half-cell alternating load changes wavelength with
refinement and cannot support a fixed-problem convergence claim.

The review required two precise corrections before any registration: the
full multiplier Riesz matrix must be `H_scalar ⊗ I3` in basis-major
three-channel order, with yaw converted to length by `ℓ=.46 m`; and the
zero-resultant signed sine load needs a fixed nonzero normalization such as
`f0 L0`. Both are incorporated in the draft. The proposed `H^-1/2` norm
remains a hypothesis for this offset four-point pose trace, even though
standard mortar theory motivates it. A passing mechanical threshold needs
a uniform continuity/norm-equivalence derivation and separate exact
retained-system analysis. Until then β may be recorded only as a
conditional exploratory diagnostic.

This review does not qualify K2, the six-channel F03 formulation, G0 or
product integration. Freeze the remaining numerical realization and
physical reference contract, then seek another preexecution review before
an immutable K2 registration.
