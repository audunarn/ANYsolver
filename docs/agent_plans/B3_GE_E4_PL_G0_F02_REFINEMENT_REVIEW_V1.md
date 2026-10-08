# Independent F02-R-v1 physical footprint evidence audit

Read-only post-execution review, 21 September 2026. The frozen runner was not
re-executed, and the raw log was not changed. This adjudicates the registered
physical in-plane membrane refinement/thickness diagnostic only.

## Identity and provenance

| Input at review | Recomputed SHA-256 |
| --- | --- |
| `scripts/probe_b3_ge_e4_pl_g0_f02_refinement.py` | `e02548f4eb3c6259d0fb1036318abc5e79e718ad88e15fef3c74063bc20bc890` |
| `docs/agent_plans/B3_GE_E4_PL_G0_REGISTRATION.md` | `157ca06170ee446c6745e107f08ff349624751c6559cd9b236f1d09b9bd64c09` |
| `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f02-refinement-v1.log` | `a7bf86e9f2c999cdfe804b67c170af548daf87d661f8111fd085f0ae37df9e16` |

The 6,081-byte raw log contains one structured result plus launcher markers:
case `G0-F02-R-v1`, frozen runner hash, source HEAD
`865483d567b45ee1ffacdfd54dbfa11678ced61b` (matching the reviewed
worktree), import origin in that isolated worktree, Python 3.14.2, NumPy
2.4.6, SciPy 1.17.1, one-thread settings, disabled bytecode, and zero origin
and runner exits. Recorded elapsed time was 16.1163435 seconds, below the
600-second envelope. These markers are self-reported launcher evidence, not
independent environment or process attestation. Peak tree memory was not
measured, so the 8-GiB envelope cannot be independently checked from the log.

## Recomputed predicates

All 12 unique `(topology, n, thickness)` tuples are present: Q4 and diagonal
S3-V2D at `n=8,16,32` and `t=.035,.07`. Shell counts are respectively
64/256/1024 and 128/512/2048, matrix dimensions 162/578/2178, and
footprint node counts 9/25/81. The recorded runner assembles only the
reported `physical` shell stiffness entries at in-plane translation DOFs,
prescribes outer zero translation and footprint `u=(-y,x)`, solves free
translations, and forms the signed footprint reaction moment and `u^T K u`.

All 12 moments are finite and positive. Independently recomputing the
work-relative discrepancy and free/constrained residual ratio from the raw
moment, twice-energy and two absolute residual norms found zero discrepancies
or failed cases: maxima `1.455995078e-15` and `6.122357789e-15`, respectively,
against `1e-8`. The constrained norms are finite and positive. All six
thick/thin ratios have absolute error at most `3.996802889e-15` from 2,
against `1e-10`; the logged comparisons match the raw moments.

At `t=.07`, Q4 moments at `n=8,16,32` are 7.766515398e9,
7.388116721e9 and 7.204981418e9; S3-V2D moments are 9.213851274e9,
7.964385201e9 and 7.444489186e9. The four independently recalculated
successive changes, normalized to the finer moment, are Q4 0.0512172034
and 0.0254178731, and S3-V2D 0.1568816728 and 0.0698363583. The log
contains exactly six thickness and four refinement comparisons, with zero
missing, duplicate, or failed entries. Three decreasing values do not
establish an asymptotic continuum limit; the node-Dirichlet footprint itself
changes with resolution.

**Disposition: recorded F02-R-v1 preparatory membrane predicates PASS.** This
accepts the narrow physical in-plane footprint torque/thickness screen with
the provenance/resource limit above. It does not establish director or
transverse-shear preservation, finite-rotation attachment, drill behavior,
coupled beam reactions, F02 qualification, or G0B acceptance. Keep F02 and
G0B OPEN, retaining this v1 log and runner identity.
