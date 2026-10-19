# Native potential-flow development contribution

`marine_potential_flow_development_v1` provides full coupled added inertia,
incremental restoring, declared baseline, single harmonic excitation and direct
fixed-grid radiation convolution through the existing native mechanical solver.
It admits **development fixtures only**. Physical BEM/source admission, formal W4
acceptance and ANYmarine GUI/persistence fluid admission remain pending.

Base import uses NumPy and the public native contribution/coordinate APIs only.
`PotentialFlowDevelopmentData.from_radiation_kernel` optionally consumes the
public ANYhydro `RadiationKernel`; no private widgets or hydrodynamic functions
are imported. A kernel's hash is retained, its unqualified status is not changed.
Full body/DOF order must match the declared frames. Arrays are immutable copies.

Declare the exact equilibrium frames/hash, force basis `equilibrium_h_gradient`,
hydrostatic role `incremental_buoyancy`, excluded gravity, zero prehistory and
positive body translation/rotation bounds. Baseline and stiffness are separate.
Unknown physical-wrench semantics, full hydrostatics, included gravity and real
BEM source labels are refused. The exact frame hash binds the declaration, not
backend geometry evidence. Changed geometry requires regenerated bound data.
These declared bounds and the principal-log guard do not qualify BEM validity.

For `h=h(q)`, `D=dh/dq`, the contribution assembles external
`D.T*(baseline-C*h+Re(X*exp(-i*omega*t))-R)-D.T*Ainf*hddot`.
All residual tangents are total analytic partial derivatives, including geometric
acceleration and force/radiation follower terms. Matrices remain fully coupled;
no symmetry repair, diagonalization, PSD claim or double inertia bias is applied.

`R(t)` integrates `K(lag)*hdot(t-lag)` by trapezoidal weights on the exact solver
grid through `min(t,kernel_duration)`. At t0 the integral is zero. Step1 seeds t0
velocity from the actual accepted state in `StepInformation`, never an initial
trial or a preparation counter. Later steps require contiguous accepted history
with matching dt and last accepted velocity. Keep the last `n_kernel-1` samples
in fixed equilibrium coordinates; rechart leaves them unchanged. Only the owner
commits a successful normal step. Abort, rejection, cancellation and initialization
cannot advance memory. The current endpoint coefficient is `dt*K(0)/2`.

Diagnostics separate reference baseline, incremental restoring, excitation, radiation and added-inertia chart
forces and give their actual assembled sum/world wrench; geometric inertia is
an explanatory subterm already included in the added-inertia force. Native model
JSON serialization supports the exact named development data/provider type only;
unknown fields, versions, source roles and subclasses are refused. ANYmarine now
persists the optional declaration and uses its shared native job/Qt workflow.
Saved dry inputs omit it entirely. Real BEM/physical-source admission remains open.

`data_to_dict`/`data_from_dict` expose strict plain-data interchange, with full
coupled arrays and equilibrium binding retained. Public `validate_states` and
`validate_accepted_history` support instantaneous preflight and final accepted
memory checks without integration or history mutation. The application numerical
worker checks accepted memory against final physical state before sealing output;
neutral result transport validates clock, finite shapes and component inventory.

Focused fixed-array and <=3step development tests check full K/C/Ma, coupled
blocks, force/work diagnostics, convolution/window/sign, native Newmark recurrence,
atomic memory and typed admission/refusal. See `native-fluid-plan.md` and the
living ANYmarine task record for prospective thresholds, scope and execution limits.
