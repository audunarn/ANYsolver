# E03 coarse B2 feasibility screen — adapter implemented, unverified

This screen fixes `build_case(0, 1)`: level 0, positive eccentric offset,
`B2_E4_PL_FAST_LINEAR_V1`, one native job and one external job only if separately
authorized. Each call finishes exactly one requested phase in its own fresh
evidence directory. There is no automatic paired execution, retry, refinement,
sign sweep, mapping review or accuracy scoring. Native and external observables
are provisional. Full E03, GE point correspondence and converged accuracy remain
**OPEN**. This preparation grants no numerical execution authority.

`scripts/r8_e03_coarse_screen.py` reuses the existing E03 builders, native adapter
and strict CCX parser. It supplies `prepare_screen` and `finish_screen` only:
no CLI, subprocess, process supervisor, test runner or new resource framework.
It was written and inspected as source only; it has not been imported, collected,
executed or tested. The preceding 56 source + 56 installed controls cover the
existing E03 candidate, not this new runner.

## Caller and supervision boundary

The source-prepared **root-owned physical execution adapter** is adjacent
`entry-v1.py` and `supervise-v1.ps1` under
`.qualification/b3-ge-e4-pl/r8-e03-coarse-dev-20261007-v1`. Root owns all execution.
The caller must supervise each native/CCX
process tree with the existing resource services, retain raw output on timeout
or failure, record precise process-wall duration and cumulative budget, and
provide the actual effective settings and resource evidence. Neither a caller's
`supervisor_id` nor receipt field validation proves supervision occurred. These
functions validate provenance supplied by that caller; they are not a process
safety guarantee or an execution authorization mechanism.

Root recorded the user's subsequent “Proceed” in adjacent root-owned
`authority-v1.json` and `ledger-v1.json`:240s aggregate,30s aggregate controls,
one native phase capped60s and one external phase capped60s after native
finalization succeeds, retaining60s for final verification. The worker has
launched nothing. No prior authority is reused. Do not substitute an unsupervised
shell call.

## Concrete deferred call contract

After separate authority, the root adapter invokes the following functions from
the declared source checkout. It may hash/read and prepare the input before the
physical process. All identities are explicit caller inputs, never guessed:

```python
from scripts.r8_e03_coarse_screen import prepare_screen, finish_screen

attempt = prepare_screen("native", native_evidence_directory, bindings=native_bindings)
# Existing caller supervisor runs exactly one installed native child below.
# The child calls scripts.r8_e03_native_reference.execute_b2(case), where case
# is the exact saved case.json, then serializes its detached result as JSON.
native_observables = finish_screen(attempt, receipt=actual_native_receipt,
    raw={"stdout": stdout_bytes, "stderr": stderr_bytes,
         "native_result": native_json_bytes})
```

For an independently authorized external phase:

```python
attempt = prepare_screen("external", external_evidence_directory, bindings=external_bindings)
# Caller supervisor uses cwd=attempt and the exact argv below, once only.
external_observables = finish_screen(attempt, receipt=actual_ccx_receipt,
    raw={"stdout": stdout_bytes, "stderr": stderr_bytes,
         "frd": frd_bytes, "sta": sta_bytes})
```

The only permitted external solver argv is:

```text
C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/calculix-223/CalculiX-2.23.0-win-x64/bin/ccx.exe -i e03
```

It has **no `-o` option**. Preparation and finishing both hash the pinned binary
against `27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f`.
The actual solve stdout must contain version **2.23**, matching the receipt;
a separately fabricated or probe-only version string is not permitted.
The root adapter must attest the actual command's working directory is the
prepared attempt and that the exact saved `e03.inp` was the input.

Bindings are a JSON object containing:

* `phase`: exactly `native` or `external`; `case_id`: the exact `build_case(0,1)` digest.
* `source_root`: absolute checkout path; `source_sha256`: exact SHA256 map for
  `scripts/r8_e03_coarse_screen.py`, `scripts/r8_e03_curved_reference.py`,
  `scripts/r8_e03_native_reference.py`, `scripts/r8_e02_double_output.py`, and
  `scripts/r8_e02_rigid_tip_reference.py`.
* `wheel_path`, `wheel_sha256`: the exact already verified 431-module wheel.
  The fixed hash is `fa5507fe14cc09949743adb7d5ae340a2499d9b813d6b80a1b7d4ea414267e82`.
* `module_manifest_sha256`: explicit identity of the existing frozen
  `.qualification/b3-ge-e4-pl/r8-e03-curved-source-dev-20261007-v1/inputs-manifest-v1.json`
  under `source_root`. Its 431 `source_modules` and `reused_wheel_sha256` are reused.
  The small parity logic from that directory's `entry-v1.py` compares exact
  source, wheel and installed Python payload maps; no solver is imported for
  this comparison. Existing builder/adapter/parser hashes must match its inputs.
* `installed_provider_root`: exact existing installed directory, required for
  either phase to preserve source/wheel/site payload parity. Exact wheel/site
  paths are supplied by the existing
  `.qualification/b3-ge-e4-pl/r8-consumer-capabilities-dev-20261007-v1/artifact-v1.json`.
* `supervisor_id`, `execution_scope`: nonempty root-owned identities for this
  attempt; `command`: exact argv array for the supervised phase.
* Native: `native_capability_law`, the explicit root-adopted expected law identity
  of the existing B2 adapter; the runner does not choose a different law.
  External: `executable_path`, exactly the pinned path above, and `command` exactly
  `[str(CCX_PATH), "-i", "e03"]` (forward slash spelling).

The actual receipt must repeat `phase`, `case_id`, `supervisor_id`,
`execution_scope`, `command`, `wheel_sha256`, `source_sha256`, and
`module_manifest_sha256` exactly. It also
requires `deck_sha256`, `exit_code` (integer), `timed_out` (boolean), finite
nonnegative `process_wall_seconds`, and `resource_receipt_path` plus
`resource_receipt_sha256` for the caller's retained actual resource record.
The latter record must include exact command/cwd/input identity, effective
runtime, exit/timeout, precise duration, cumulative budget used/remaining, and
limits; this content is reviewed by root, not interpreted by another service here.

Every raw item has a corresponding `<name>_sha256` receipt field.
Native additionally requires `anysolver_origin` and `anysolver_origin_sha256`,
the actual child package import origin/hash inside `installed_provider_root`.
The origin must be `anysolver/__init__.py`, with receipt and actual file hashes
matching the existing module manifest. The native child must import the adapter from
the bound source checkout and ANYsolver from the verified installed provider.
External additionally requires `executable_path`, `executable_sha256`,
`version="2.23"`, `frd_sha256`, `sta_sha256`, `stdout_sha256`, and `stderr_sha256`.
These names match `parse_result` exactly. Complete single-increment STA and
DOUBLE FRD validation remains delegated to that parser.

Native JSON must contain the exact completed B2 status/case/level/sign, positive
finite work, the existing scaled balance at most `BALANCE_LIMIT=1e-8`, two distinct
rib 0/1 six-component physical tip poses, a six-component common-origin root
wrench, the bound capability law and both complete six-component native
multiplier/gap row sets for the eight declared point identities. Their existing
coordinate labels remain explicit; these row components are not spatial wrenches.
The existing bounded finite JSON validator detaches native output and receipts.

`finish_screen` saves received bytes before status/parser checks, including failed
or timed-out receipts. If a raw file is absent on failure, pass empty bytes and
the actual failure receipt; never invent a completed record. Each attempt can be
finished once. A refusal preserves received output, resource bytes when readable,
raw receipt and `failure.json`, then raises. Success saves detached provisional
`observables.json` and an explicitly unqualified `outcome.json`; no comparison
or accuracy verdict is produced. Preserve a failure and investigate it rather
than reusing its directory or automatically retrying.

## Root execution commands and retained limits

Prepared commands for root after source review, unexecuted at this handoff:

```powershell
& ./.qualification/b3-ge-e4-pl/r8-e03-coarse-dev-20261007-v1/supervise-v1.ps1 -Mode controls -Attempt controls-v1 -Cap 30 -Reserve 60
& ./.qualification/b3-ge-e4-pl/r8-e03-coarse-dev-20261007-v1/supervise-v1.ps1 -Mode native -Attempt native-v1 -Cap 60 -Reserve 60
& ./.qualification/b3-ge-e4-pl/r8-e03-coarse-dev-20261007-v1/supervise-v1.ps1 -Mode finalize-native -Attempt native-finalize-v1 -PhaseAttempt native-v1 -Cap 30 -Reserve 60
& ./.qualification/b3-ge-e4-pl/r8-e03-coarse-dev-20261007-v1/supervise-v1.ps1 -Mode external -Attempt external-v1 -Cap 60 -Reserve 60
& ./.qualification/b3-ge-e4-pl/r8-e03-coarse-dev-20261007-v1/supervise-v1.ps1 -Mode finalize-external -Attempt external-finalize-v1 -PhaseAttempt external-v1 -Cap 30 -Reserve 0
```

Run serially from the declared checkout and inspect each exit/receipt. The
supervisor reuses the E03 source-entry watchdog and precise outer accounting:
CPU0, frozen thread environment1, JIT off,2GiB process tree, one job. Physical
primary tokens are persisted as consumed before launch; launch failure grants
no retry. Controls repairs share30s aggregate. Only finalize-external may consume
the final60s reserve; all modes still share240s cumulative.

Outer `execution.json` exists only after child exit, so finalization is a separate
bounded invocation. Actual completed outer receipts, input/artifact hashes,
before/after runtime, actual loaded origins and resource records are validated
before writing provisional success. Finalization refusal preserves all physical
raw files at the original attempt and writes `finalization-failure.json`; parser
refusal also preserves its `received` inventory. No outer timing or physical
success is synthesized. External launch requires matching controls PASS and
successful native finalization. Both finalized phases are required before
examination of paired coarse evidence.

CCX configuration requires inherited frozen thread environment, observed CPU0
and actual solve stdout `Using up to N cpu(s)` declarations all equal to1.
Missing/conflicting declarations explicitly refuse configuration. OS threadcount
observations remain diagnostics. The watchdog alone does not prove settings.

Static parametrization prepares **33 synthetic controls**: phase/binding refusal,
source and child-origin hashes, case/deck mutation, failed receipts, partial native
observables, malformed raw output, evidence preservation and detached results.
They invoke no native solve or CCX. Neither collection nor execution has occurred.
The unchanged431package modules reuse the verified wheel; no package build is
needed. Root reviews frozen snapshots/manifest and launches all approved checks.

The principal question is whether both routes complete at this fixed coarse case
and yield inspectable finite work, tip and common-origin reaction observables
under their declared fitted-port work maps. A completion permits examination of
that bounded feasibility evidence. A refusal, timeout or resource limit stops the
affected phase and retains its evidence. Neither outcome establishes physical
accuracy, adopted native/external mapping, GE correspondence or converged E03.
Source review and root-run focused controls remain prerequisites. Missing runtime
evidence remains a refusal; it does not authorize weaker criteria or a physical
retry. Full E03 acceptance remains open.
