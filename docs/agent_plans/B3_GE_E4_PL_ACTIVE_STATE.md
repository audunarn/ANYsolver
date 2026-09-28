# B3-GE / E4-PL / B2 active state

Updated 28 September 2026 for Revision 7. This is the short working record. The
prior full version is preserved in Git at 69224fba; the historical checkpoint,
complete programme, registrations, failures and evidence retain their meaning.
ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1 applies prospectively.

## Decision sought

Deliver the experimental multi-element point-connected GE/B2 workflow while
resolving a defensible six-channel native line law and growing multiplier space.
G0B/F03 remain open; G1 acceptance and production qualification are barred.
Formal F03 execution authority is unconsumed. There is no release or speedup
claim. The factor-4 Fy fallback script remains dirty and unrun.

## Delivered behavior and evidence

- ANYsolver commits d2b05423 and a2bc9a3f provide the sparse GE development
  owner: multiple Q4/S3 shells and native B3 members, point connections,
  retained variables, reference-linear and short finite elastic solves,
  reactions, atomic stepping, cancellation, checkpoint/restore and continuation.
  Eligible unchanged reference-linear cases reuse one factorization.
- The separate B2 development profile handles compatible 1/10/100 loads with
  selected recovery and factorization reuse. Bounded Q4/B2 point-panel and
  dense-oracle parity exist. Wider B2 conditioning, mass/prestress and scale
  qualification remain open.
- ANYfem commit c7035a7 provides a separate experimental GE-panel format,
  save/reopen and headless restore/continue. Ordinary project formats retain
  their existing route.
- Development installed wheels have SHA-256
  E7BA4EF774558C5AB0D666810B96C2F722816269ADF0971CD53C37EEB23C8D7E
  (ANYsolver) and
  C7E9D005DFEDDDC6D23C1D6757E29B3F314A7E94F614C98E0EEA76C87236D467
  (ANYfem). Actual installed imports passed 40 solver and 3 consumer checks;
  23 focused source checks passed. Windows/Python 3.14.2, one OpenBLAS thread
  and NUMBA_DISABLE_JIT=1 were effective. Wheel bytes, build/install/test logs,
  imports, dependencies and manifest are preserved under
  .qualification/b3-ge-e4-pl/r7-integration-dev-20260928-v3/.
  These development wheels do not satisfy G6.
- Reference equilibrium is screened by tangent-relative, unit-covariant
  residuals per element and after assembly. This is a roundoff screen, not
  an absolute physical force limit or G0 stress-free qualification.

## Mechanics uncertainty and next discriminator

The saved off-ratio Fy/rotation diagnosis showed alternating force/couple
cancellation. A smooth loaded Fy pair passed supported equilibrium but did not
excite that least mode or select a law. The factor-5 CalculiX Fy run timed out
without a physical result. Historical classical axial, Q6/finite-pad, F5 and
native six-channel references remain distinct. Do not launch the prepared
factor-4 fallback merely because it exists.

The private L1 probe uses an objective reference-offset SO(3) Log pose gap,
physical E4 projected-tangent/director trace and retained B3 half-cell port.
Its reference, first-variation, objectivity and chart checks pass. Composed
Hessian, integrated line work, physical transfer and multiplier stability
remain open. Its shell-frame translation differs from the saved candidate's
beam-frame translation; constrained zero sets can agree while multipliers and
off-constraint work differ. The law must be chosen and derived.

The independently read-only reviewed prospective draft at
docs/agent_plans/B3_GE_E4_PL_G0_F03_PROSPECTIVE_ASSESSMENT_DRAFT.md states
prerequisites for a reference-relative compliance test: physical stationary
reduction, positive supported work, exact gauge, same-law converged reference
and work-preserving action injection. Its reference, numerical floors and
thresholds are not frozen; formal F03 assessment is barred. Rank or one
quotient cannot select a multiplier space.

Next: derive and verify the chosen translation-frame work and full curvature;
then conduct one bounded theory-led multiplier design and targeted comparison.
A matched all-shell flat-bar/T CalculiX reference first needs a folded-web
deck, partitioned action/work parser and matched Fy/torque loads. Proceed with
independent F01-F13 and GE/B2 lifecycle work that does not depend on this
decision. Preserve all seven ratios, growing spaces, three refinement levels,
physical transfer/locking and the registered G0-G6, F01-F13, V01-V28 and
B01-B18 scope. None of F01-F13 is fully accepted yet.

## Execution boundary

Revision 7 permits experimental integration during open G0, at most three
workers and one heavy numerical job at a time. New bounded diagnostics may use
at most 100,000 rows, 600 seconds, 8 numerical threads and 8 GiB per process
tree after verifying effective settings. Historical one-use executions are
not replayed. The complete release still requires the external references,
practical scale, installed-platform checks and independent acceptance.
