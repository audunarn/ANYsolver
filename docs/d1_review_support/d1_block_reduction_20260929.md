# D1 saved-pose block-reduction cost screen — 29 September 2026

The 4-Q4/16×16-S3 saved-pose contact linearization remains a measured D1 cost limit. A geometry worker tested one temporary contiguous quadrature block reduction against the current batched Jet2 route. The test did **not** run a coupled equilibrium or change the accepted mechanics. The source candidate was removed after measurement; production source and focused test returned to HEAD `331a8900`.

The ABBA same-pose comparison held the saved 8×8 accepted pose interpolated to the existing 16×16 target, nodal forces, model and integration settings fixed. Both paths used 2524 reported evaluations and 2416 integration triangles, with equal overlap branches. Scaled support, gap and Gram differences were zero; maximum scaled gap-gradient and tangent differences were 1.11e−16 and 3.43e−20. Peak sampled RSS was 305.95 MB; the probe elapsed 68.03 s with 10.38 s setup, below the existing 180 s / 1 GB cap.

| Path | First linearization | Second linearization | Median |
|---|---:|---:|---:|
| Current batched Jet2 | 12.628 s | 13.291 s | 12.959 s |
| Temporary block reduction | 12.588 s | 19.095 s | 15.842 s |

The variable candidate timings show **no demonstrated material saving**. The paired median ratio is 0.818, but two runs per path do not establish a stable slowdown. The candidate does not justify another 16×16 coupled solve. This is a failed optimization result, not a contact-mechanics failure or an acceptance gate.

The temporary `_rule_batched` branch reshaped the eight batched Jet integral arrays into triangle-by-quadrature blocks, summed each block along its quadrature axis and rebuilt scalar Jet2 results. It computed the 16 value-only pressure-mass entries with a per-triangle `einsum`. The original reduction remained the other branch under a private `_BLOCK_REDUCTION_ENABLED` flag. Its exact patch text remains in the task tool history; no candidate Git blob or standalone patch was saved.

The [raw JSON](d1_block_reduction_16x16_probe_20260929.json), [text](d1_block_reduction_16x16_probe_20260929.txt) and historical [probe script](d1_block_reduction_16x16_probe_20260929.py) are retained. The private flag was removed from current source. **Running the historical script at HEAD would silently compare the baseline with itself**, because assigning the absent module attribute does not enable a candidate. Reproduction first requires reconstructing that temporary branch. No new source optimization is promoted from this slice.
