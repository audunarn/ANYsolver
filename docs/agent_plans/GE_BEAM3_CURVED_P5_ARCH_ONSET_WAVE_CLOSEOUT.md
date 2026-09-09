# P5 sampled lateral-onset refinement — research closeout

The single approved diagnostic wave completed. It demonstrates convergence
of the sampled lateral-onset location with mesh refinement, but does not
qualify GE-B3 or establish a rigorous first critical point. The 8- and
16-element searches stopped on uncertain midpoint signs and preserved their
last sign-separated brackets. No tolerance, uncertainty rule or interval
was relaxed to produce a result.

## Authority, execution and preservation

Frozen implementation: `8c31051076b0b3153dddfd9eb43e4fd3a833889b`, tree
`979fc4bfabe8a8b71f028edd86fa81a2769e39a8`, exact three-path successor of
`3d7dd492180f4d6658d832d5a71ca7a4a028aadb`. Runner file SHA-256:
`C373BEDD5EAFB788FFB3FFE09A8726712286733C2A28D4664412A415423E8F4B`.
The implementation, plan and all previous evidence were unchanged throughout
execution and the administrator's terminal verification.

Consumed request: `1b014e442280411a95c66e27502d0465`, 653 bytes, SHA-256
`A85B31728C3F16ECD13B495F33F9B56E86C1C6C339D87B7980B669B363D279BC`.
The resource administrator appended APPROVED before execution and
COMPLETED_PASS after independently checking raw byte/hash bindings and
resource termination. This is **resource accounting**, not independent
element-mechanics or spectral qualification. No request was retried or
reused. The exact stored command ran once, with acquire/release in `finally`.

External output remains immutable at:

`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-onset-20260906-4e2f54a71be94bb1ad3a0b5df77dad05`

It contains **102 files, 19,142,484 bytes**. The canonical sorted inventory
of relative POSIX path, byte count and SHA-256 has digest
`AC51C22AF56AE87F09ECD7CC72B4DCE0038BA2DEE63734B9306E57DC6686BE98`.
The inventory was calculated read-only in the task transcript; no new
inventory file was inserted into the frozen output directory.

The permanent consumed claim is
`C:\Github\.resource-manager\claims\ge-beam3-onset-1b014e442280411a95c66e27502d0465`.
Registered worker PIDs 31820, 39052 and 39676 were confirmed absent. The
resource lock was released and confirmed absent. Main remains
`09351645ba17a0a5b130a1c7a48007d36dd08ada`; this work modified no other repository.

## Bound outputs and resource results

| Record | Bytes | SHA-256 |
|---|---:|---|
| aggregate.json | 5160 | DBA974AA285EF1F25073FE3B539EEABDB6DC8627D96AFFAE6ABBCF1F8E62ED58 |
| inputs.json | 1589 | 83B4B16781B5E33F0BFB458008433BB283EAD4E07E0EE63908547E06D4A8C4EF |
| elements-04/complete.json | 10877 | EFA324D618ACF127DFC55134208C6F4F81746AF34FA0668F26C6E39D65B1CF0C |
| elements-08/complete.json | 10908 | 43DF5834126F0DC680E90E465EC305E0A80AA3CDC6E0310A3399CFCCE2E1C7A4 |
| elements-16/complete.json | 9228 | 65BBA86336FB56539E8828519C6A236A099A652993F5CC0A76E42C364A331E1E |
| elements-04/process.json | 100 | 28E055CAC80BBBCB93BFB73E940BB09A43C0F9A0C2A6E82EDDDAC083D077C0E4 |
| elements-08/process.json | 99 | CED8028C10C5E0E640865F725EB8FC4478A4B51D17D3A3F79735435AF666AB4D |
| elements-16/process.json | 99 | C4AE28076128A58384DCD4DD5B4CDF3F4964BF4ABD18A59C6E7742AB6845EAC9 |

All **82 raw trial records** (29, 29 and 24) are transitively byte/hash-bound
through their corresponding complete packet and the aggregate. Read-only
post-execution inspection recomputed the full/even/odd spectra, physical
checks, origins and deterministic search history and reconstructed the
aggregate comparisons. It did not reassemble an element, solve equilibrium,
rerun a worker or create replacement scientific evidence. The administrator
separately verified all 82 byte/hash bindings and complete packet identities.

All six worker stdout/stderr files are empty (SHA-256
`E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`).
Progress files, process-start records and every raw trial remain preserved.

| Elements | Raw states | Wall seconds | CPU seconds | Peak tree bytes | Exit |
|---:|---:|---:|---:|---:|---:|
| 4 | 29 | 30.1084261 | 29.8125 | 175403008 | 0 |
| 8 | 29 | 56.2812466 | 55.71875 | 180486144 | 0 |
| 16 | 24 | 93.4962116 | 93.0625 | 189407232 | 0 |

The serial worker span inferred from start records and recorded durations
is approximately **180.29 seconds**, not an independently measured total
coordinator duration. Every process satisfied its frozen envelope. The
largest physical check was `7.49484895345921e-12`, below `1e-11`. At most
three Newton correctors were used per state; maximum mixed evaluations were
60/120/240 for 4/8/16 elements, respectively.

## Scientific findings and retained uncertainty

The continuum endpoint drop interval remains
`[0.04564716575317947, 0.04564717069285733]`; corresponding recovered load
values are `[0.027747213792589615, 0.027747213018465982]`. Both frozen
interpolation-stride packets report these same endpoint coordinates; their
separately reconstructed transfer data remain distinct and bound. These are
observed numerical endpoints, not rigorous enclosures.

| Elements | Discrete drop endpoints | Load at endpoints | Relative drop error | Relative load error |
|---:|---|---|---|---|
| 4 | [0.036329574584960944, 0.03632965087890625] | [0.031958418891032445, 0.031958416959015024] | about -20.41% | about +15.18% |
| 8 | [0.04214431762695313, 0.04214447021484375] | [0.029073469708223897, 0.029073451051250365] | about -7.67% | about +4.78% |
| 16 | [0.044658203125, 0.0446630859375] | [0.028105447526341233, 0.02810472417562456] | -2.16655% to -2.15584% | +1.28845% to +1.29107% |

The fourth column says the discrete onset occurs too early in displacement.
These load values are evaluated at bracket endpoints; they do not imply
that load is monotone throughout the interval or rigorously enclose its
critical value. No new accuracy pass threshold is being applied retrospectively.

The 4-element search reached width `7.629394530722644e-8` and returned
`SAMPLED_LATERAL_SIGN_BRACKET_LOCALIZED`. The 8-element search retained width
`1.5258789062139178e-7`; the 16-element search retained width
`4.882812500002498e-6`. Both returned
`MIDPOINT_LATERAL_SIGN_UNRESOLVED`, not a failed process and not an exact zero.

At the uncertain 16-element midpoint, drop `0.04466064453125`, the lowest
scaled odd value was `-1.3014042410820745e-8`, within its uncertainty band
`1.5168748495185153e-8`. The retained endpoints remain sign-separated:
positive `2.2335871336779176e-8` versus band `1.5180939687932948e-8`, and
negative `-4.8360181206239975e-8` versus band `1.5166872322003458e-8`.
The growth of the conservative backward-error band with refinement is
visible rather than hidden by a smaller sign tolerance.

The canonical disposition is `RESEARCH_ONSET_DIAGNOSTICS_COMPLETE`, with
`accuracy_qualified=false`, `production_qualified=false` and
`first_critical_point_proven=false`. Finite sampling and numerical spectral
checks cannot prove a unique first continuum critical point, full dynamic
stability or general nonlinear beam qualification.

## Next engineering step

Preserve this consumed wave and prepare a separately tested explicit
refinement beyond the existing sixteen-element envelope if further onset
accuracy is pursued. Freeze the enlarged node/matrix/iteration/raw-schema
limits, validate small correctness cases and source identities, and request
a fresh contained resource run. Do not bypass current limits, rerun this
request or alter uncertainty rules to force a narrow bracket. A larger
mesh should be justified by this observed error, not adopted as an
unbounded convergence campaign.

Independent source/mechanics review, broad spatial and slenderness evidence,
nonlinear material parity, physical mass/dynamics, production restart and
interfaces, installed packaging and objective beam-shell connections remain
open. This closeout is documentary only; it changes no mechanics, defaults,
historical qualification evidence, version or release state.

NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
