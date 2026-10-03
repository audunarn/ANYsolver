# Affine BL5 flexible physical comparison — 3 October 2026

**Decision: keep the candidate experimental; flexible transfer fidelity is open.**
Independent external affine enforcement and the installed native comparison now
work on the same existing grid. Close displacement/work agreement is accompanied
by substantial interface and root-partition differences. The saved-state audit
identifies a discrete director-trace difference; it does not allocate the entire
force discrepancy or justify replacing native retained directors.

Source `9c75d6e9bcc26c33af4db28aee76cd3f10b30176`; saved-state audit source
`41adee98242377bc1d3b05566320deacf98c6473`. No product equation, default,
material tolerance, profile or checkpoint change. Formal F03 UNCONSUMED.

## Executed comparison and identity

One 16x4 Q4 shell/32 beam-interval model, eight physical supports of width0.125m,
all five channels with `[1,xi]` affine densities, unchanged geometry, sections,
offsets, frames, full shell-root grounds and first-five beam-root grounds.
Native retains16 B3 members and all384 internal coordinates; independent external
uses32 ElasticTimoshenkoBeam intervals with ASDShellQ4. They discretize the same
declared continuous connection; their director traces are not identical discrete
operators. The external reference independently integrates signed shape weights,
normalizes dependent rows by an invertible recorded transformation, and recovers
physical density from two free interior nodes per support. Center recovery would
lose slope. Native and external row/channel orders and signs remain explicit.

Three external processes executed Fy100N, Mx10Nm and Mz10Nm. One installed native
owner solved the same three loads with **one factorization**. Full poses,
retained variables, sparse operators, covectors, connection work and actual root
ground/internal/interface partitions are retained before numerical predicates.
Complete section/connectivity/frame/command/physical-row identities and all15
external physical controls are checked. Exact polynomial moment recovery includes
the quadratic lever-arm wrench; this changes diagnostic recovery, not product
quadrature.

**16 combined focused checks passed in0.69s**; worker isolated13 checks passed
in0.43s. The combined and first worker logs retain a pytest shared-temp atexit
permission warning (exit0); the isolated worker run has no cleanup warning.
The three external physical controls are at most4.0521e-12, native9.2975e-13;
preparation actual-update derivative discrepancy is at most3.29e-10. These are
successful equilibrium/work/derivative controls, not reference-accuracy passes.

All **417 source/wheel/site module bytes match** the unchanged installed wheel:
`ef96a35e7d24912500d42422be59171b0f4e9f5830157e0088d226960ce5a06b`.
The original installed binding and package checks remain at
[affine-density evidence](../r8-bl5-affine-density-20261003/results.md).
ANYmaterial remains an editable recorded dependency; this is not final package-
graph or Windows/Linux/Python-matrix acceptance. OpenSees3.8 requires the recorded
Python3.12 executable; DLL SHA256
`25ba42e1672526137d765d9c3631d1403e091f54f5afcdb9242f9243c63c3a96`.
This is a supplementary development reference; it does not close mandatory
CalculiX comparisons or any final external-reference gate.

## Physical results and limits

Common Q1/P1 fields use the previously declared1m rotation scale and floors.
The signed work difference is native minus external, divided by external work.

| Load | Work difference | Shell combined L2 difference | Beam combined L2 difference |
|---|---:|---:|---:|
| Fy | -1.046486% | 1.620194% | 1.299239% |
| Mx | -1.023869% | 1.274585% | 1.271050% |
| Mz | -0.843272% | 1.477839% | 1.319882% |

These single-grid quantities are not converged1% accuracy or locking evidence.
Important differences survive integrated physical recovery:

- Fy complete-interface Fx differs by **-70.416399N**, balanced by the opposite
  beam-ground difference. Overall equilibrium does not identify a unique partition.
- Mx complete-interface Fy differs by **-20.426552N**.
- Mx interior x=0.25..0.75 moment Mz is **10.527131Nm native**, **-0.562279Nm
  external**: difference **11.089410Nm**. This prevents attributing all mismatch
  to root localization. Do not hide it behind the displacement agreement.
- Mz complete-interface Fx differs by -7.677536N.

Historical [P0 comparisons](../r8-bl5-matched-comparison-20261001/refinement-v1-results.md)
remain separate frozen evidence. They are not affine oracles or a matched new
artifact performance/accuracy baseline. No affine-over-P0 flexible improvement
is claimed.

## Saved-state discriminator and resulting action

No model construction, factorization or new solve was needed. At every saved
station reconstruct the actual half-cell director and the common nodal P1 beam
rotation. In identity frames, physical channels map from native gaps as
`(-g_tx,-g_ty,-g_tz,g_dy,-g_dx)`; the same orthogonal map preserves multiplier
work. The actual saved Cq, recorded station Jacobians, and independently
integrated external hat rows verify the reconstruction across all five channels.

Actual native weak moments are below8e-22. Substituting common nodal rotations
gives moments up to1.44e-9/1.08e-9/1.47e-10 for Fy/Mx/Mz, while the external's
own common moments vanish within its numerical controls. The native-density
change in resisting constraint work is **-0.295405%, -0.840214%, -0.173933%** of
applied work. These are trace-work witnesses, not causal shares of stiffness error,
energy reduction or proof that P1 substitution is an admissible native variation.
The saved absolute-work field means sum of absolute support/channel contributions
after degree summation, not integral absolute station work.

Next bounded question: do mechanical/director approximation differences shrink
while the physical affine support space stays fixed, or do transfer partitions
remain unstable? Use **one finer Mx comparison**, 32x8 shells/64 beam intervals,
with the SAME eight support endpoints and all five channels. Explicit span8 is
required: the automatic growing-space rule would otherwise change the number of
supports and confound this discriminator. Compare trace-work witness, work/fields,
exact interior Mz and root partitions together. Decreasing trace discrepancy and
stable transfer would justify the required growing-space envelope; persistent
transfer discrepancy calls for focused force-stability/operator analysis.
One further grid would still not establish convergence. No sweep, channel tuning,
native director substitution, new norm or acceptance relaxation is authorized by
these results themselves; use existing bounded development authority and the
living note before execution.

## Resources, review and preservation

External children completed in0.402/0.392/0.416s; sampled peak process-tree RSS
34.2/42.1/40.4MB. Native completed4.514s/184.3MB; saved audit0.451s/56.6MB.
Single CPU affinity was verified while each Windows child was suspended before
execution; sampled numerical/unresolved start count was1. Threads requested1,
native BLAS/Numba effective1/JIT off. Limits were600s,8GiB external/1GiB small
native/audit,8 numerical threads, serial heavy execution. These samples do not
prove continuous maxima or effective external-library thread configuration.
No runtime or development-speed improvement is claimed.

[Independent Read review](review.md) resolved tooling/retention findings and
preserves the physical-transfer finding. This OpenAI scrutiny is not different-
family scientific acceptance. M2/F03, aggregate G0 and full release obligations
remain open.

[Raw manifest](raw-v1.json) binds81 explicitly whitelisted new files, including
native inputs/operators, complete references, saved-state audit, source/tests,
commands, resource records and retained warning logs. Archive658343bytes,
SHA256 `3c5aabd9db74e9e42ece6be737788a423c1c3964589d8ae4aa74f394d1fe0d48`.
No protected canary history or formal F03 runner was copied or executed.
All owned jobs and reviews TERMINAL; no run needs replacement.
