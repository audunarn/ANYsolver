# Native generalized tangent-resolution incident

Initial unfrozen rehearsal: 22 passed, 1 failed. The failure was
test_actual_directional_tangent[True-True], after both coarse central
differences exceeded the unchanged 1e-7 directional acceptance threshold.
The initial curved-plastic transaction smoke passed all six plastic components.

Initial result directory:
`C:\Users\AUDUNA~1\AppData\Local\Temp\ge-beam3-native-generalized-rehearsal-cj6yl35d`.
Supervisor exit 1; 105.25869209999655 seconds; zero job descendants.
All five initial source files were copied and hashed before any correction.
Their manifest and the failed raw evidence accompany the final archive.

A separate disposable resolution diagnostic completed once in a fresh path:
`C:\Users\AUDUNA~1\AppData\Local\Temp\ge-beam3-native-generalized-resolution-diagnostic-6bo55zvd`.
It used the unchanged implementation, fixture, state origin and direction.
Supervisor exit 0; 36.08806029999687 seconds; zero job descendants.

| Central step | Normalized derivative error |
| --- | ---: |
| 2e-5 | 6.131893260264411e-7 |
| 1e-5 | 1.5330454992144692e-7 |
| 5e-6 | 3.826536241867727e-8 |
| 2.5e-6 | 9.580794158928314e-9 |

The errors decrease by approximately four for each halving. Independent
Richardson combinations (4 D(h/2)-D(h))/3 give errors
1.8009886652698835e-10, 2.2175372878402207e-10 and
1.2069274454024579e-9. This supports central-difference truncation as the
cause of the failed coarse resolution, not a constitutive/tangent correction.
The conclusion is limited to this diagnostic; it is not full qualification.

One reviewed-in-turn pre-freeze test-resolution correction retains every
original coarse derivative, adds two finer steps, and requires both fine raw
derivatives plus all extrapolations to meet the same 1e-7 tolerance. Any coarse
failure also requires the observed second-order convergence ratios. No fixture,
mechanics, material, load, state, equation, internal-solve tolerance or production
source is changed by the correction. Independent review remains pending.

The initial attempt stays classified as failed and is not replaced or counted
as a passing cycle. There was no automatic retry. Only after the diagnostic
and explicit test correction may a new complete rehearsal be run and frozen.
