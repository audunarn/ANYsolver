# Guided S3 right directional rates — development result

Implemented, source-tested and installed-tested. Scientific C6 acceptance and
release remain open. Starting commit `18ce7f6f567d8d025d38e55f44438af0d21d0250`;
the adjacent manifest/archive binds the actual uncommitted candidate bytes.

## Change and scope

Explicit `s3_one_sided_rates_dev=True` selects distinct constant/history profiles.
The existing guided elastic single-S3 fixed-plane owner now recovers the right
directional derivative of its affine penalty algebraic force at touch. A bounded
active-set solve preserves the physical mass projection. Acceleration distinguishes
closing, opening and stationary total gap velocity and includes structural
curvature. Singular/cycling/exhausted solves fail explicitly. No global convergence
or uniqueness claim follows. Arithmetic ties use 64 machine epsilon times their
operand scale, not the dimensional penetration tolerance.

Defaults, original profiles/fingerprints, normal force law, structural formulation,
mass model and commit order remain unchanged. Histories still require exactly zero
represented algebraic base force. Directional checkpoints reject old controls.
The example exposes the opt-in flag without changing default behavior.

## Verification actually run

All checks used Python 3.14.2, JIT off, numerical/Numba threads one, and explicit
180 s / 953 MiB supervision. The new focused source runner recorded runtime/source
imports and exact selectors. One installed artifact was checked after integration.

| Run | Outcome | Complete elapsed | Sampled peak process-tree RSS |
|---|---|---:|---:|
| Source v1 | 9 pass, 1 split-partition test failure | 7.620 s | 169586688 B |
| Source v2, failed target only | 1 pass | 7.211 s | 171544576 B |
| Source v3, new history target | 1 pass | 5.857 s | 168755200 B |
| Source v4, missing review checks | 5 pass | 6.122 s | 169463808 B |
| Installed coherent candidate | 17 pass, zero skips | 4.196 s | 157007872 B |

Independent checks comprise an exact two-coordinate unilateral force derivative,
multiple-constraint branch enumeration with nonorthonormal null basis/curvature,
explicit iteration exhaustion/nonmutation, and manufactured nonlinear structural
force expansion through the integrated helper. Public checks cover tilted impact,
physical Newmark motion, active-contact split restart, incompatible profile rejection,
history loading/eligibility, and injected rate failure with no endpoint commit,
manager cleanup and bit-identical fresh-model reuse. The installed ramped CLI
example also passes its stated gap/residual checks.

The first source split used a separately rounded `.011` end time: its clipped last
step differs by a few ulps from the uninterrupted accepted partition. Acceleration
parity failed by 1.741e-9. The corrected test uses the actual accepted time; its
1e-11 absolute tolerance is unchanged. This establishes parity on identical time
partitions, not arbitrary partition independence. No source law changed to repair it.

An initial installed command had two nonexistent selectors: no tests ran (exit 4).
Correct selectors were used once; the failed command/log is retained. Disposable
packaging setup also hit an existing fixtures directory and scoped Git ownership
check before building; setup repairs did not change product source.

Wheel SHA256: `4cabc275956f44e7d4c8033acb83bd8340ef2fe7f05a513053d95ec471f81424`.
All 448 source/wheel/site Python modules match. All 197 observed solver imports
are confined to the new installation. No runtime saving is claimed from different
source/installed timings.

## Independent scrutiny and remaining limits

Mistral completed a read-only kernel review with actual source reads and analytical
checks; no counterexample was found. Its separate integration attempt reached its
8-turn limit without a final assessment and is preserved as incomplete. Independent
OpenAI integration review found no definite defect and requested acceleration-mask
and public-cleanup checks; source v4 closes those specific coverage gaps.
Reviews do not establish scientific acceptance.
The [completed follow-up](review.md) checked the missing-test assertions and saved
installed identities/results and found no remaining consequential defect for this
bounded development disposition.

One guided elastic S3, one fixed plane, small-rotation geometry only. Event location,
incoming/outgoing interval traces and conservative integrated-path checks remain
open. The declared cubic Hermite reconstruction is not a general crossing
certificate. Legitimate massless rate jumps need not satisfy full-coordinate Newmark
kinematics; historical failures and criteria retain their original meaning.
General shells, beams, free bodies, moving tools, friction, nonlinear material
transactions, broad space/time qualification and full C6 remain required.

## Reproduction and retained evidence

Source commands: `scripts/run_portable_ci.py --development <recorded selectors>
--jit off --timeout-seconds 180 --memory-limit-mib 953`; selection/runtime/resource
records are retained in [raw-v1.zip](raw-v1.zip). Installed command and supervisor,
fixtures, wheel, manifests, complete logs/inventory/imports and reviews are also
retained. [Raw identity](raw-identity.json) binds each archived member; all members
were read back and hash-checked. [Resource records](resources.json) retain measured
counts/settings. Working package: `C:/ANYworkspaceWork/contact-directional-rates-package-20261001`.
Archive SHA256: `fc182d82a2cb22a0722c82168c9b9431391e688d676d1dcf7da857450c360431`.

Next: one independently solvable transition fixture to select interval-trace/event
handling before expanding the owner. Reuse unaffected tests; do not repeat consumed
native or historical activation campaigns. No communication with the other task.
