# Independent F09-L-v1 local linear B2 evidence audit

Read-only review on 21 September 2026 of the once-executed, bounded
preparatory F09-L-v1 case. No runner was re-executed and no raw evidence was
changed. This adjudicates only the registered local scalar/generalized
flexibility prototype, not F09 or the new product operator.

## Bound inputs and provenance

| Item | Recomputed SHA-256 |
| --- | --- |
| `scripts/probe_b3_ge_e4_pl_g0_b2_linear_flexibility.py` | `e7bb2741b631ac6ff7141b080db5b1af101e056a280ad93087509eddb062c530` |
| `docs/agent_plans/B3_GE_E4_PL_G0_REGISTRATION.md` at review | `29e005ad1621056ab749cce3bb23c0fdadd9901f7813a39c72b466c530846ae0` |
| `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f09-linear-local-v1.log` | `cff76eec04ed41b67f646d3ed14d06bbd4af00ff18943cc6ca7598109fd7c8b0` |

The 7,827-byte log contains one structured result and nine launcher/identity
lines. It binds case `G0-F09-L-v1`, runner hash, source worktree import,
source HEAD `f1d1734cc1a72862ebb5956db48b47a64303236c` (also observed as
current HEAD), Python 3.14.2, NumPy 2.4.6, SciPy 1.17.1, one-thread settings,
disabled bytecode, `origin_exit=0` and `runner_exit=0`. These are recorded
launcher markers, not a separate independently signed process/environment
record. The log has no elapsed-time or peak-tree-memory measurement, so the
120-second/2-GiB envelope cannot be independently verified from this file.
The registered runner was frozen at the same hash before execution.

## Scientific checks

Exactly S0, S1 and S2 are present, with both y and z displacement cases,
12-coordinate input vectors, positive nonzero physical and rational energy,
six basic rank, six positive modal factors, and rigid-basic residual at most
`1.047e-17`. Independently recalculating the unfloored Timoshenko transverse
formula from each reported input matches all six logged physical energies at
printed precision. The largest recorded physical-relative energy error is
`2.711e-16`, and the largest directional force-work error is `1.356e-16`,
below `1e-12`. S0's full local matrix differs from the equivalent public
scalar law by `2.601e-19` relative. Its station/complementary, basic and
coordinate work errors are at most `1.224e-16`; physical force agreement is
`1.075e-18`, directional energy derivative error `4.595e-12` and tangent
action error `2.957e-12` (both below `1e-6`). The log retains actual work,
normalization scales, basic/station resultants and direction vectors.

The historical public/physical energy ratios are recorded as diagnostics:
approximately 1 in S0, 184.6923077 in S1 and 2.417851639229e12 in S2,
identically in both directions. They do not enter the runner's final pass
condition. The tiny S2 physical energy `2.067951531383e-29` remains positive
and agrees with the rational oracle to `2.711e-16` relative; this is local
modal-factor retention, not numerical assembled graph rank or conditioning.

The generalized case contains the registered SPD diagonal and three
off-diagonal couplings and L=2; its section and basic flexibility minimum
eigenvalues are positive (1.98005 and 0.198948), and basic rank is six.
The independently expanded polynomial versus three-point flexibility
integral differs by `1.077e-16` relative. Station virtual-work error is
`2.392e-16`, tangent skew `1.424e-17`, directional force derivative error
`2.397e-12`, and rigid-basic residual zero, within all registered bounds.
All four negative cases are present with input, `ValueError` type and detail;
the non-SPD fixture passes through the same generalized validation as the
positive fixture. Independently checking the complete recorded numeric
predicate set found zero failures. The output status and exit marker agree
with that narrower calculation; no omitted or failed row was found.

**Disposition: recorded F09-L-v1 local preparatory predicates PASS**, with
the provenance/resource measurement limit above. This is not a new product
operator, graph/assembly proof, shell trace, attachment, mass, geometric
prestress, installed compatibility, performance, F09 or G0B acceptance.
Keep F09 and G0B OPEN and preserve this v1 log and its identity. A production
F09 candidate needs its separately frozen source/input graph, admitted range,
independent review, and full section/trace/assembly evidence.
