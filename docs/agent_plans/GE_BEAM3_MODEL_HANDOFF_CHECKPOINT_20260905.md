# GE Beam3 model handoff checkpoint — 2026-09-05

This note is a navigation aid for a successor model. It does not replace, amend, or reclassify canonical evidence. The hash-bound JSON records and the commits named below remain authoritative.

## Repository state

- Repository: `C:\Github\ANYsolver`
- Clean local `main`: `09351645ba17a0a5b130a1c7a48007d36dd08ada`
- Local `origin/main` tracking ref: `09351645ba17a0a5b130a1c7a48007d36dd08ada`; a live `git ls-remote` audit confirmed GitHub `main` at the same commit.
- Accepted GE-Beam3 work has not been pushed, merged into `main`, tagged, released, or published.
- None of the accepted GE-Beam3 branches exists on GitHub; the accepted state is local-only and therefore depends on the local branches and archive refs described here.
- Existing B2, legacy B3, qualified Q4, qualified S3 V2D, aliases, defaults, packages, dependencies, and workflows remain unchanged by P3/P4.

## Accepted straight standalone gate (P3)

- Branch: `codex/ge-beam3-dc-mixed-p3-optin-v1`
- Worktree: `C:\Github\ANYsolver\.perf2-worktrees\ge-beam3-dc-mixed-p3-optin-v1`
- Closeout commit: `7aa359c18d1cf5db3dfb84d364afd9870e2da994`
- Tree: `8e3bde1484c5291b2bb74e4f03071d3cf23e4600`
- Terminal: `PROVISIONAL_GO_GE_BEAM3_STRAIGHT_STANDALONE_OPT_IN`
- Qualified formulation ID: `GE_BEAM3_DC_MIXED_K1_MACRO_V2`
- Public selector authorized by P3: `ge-beam3`
- Canonical status: `docs/reference_cases/ge_beam3_mixed_p3_formal_status.json`
- Preservation ref: `refs/archive/ge-beam3-p3-straight-optin-accepted-20260905`

The accepted P3 candidate commit is `f63b2fc000c87003ae5c322dbd881e98f64b22ab` with tree `3402268699829119cc9f4abce711535323f84a4a`. Its accepted harness, package-authority, and performance-authority commits are respectively `1e37e7e19d21694e06934dd2075ce1c938e20f17`, `e85c8d558181e6fdd52a22008ea0911147abb0f9`, and `b843ba881eae78d0a349dd021ce1e7cf8bb567bf`.

P3 authorizes explicit straight-reference standalone use only. It does not authorize default routing, ecosystem exposure, version changes, tags, publication, curved-reference use, or beam-shell joints.

## Accepted private curved-reference gate (P4)

- Branch: `codex/ge-beam3-curved-p4-reference-v1-authority-c1`
- Worktree: `C:\Github\ANYsolver\.perf2-worktrees\ge-beam3-curved-p4-reference-v1-authority-c1`
- Candidate: `CANDIDATE_GE_BEAM3_DC_MIXED_CURVED_Q2_MACRO_V1`
- Closeout commit: `e59670ec1e69c0aba4e4027aaa271efa91e46b8d`
- Tree: `a55c7bdd2e4a431d4db275d30ba6fbd35d4890fa`
- Parent authority commit: `d306dcd6789a146f063a512a4a2e2c3b52f01d40`
- Terminal: `PROVISIONAL_GO_GE_BEAM3_P4_PRIVATE_CURVED_REFERENCE_CORE`
- Production restriction: `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`
- Preservation ref: `refs/archive/ge-beam3-curved-p4-reference-core-accepted-20260905`

P4 lineage, in order:

1. `5cf0fc884685b454ea645c2052c7cba60c66cbbb` — preregister reference core.
2. `214d6de76795bb7d656dc377166bd05cc35c6a3f` — add private reference core.
3. `d59ed224cabae23fac4ef68a74bc53ef5602b3db` — correct frame admission.
4. `8fcf827b6e5364f0e1bc8221a3f74602e3f39261` — accept corrected core.
5. `780991f7adea6fb4dc2da9fcdeca1d37379bf2ba` — freeze reference harness.
6. `20e895e8803de086b8abf19e3183e4d6a3b96fd6` — review harness.
7. `259fa6388106d67e76e80e8dbfd5409f6aeb5937` — add ledger-backed executor.
8. `4d3b398f71813fc1733a172c13e3831f48089a80` — review executor.
9. `d306dcd6789a146f063a512a4a2e2c3b52f01d40` — successful execution authority.
10. `e59670ec1e69c0aba4e4027aaa271efa91e46b8d` — accepted closeout.

Canonical closeout records:

| Record | Bytes | SHA-256 |
|---|---:|---|
| `docs/reference_cases/ge_beam3_curved_p4_scientific_result.json` | 1,298 | `91ABC1D1355E5F4450DD475B03720625A4840A19059521DA0E1622D9B90DFAFF` |
| `docs/reference_cases/ge_beam3_curved_p4_scientific_review.json` | 7,588 | `CF55C08DC4E91FC5E16CDD0928D58F038B7BF1B20F8C4A64D43CF1D4E5A02026` |
| `docs/reference_cases/ge_beam3_curved_p4_status.json` | 4,384 | `BD41BF63075CF7B03C9DA944E9D166F3C05539AF3CD55B9009AA060614FAC444` |
| `tests/test_ge_beam3_curved_p4_closeout.py` | 20,425 | `D2272C242EB2CE09FDA9B0A1AC742ACBED29B8817D5E835F35FC77C0602884E2` |

P4 verification at closeout:

- Full P4 suite: 163 passed in 27.65 seconds.
- Focused closeout suite: 31 passed in 1.04 seconds after the closeout commit.
- Independent scientific review: no P0/P1/P2 findings.
- Two fresh canonical cycles are byte-identical.
- Each cycle covers 26/26 obligations, six cases, and 144 stations.
- Cycle SHA-256: `CAC58A406F589DE0ADD09536A3567FC995A09A5CEA2833CB171AA124BA287123`.
- Proof SHA-256: `5A24120AFA220D4109F7C960693C99E1D6D67892A362E2BA366FA2FE77311A45`.
- Checker SHA-256: `90799C511EAAD7E3FCAE2CA0378724BB27F72428F3D1F1B30B543841EF749951`; both replicas are byte-identical in both cycles.

Important interpretation: each frozen cycle JSON intentionally retains `BLOCKED_GE_BEAM3_P4_REFERENCE_PROCESS_OR_EVIDENCE` in its nonclassifying `terminal` field. Its independently produced `diagnostic_checker_terminal` is `PROVISIONAL_GO_GE_BEAM3_P4_PRIVATE_CURVED_REFERENCE_CORE`. The C3 adjudicator, receipt, canonical result, independent review, status, and closeout test correctly use the diagnostic terminal. Do not reclassify the accepted P4 closeout from the cycle sentinel.

## Formal P4 execution chain

- Request ID: `173f5eb7c11f42518db832916705f74f`
- Attempt ID: `16413b7610f04ec4b19c0bb4f886ec5d`
- Request: 1,291 bytes, SHA-256 `93F899BAB7E8CAFFA49E507780BFE493570AF95F357A2106E72549C772096FAF`
- Claim and attempt: 748 bytes each, byte-identical, SHA-256 `E6201381D6F46A0BF6E01D92D9BBA2253B39B9E03954CD0A7AA9EEB3B8B001EA`
- Receipt: 1,362 bytes, SHA-256 `58CC8175A8F9001F712B03F36C6663700D5BD7DF1A0C7E415BEC764C3F09A48D`
- Canonical manifest: 416 bytes, SHA-256 `008FCBE76F4C3A5DC39EC48582EC6F9CAC23EC2ADC46DC27B7F70E9784B3C7A3`
- Lifecycle: `APPROVED` → `EXECUTION_STARTED` → `COMPLETED_PASS`.
- The request was consumed exactly once. Retry and request reuse are forbidden.
- External result: `C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-curved-p4-formal-16413b7610f04ec4b19c0bb4f886ec5d.result.json`
- External work root: `C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-curved-p4-formal-16413b7610f04ec4b19c0bb4f886ec5d`
- External work-root inventory: 21 files, 521,229 bytes, canonical file-row SHA-256 `F45A7FBA2DCE558230491A04E06931F7A3FE0FE3B4C88A816A0837FCAEAEF04C`.
- External authority manifest: 6,287 bytes, SHA-256 `13308601CA45CE5DB7CB8A32138ABB273560F1EF426F0763E45F59618D46F7F7`.
- Resource manager: `C:\Github\.resource-manager`
- The global execution slot was released in `finally`; no execution process remains.

## Preserved incidents

- Failed preclaim C5 is preserved at `refs/archive/ge-beam3-curved-p4-c5-preclaim-authority-incident-20260905`.
- Incident commit: `5befff866b25a31151c6d02106cc1b415587c33d`; tree `406c6fccbf31fed233a8d02eb2a38e9147f789f0`.
- Failed request `e562843ee0db4d9a8bc4ad97d04bb773` failed before claim/scientific execution because its `EXECUTION_STARTED` timestamp was serialized as locale text. It must never be rerun or reused.
- Request `d2683826f36948a288f43f97b07351e4` was canceled without execution because its approval note did not match the frozen template.
- Request `9db525f7b136474f890d4b3672b92d3a` was canceled without execution because its pre-bound start time elapsed before authority review.
- The two canceled requests produced no claim, attempt, receipt, work root, output, or scientific child and must never be reused.

## Exact next gate

P4 authorizes only preparation of a separately preregistered, hash-frozen, independently reviewed **private curved mixed-mechanics tranche**. Before any scientific execution, the successor must define and freeze its own potential/residual/tangent/condensation/state contract, independent checker, bounded runner, cases, terminal precedence, resource request, and execution review.

P4 does **not** authorize:

- execution of that successor before its separate authority;
- a public curved selector or export;
- serialization/restart exposure for curved mechanics;
- ANYfem or ANYstructure exposure;
- beam-shell joints;
- default changes;
- tags, releases, or publication;
- changes to accepted straight mechanics, B2/B3, Q4, or S3.

## Revalidation command

In the P4 worktree, use this checkout-neutral environment:

```powershell
$env:PYTHONPATH = 'C:\Github\ANYsolver\.perf2-worktrees\ge-beam3-curved-p4-reference-v1-authority-c1\src;C:\Github\ANYfileIO\src'
python -m pytest tests/test_ge_beam3_curved_p4_preregistration.py tests/test_ge_beam3_curved_p4_reference.py tests/test_ge_beam3_curved_p4_implementation_review.py tests/test_ge_beam3_curved_p4_formal_runner.py tests/test_ge_beam3_curved_p4_scientific_executor.py tests/test_ge_beam3_curved_p4_closeout.py -q
```

Expected result: 163 passed. A Windows pytest atexit warning about access to `pytest-current` may occur after a successful zero exit; it is not a scientific failure.

Do not add the active local ANYmesh checkout to `PYTHONPATH`; it may contain concurrent incomplete work. The accepted P4 run used the installed compatible mesher dependency.

## Transfer rules

1. Verify the two accepted preservation refs before changing any branch.
2. Treat the canonical P3/P4 JSON records as authority; this note is only an index.
3. Never amend, squash, cherry-pick over, or rewrite accepted evidence commits or archive refs.
4. Create the successor in a new dedicated worktree and branch from the accepted P4 closeout or its explicit reviewed successor authority.
5. Preserve bounded execution: one numerical-library thread per child, 24 GiB per process tree, 600-second child limit, at most three children, 1,800-second complete-wave limit, progress checkpoints, process-tree termination, and no automatic retry.
6. Keep the production restriction and all existing defaults unchanged until a later gate explicitly authorizes otherwise.
7. Raw formal evidence and the resource-manager ledger live outside Git. They are cryptographically bound by the committed review/status but must remain at their exact paths, or be separately archived under explicit authority, if the work moves to another machine.
