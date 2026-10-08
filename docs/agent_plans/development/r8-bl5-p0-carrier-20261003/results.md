# Finite P0 carrier reference — 3 October 2026

**Decision:** retain BL5/c2 for development. This fixture's dominant transfer
discrepancy is finite weak enforcement versus continuous restraint, rather than
the native beam approximation. The causal discriminator is complete; no new
native solve, fourth grid or formal F03 run occurred. M2 remains unaccepted.

## Matched physical question

Reuse the saved one-metre rigid carrier, uncoupled EI_z=1.75e6 Nm²,
kGA_y=646153846.1538463 N, eccentric arm−.05m, both beam-end uy fixed,
root normal spin free and tip Mz=10Nm. This is normal-spin bending, **not
Saint-Venant torsion**. A released normal spin does no direct normal-couple work.

The new reference constrains the exact saved finite P0 means, instead of replacing
them by u(x)=0. Independently integrate V'=−p, M'=−V, phi'=M/EI and
u'=phi+V/kGA with constant p on each actual support. Enforce integral(u)=0,
u(0)=u(L)=0, M(0)=0 and M(L)=10. A bounded support-count-plus-two system
determines phi(0), V(0) and p_i; no native element or global mechanical inverse.

| Saved grid / supports | Native vs same-P0 tip | Native vs same-P0 force moments 0–3 | Same-P0 vs continuous-tie force moments 0–3 |
|---|---:|---:|---:|
|16x4 /8|+1.0113%|+0.6905 to +0.8198%|−24.1185 to −28.0270%|
|32x8 /16|+0.3354%|+0.2548 to +0.2946%|−8.6777 to −10.0960%|
|64x16 /32|+0.0912%|+0.0769 to +0.0883%|−2.5773 to −2.9992%|

The two factors multiply to the previously saved native-versus-continuous-tie
transfer discrepancy (finest−2.5023 to−2.9135%). At the finest grid the same-P0
tip differs from the strong tie by only+0.00929%; small tip agreement again
does not establish transfer accuracy. Native-versus-P0 combines beam
discretization/formulation effects; this comparison does not separate those two.
Finest root reactions1.65758e−6N(native) versus1.68706e−6N(P0) remain near-zero
quantities requiring an absolute/applied-force scale, not a primary relative test.

## Checks and source

Reference source a32c2cc0. Ten focused new/existing reference tests pass:
independent one-support algebra, equilibrium/constitutive derivatives, continuity,
energy/work, means, signs, equivalent units, invalid inputs and owned definitions.
A separate60-digit quartic-displacement formulation with continuous u/phi/V/M
checks finest root/tip/densities. Scaled condition reaches195,294; finest physical
controls≤3.5e−15. Precision corroboration is not a general forward-error theorem.
P01 effective pools1;119,451,648B sampled peak;2.56s supervised,1.50s pytest.

Initial multidimensional field-axis error caused3failed/4passed; corrected by
moving only the component axis. Direct-script import failed once after adding
the strong-tie comparison; repaired explicit package/direct execution imports.
Failed and repaired logs are retained. OpenAI Read review found no actionable
equation, sign, comparison or precision-control defect; reviewer launched no jobs.
This is development scrutiny, not different-family scientific acceptance.

Reproduce without a native solve:

```powershell
$env:OPENBLAS_NUM_THREADS='1'; $env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
C:/Python/Python314/python.exe scripts/r8_bl5_p0_carrier_reference_dev.py --saved-evidence docs/agent_plans/development/r8-bl5-rigid-carrier-20261002 --output <new-output.json>
C:/Python/Python314/python.exe scripts/run_portable_ci.py --development tests/test_bl5_p0_carrier_reference_dev.py tests/test_bl5_rigid_carrier_reference_dev.py --timeout-seconds 600 --memory-limit-mib 1024
```

Saved53-member archive SHAcd5116af...600f6b is unchanged. Only nine explicitly
named summary/transfer/state members are read, with member/archive hash checks.
[Comparison outputs](comparison-v1.json) and [new raw checksums](raw-v1.json)
preserve source, checks, failures and review; historical evidence is linked.

## Resulting action

Close this causal investigation **within the fixture**, retain its strong-tie
accuracy failure, and stop isolated carrier refinement. When developing the
production resolution rule, account for physical transfer length scales and
finite weak enforcement; do not tune separate channels or infer policy from
tip response alone. A changed complete support rule needs its own physical and
stability checks. Required flexible-carrier, coupled torque/shear, ratios,
mixed-system, external and wider mechanics evidence remain open. No tolerance,
law, multiplier policy, qualification or release authority changed.
