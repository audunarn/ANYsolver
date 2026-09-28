# Eccentric source director work — bounded development check

Solver source before this check: `3f50eb08` on `codex/general-contact-core`. Probe: `scripts/general_contact_d1_eccentric_source_director.py`, SHA-256 `e8f3152d79e7f9fa49fef7577dd9b02f1e070ba7cd0117403d5c9be39c4af312`. Python 3.14.2, NumPy 2.4.6 and SciPy 1.17.1. This is local fixed-multiplier code verification, not an accepted static solution or independent D1 assessment.

**Question.** The aligned flat cycle produced only a 1.52e−10 source moment derivative. Does the admitted Q4/S3 Jet2 work map differentiate a physically meaningful source director couple when contact force is eccentric to its physical director?

**Fixture.** Two coplanar Q4 source faces and two S3 target faces use the declared bottom/top skins, 50 mm thickness and a 10 mm S3 reference offset. Their initial physical gap is 15 mm with no active pressure. A candidate moves the source down 16 mm and raises the two target tip nodes by 1 mm, making a gently tilted current target. The candidate has six active nodal pressure modes and a minimum physical gap of −2 mm, within the fixture's explicitly declared 5 mm gap setting. Normal regularization is 1e6 Pa/m and fixed multipliers are 1000 Pa. The candidate is used only for local residual/tangent evaluation; no equilibrium or increment acceptance is claimed.

An equal `ry` variation at all six source nodes probes full force and moment rows on both bodies. At both ± perturbations, the active pressure mask, positive support mask, aggregate overlap incidence and differentiated pair signatures remain unchanged.

| Quantity | 1e−5 rad step | 5e−6 rad step |
|---|---:|---:|
| Source force directional error | 4.97e−10 | 1.34e−9 |
| Source moment directional error | 3.59e−9 | 8.64e−9 |
| Target force directional error | 7.31e−10 | 1.25e−9 |
| Target moment directional error | 3.13e−9 | 1.06e−8 |

The source moment action is 3.786e−4 in the reported generalized directional units and the target moment action is 2.433e−4, both well above the prior flat-cycle action. Integrated source/target force and moment balances are 4.54e−16 N and 2.28e−13 N·m. The focused reproducible regression test passed once in 3.07 s. The bounded probe completed in 4.11 s at 169.60 MB peak process-tree RSS, under the existing 180 s/1 GB development cap.

The first two attempts failed fixture capability validation because the probe initially used one Q4 source face and then omitted the required explicit pressure tolerance. Those were setup defects; [first](d1_eccentric_director_setup_failure_20260928.txt) and [second](d1_eccentric_director_setup_failure_v2_20260928.txt) logs are retained. The final fixture uses the admitted refined two-Q4/two-S3 profile. No production solver code was changed.

[Raw result](d1_eccentric_director_final_20260928.json), [resource record](d1_eccentric_director_final_resource_20260928.json), [console](d1_eccentric_director_final_console_20260928.txt) and [focused test](d1_eccentric_director_test_20260928.txt) are retained. This narrows the source director work-map gap for a smooth eccentric local branch. Clipping ties, coupled response, pressure-space stability and final D1 acceptance remain separate.
