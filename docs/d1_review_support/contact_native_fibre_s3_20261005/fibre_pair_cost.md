# Native physical-fibre pair: geometry cost and continuation - 5 October 2026

Status: verified development improvements; coupled final target remains incomplete.

## Measured action and checks

First-Newton profile identified search as nearly the complete contact cost, with factorization only 0.0078 s. The opt-in V6_GLOBAL_CHORD mode now carries one complete-source/two-target lower bound through the search. Local certificates remain at unresolved leaves. Historical default V4 is unchanged and checkpoints cannot be rebound from V5 to V6.

Exact candidate contact is reused in assembly, and a complete candidate evaluation is reused at the following Newton iteration within the same target and committed origins. Guards remain before consumption. Different-pose reuse is rejected; both-body tangent conversion still copies the contact block. Physical commit continues to reconstruct and validate its record.

- Installed core controls: 14 passed in 19.139692 s / 198623232 B; extra cancellation-on-complete-reuse control passed in 2.676860 s / 182046720 B.
- Straight active/open, curved open with nonzero chord deviation, and curved active interior pocket controls pass. The pocket cannot be discarded by its open chord/endpoints.
- All 527 Python files match candidate15 installed package byte for byte.
- Same-family supporting source review found no consequential remaining defect; this is not different-family engineering acceptance.

## Performance observations

Profiled first-Newton diagnostic: 43.330693 to 13.124142 s (about 3.3x), at identical load, material, geometry and tolerances. Endpoint contact energies match; a stronger gap certificate changes reported lower bounds appropriately. The open trial swept check fell from 16.007172 to 0.004931 s. These are diagnostic comparisons, not balanced complete-route performance claims.

The new full single-jump route still timed out at 120.114197 s / 198377472 B. A separate staged path (.005,.01,.02,.03,.04,.05), preserving the final 0.0025 N force, law100 N/m2, gap50 um and one owner clock, also timed out at 120.136990 s / 199602176 B. No accepted prefix was persisted by either killed run; none is claimed. Neither failure is regraded or automatically rerun.

A ten-contact-call discriminator stopped deliberately in 18.156209 s. Initial trials repeatedly incur unresolved active ownership or real gap rejection. Its independent finite-segment oracle found last-trial minimum gap -175.766888 um versus production lower -175.766893 um: rejection reflects physical penetration, not an overconservative bound there. This control terminates without an accepted target and is not coupled qualification.

The first profile attempt had a test-file indentation defect; collection failed before numerical execution. Its raw record is retained separately from mechanics failures.

## Decision

Stop optimizing without a mechanics discriminator. Reuse/extend the existing independent small-motion Timoshenko finite-foundation reference for a tip-loaded relative pair and assess the declared line regularization against the dimensional gap requirement. Keep elastic/reference scope explicit; it cannot qualify nonlinear native mechanics. Select a justified enforcement/globalization candidate from that evidence before another coupled campaign. No cap, gap, stiffness increase or clock reset to rescue the recorded failures.

Full C0-C9 and native paired static acceptance remain incomplete; no delivery forecast follows from these local gains. Source identities, raw paths and resources: [summary](fibre_pair_cost_summary.json).
