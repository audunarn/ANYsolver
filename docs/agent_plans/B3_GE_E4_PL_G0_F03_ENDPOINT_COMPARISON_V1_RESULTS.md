# F03 endpoint-space comparison v1: unresolved auxiliary norm

22 September 2026. **All 30 equilibria completed; all ten registered case
decisions are UNRESOLVED_AUXILIARY_NORM.** The frozen squared-dual-norm
resolution check failed for the enriched comparator. Preserve this decision;
do not treat the successful solves as an accepted comparison or G0B pass.

## Frozen execution and terminal decision

Source: `2b64174becb7d4d7fe150bf0efbaf613a75af07f` on the isolated integration
branch. Accepted main remains `be41a77a62e1cd7e1767bda6e955253af0819f91`.
The independent pre-execution review gave GO after the 48-check focused
suite. A final reporting correction preserving failed-child reasons passed
all 14 affected checks. Review details are retained with the registration.

Evidence root:
`.qualification/b3-ge-e4-pl/f03-endpoint-comparison-v1/`.

| Artifact | SHA-256 |
|---|---|
| Registration | `56548b5a4d44c2ae09235d2557f2aa36ed3232d31446865caf172e03ce0380bb` |
| Adjudication | `956539fbdc34eedb1c6e7de609f2f386f706a853d67f5a5b157f60de426b3fd6` |
| Orchestration | `a9918683a39d86cb082acf118f1ca34846e92f19356aa0384a44709dccf9d1b2` |

All ten child processes exited zero, with all three formulations and their
owned snapshots saved in each case. Serial execution took 263.3 s against
the 1,200 s launch budget. Maximum child duration was 38.089 s and sampled
RSS 80.863 MiB, within 900 s and 8 GiB limits. The one-use adjudicator
exited **1**, preserving the unresolved scientific predicate.

An independent read-only audit found no evidence defects: ten cases,
30 final state pairs, all 30 partial pairs exactly matching their finals,
all 13 source hashes and parent parity. It confirmed that only the
enriched auxiliary-norm check fails and that the registered unresolved
terminal decision is correct. It did not rerun any cases.

The original P1 solution matches each frozen parent snapshot inside the
registered coordinate and multiplier tolerances. Equilibrium, compatibility,
signed support balance, reaction partitions, energy identity, enriched
energy ordering and structural inverse-action checks all pass. No finite
Schur quotient is nonpositive. These facts do not override the failed
auxiliary-norm predicate.

The independent norm uses the full H1 interval, including endpoint
evaluation, with 32 and 64 subdivisions **per mortar cell**. The frozen
criterion is `max(abs(eig(G64,G32)-1)) <= 0.001`.

| Nm | P1 change | Hybrid change | Enriched change |
|---:|---:|---:|---:|
| 4 | 0.000606506 | 0.000365272 | **0.001449543** |
| 8 | 0.000609311 | 0.000520829 | **0.001327423** |
| 16 | 0.000610016 | 0.000584799 | **0.001318418** |

This auxiliary calculation is independent of the structural shell/beam
mesh; its values repeat where Nm is unchanged. P1 and hybrid individually
meet its resolution criterion, but the registered comparison requires all
three spaces. Do not remove enriched retrospectively. No 128-subdivision
retry, relaxed threshold or overwritten registration was used.

## Descriptive physical results

At fixed `(Ns,Ny,Nb)=(8,16,16)`, endpoint-compatible spaces substantially
change the root load path. These are different finite constraint spaces;
the changes cannot be called an algebraically equivalent improvement.

| Q4 space | Nm | Tip uy, micrometres | Root Fy, kN | Root Mz, kN m | Stored energy, J |
|---|---:|---:|---:|---:|---:|
| P1 | 4 | 44.4846 | -445.3010 | -8.3615 | 24.28888 |
| P1 | 8 | 39.5169 | -601.2428 | -8.8795 | 19.89288 |
| P1 | 16 | 35.4577 | -721.6444 | -11.8057 | 16.45210 |
| Hybrid | 4 | 25.8366 | -787.9128 | -180.6036 | 10.43969 |
| Hybrid | 8 | 25.8057 | -788.5411 | -180.2683 | 9.67316 |
| Hybrid | 16 | 25.7997 | -789.1614 | -180.5531 | 9.56621 |
| Enriched | 4 | 25.8524 | -788.5489 | -180.2107 | 9.58380 |
| Enriched | 8 | 25.8051 | -789.0729 | -180.5436 | 9.56106 |
| Enriched | 16 | 25.7992 | -789.1560 | -180.5787 | 9.55723 |

The CST-CB results show the same pattern. At Nm=16, hybrid/enriched tip
uy is 25.4532/25.4528 micrometres, root Fy -789.9643/-789.9616 kN and root
Mz -182.3691/-182.3906 kN m. The Q4/CST-CB displacement and moment
differences still require structural refinement; agreement between two
spaces on a fixed shell mesh does not establish physical convergence.

Explicit endpoint forces/moments carry significant load. For Q4 hybrid,
root vertical atom changes from -682.598 through -721.070 to -749.416 kN;
the tip vertical atom changes from 93.531 through 52.105 to 33.463 kN.
These decomposed endpoint quantities have not settled merely because total
root force is comparatively steady. The first-quarter *total* Fy changes
from -510.328 through -484.161 to -493.512 kN, and its Mz from -147.927
through -141.881 to -144.109 kN m. The last force change is still about
1.9%; stored energy changes about 1.1%. Keep these channels visible.

With Nm=8, beam-only refinement Nb=8/16/32 gives hybrid tip uy
25.8028/25.8057/25.8059 micrometres and root Fy
-788.4840/-788.5411/-788.5438 kN for Q4. This isolates the previous strong
sensitivity to the boundary representation; it does not replace a joint
shell/beam/interface refinement or external physical comparison.

The observed endpoint gaps for hybrid and enriched are at floating
roundoff. Their line-gap L2 norms remain nonzero: Q4 hybrid decreases
12.960, 1.734, 0.147 micrometres as Nm=4/8/16, versus enriched
1.493, 0.315, 0.049 micrometres. This is consistent with the stronger
enriched feasible set. It supplies no native full-vector or nonlinear
attachment qualification.

## Next bounded work

Preserve this failed resolution decision and all raw/partial snapshots.
An independent full-H1 norm can be derived directly from the one-dimensional
Green function or a piecewise-exact Riesz solution, then checked against
analytical identities and conditioning bounds. That is a separate reviewed
norm study, not an automatic finer-grid retry or a reinterpretation of v1.
Any later use of the saved mechanical states must explicitly bind their
unchanged identities and the new analysis contract.

After resolving the norm, assess physical channels and structural refinement
before selecting a multiplier candidate. F03 and G0B remain open, G1 remains
barred, and the integration branch remains experimental. Main and the
package version are unchanged.
