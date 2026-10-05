# Paused completion-sensitivity discriminator

User paused feature development on1 October for coordinated testing-regime work.
No active owned process or numerical reservation. Formal F03 remains unconsumed.

Current diagnostic source: `scripts/b3_e4_bl5_completion_sensitivity_dev.py`.
It has source-level independent review, not numerical acceptance. The exact
historical coupled n64 Mz fixture is unchanged, with8940q/160rows and wheel
`0c45666609355e654cb726a0e4e0780d386bccfaafef1209ffd994bdd3b9d09c`.
No product coefficient/law/mesh/tolerance changed.

V1 performed one KKT factor and passed mapped core+PL+hourglass reconstruction
before failing an inapplicable external-load active-row test on the manufactured
derivative RHS. Source `be7eb0f008974aad72d9970b906038c9bfa5b2caceed4113dccd267482d682ca`.
Independent review explains why componentwise backward error and frozen upper
physical-work norm are appropriate, preserving the original baseline physical
gate. V1 stays failed. All raw solve/derivative arrays are preserved.

V2 reuses exact V1 hashes and performs no assembly/factorization. It also FAILED:
componentwise backward error `2.4487812109162483e-8` exceeds its unchanged `1e-8`
criterion. Upper work ratio `6.4279826714833586e-15` and original physical-load
reference `1.6133227976067199e-16` pass. No derivative/causal acceptance follows.
Do not report the provisional sensitivity as accepted or loosen a threshold.
The precise remaining numerical obstruction is this componentwise backward error.

Raw working directories:
`C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-bl5-completion-sensitivity-20261001-v1`
and the corresponding `-v2`. Adjacent archive/inventory preserve both consumed
runners, resource records, raw arrays and failures. On authorised resumption,
inspect the retained error distribution before deciding any affected numerical
repair; do not automatically rebuild the fixture or start a mesh sweep.
