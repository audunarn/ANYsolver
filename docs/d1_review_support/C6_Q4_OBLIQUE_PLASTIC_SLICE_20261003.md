# Manufactured contact-driven Q4 plasticity — development evidence

3 October 2026; parent `a2b142a1`. Final source content, raw diagnostics and
environment identities are bound in `contact_c6_q4_oblique_plastic_20261003`.
Implementation/source/isolated installed testing, not engineering acceptance or
release. The accepted shell artifact and historical defaults remain unchanged.

## Independent mechanical discriminator

Unit square x,y±.5m,h.05m,E1e9Pa,nu.3,rho1e4kg/m3,constant DNV plateauY.2Pa.
Midsurface motion is `u=(epsilon*x,-epsilon*y,w)`, zero rotations. Initial epsilon,
its rate and all material history are zero; normal velocity is−1m/s. The plane has
normal `(sin2e-5,0,cos2e-5)`, point z−.0008m,kn4e11Pa/m,gapbudget5e-5m. Scales
are manufactured, not an engineering material recommendation.

Exact independent reference quantities:

- Masses `M_e=rho*h/6=83.3333kg m²`, `M_w=rho*h=500kg`.
- Q1 nodal support1/4; weighted x=±1/6m, not the physical corner±1/2m.
- `g_i=n_z*(GAP+w)+n_x*x_i*(1+epsilon)`; reaction derives from the same nodal
  penalty potential, preserving its complete epsilon/w cross terms.
- Pure deviatoric membrane stress `tau=clip(2G*(epsilon-p),±Y/sqrt3)`;
  generalized membrane reaction `2*volume*tau`,alpha increment`2abs(dp)/sqrt3`.
- Reference Newmark uses independent enumeration of4 pressure-group subsets ×3
  material branches, solves each affine2x2 system and checks inequalities/residual.
  It calls no production contact, material, structural assembly or solver kernel.

Local production mass/structural/contact work agrees with these formulas. Dynamic
comparison checks both coordinates, velocities, all12 plastic core entries and
separate modal equilibrium. Scales5Nm and1.5e7N prevent large normal reaction from
hiding tiny membrane excitation. Production equilibrium tolerance1e-13; no
mechanical law or numerical scientific gate was weakened. Plateau boundalpha<.005
is checked in saved data; the test and public diagnostic guard that assumption.

The independent no-contact reference has identically zero membrane motion/history.
Production precontact membrane motion is checked; there is no separate complete
production contact-free run. Global energy is dominated by250J normal kinetic
energy and cannot establish the tiny coupling/plastic work.

## Results and retained failure

| Record | Actual outcome |
|---|---|
| `contact_q4_oblique_local_a_20261003` |Local mass/work/physical-gap formula passes |
| `contact_q4_oblique_integrated_b_20261003` |All intended mechanics/core checks pass before extra zero-cutback assertion fails;1failed/1passed retained |
| `contact_q4_oblique_integrated_c_20261003` |2 coupled/reference outcomes pass;83.00s fixture,86.64s pytest |
| `contact_q4_oblique_diagnostics_d_20261003` |New callback cause/count and2 affected controls pass |
| `contact_q4_oblique_half_e_20261003` |2 half-step coupled/reference outcomes pass;139.82s fixture,143.48s pytest |
| `contact_q4_oblique_compat_f_20261003` |Typed cutback diagnostic plus elastic event/restart controls pass |

These are5 physical/reference outcomes,2 diagnostic outcomes and4 affected
controls through scoped selections, not one whole qualification suite. Every
successful runner uses reconciled imports,JIT off,Numba/BLAS threads1,180s/953MiB.
The zero-cutback expectation was an extra test assumption, not a scientific gate.
Bounded cutback is authorized; rejected work and original failed outcome are kept.

Coarse dt3e-5s,end.003s:104acceptedsteps,4 events,1cutback,132endpoint requests,
567stage evaluations. First yield.0008933632225s while contact active. Final
p_xx−1.282989468e-8,alpha1.481468629e-8,minimum physical represented gap−4.52339e-5m
within5e-5m. Maximum normalized modal residuals1.89e-13/2.24e-15; reference coordinate
errors9.33e-20/6.51e-19. No claim of general floating accuracy follows.

Half dt1.5e-5s has the same endpoint:finalp_xx−1.240267338e-8,alpha1.432137363e-8.
Plastic strain/alpha changes3.44459%,membrane coordinate3.40340%. Modal residuals
7.64e-14/2.67e-15. Total-energy defects1.18e-7/8.78e-8 are small but cannot prove
membrane work accuracy. These two levels do not establish temporal convergence,
the representative2% accuracy gate or formal impact acceptance.

## Targeted diagnostic and installed handoff

Cutback occurs atcoarse t.00078s,h3e-5s after14callback requests/53stage evaluations.
Old helper labeled any callback ValueError as invalid gaps. A bounded33-step replay
shows the actual cause: endpoint-family equilibrium did not converge within its
existing Newton limit. Its corrected diagnostic is retained. It is not material
failure or an admitted cap increase; recovery still uses one committed parent.
Half-step also recovers one non-equilibrating endpoint trial.

`cutback_diagnostics` appends time,duration,reason and cumulative plane work at each
rejected attempt. Failure reason resets per attempt. Typed endpoint cutbacks retain
their diagnostic cause and actual callback units; malformed vectors stay distinct.
No force/inertia/material/restart equation changes. Result tuples contain owned
mutable dictionaries, not deeply immutable state.

Source/installed example matches all205 imported module hashes and numerical fields.
WheelSHA256 `fbffc76ee0cd57d5ac932ba048556fc1112a673ab4ea54ac91670e653a1d5535`.
Source85.377s/170393600B,installed78.801s/170258432B under existing limits. Single
runs are not balanced performance evidence. Artifacts:
`C:/ANYworkspaceWork/contact_q4_oblique_package_20261003`.

Read-only same-family scrutiny found no concrete defect in work/branch/scaling or
diagnostic changes. It identified the plateau guard and counterfactual/energy/
temporal-claim limitations now explicit above. No independent execution or
engineering acceptance. Full C0–C9 remains active; native friction's separate
closed-strip tangent NONPASS and consumed run restrictions remain unchanged.

Next discriminating action: cheap independently checked continuous affine-branch
reference with material/contact events and bounded numerical error. Determine
temporal accuracy before another expensive shell solve; no open-ended dt campaign.
