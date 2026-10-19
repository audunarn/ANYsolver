# Marine W6 prospective cases

`contract.json` fixes inputs, normalization, near-zero handling and acceptance
thresholds before execution. This tooling covers the W6 line inventory; a rehearsal
or green runner is not scientific acceptance. Independent scientific assessment
remains separate from implementation authorship, as required by the adopted
ANYmarine plan. Different-model-family assessment is preferred when available;
cached Mistral unavailability is not a waiver of independent assessment.

The reference implementation uses equilibrium force integrals and numerical
quadrature rather than the product's closed-form catenary or initializer. In
reference material coordinate s, local cable tension is (H,0,V+w*s), and the
position derivative is tension/|tension| + tension/EA. End forces are opposite
local internal tensions. Suspended reference forces solve both terminal-position
integral equations. A grounded frictionless reference has constant H on its
grounded length and V=0 at touchdown; its suspended length and H satisfy terminal
span and elevation. Reference ground is the line-center surface at floor+D/2.
Finite foundation compliance is tested against its explicit penetration bound,
not represented as an exact hard constraint.

Axial vibration uses two taut springs and their reference lumped mass. Contact
release uses the piecewise closed-form response of m*q''=max(-K*q-C*q',0) for
q<0, and zero normal force otherwise. The non-tensile Kelvin branch releases when
raw normal force first reaches zero; ballistic motion follows. Energy checks
separate stored foundation energy, damping/clipping loss and time-discretization
error. No hidden numerical stiffness or compression regularization is introduced.

MoorPy's [catenary implementation](https://github.com/NatLabRockies/MoorPy/blob/main/moorpy/Catenary.py)
is a separately authored optional reference, not a runtime dependency. This
runner does not claim to have executed MoorPy. Sources are provenance, not proof
that every case or scope has been validated.

Run in an installed ANYsolver/ANYloads environment with BLAS/OpenMP threads set
to one and a supervised 90-second process bound:

```text
python runner.py --out UNIQUE_EVIDENCE_DIRECTORY --phase rehearsal
```

Every case writes accepted results, metrics and failed predicates separately.
The summary retains complete required inventory and non-success status. Formal
acceptance also requires an independent review tied to the exact contract,
runner, installed candidate and evidence identities. No automatic promotion,
threshold tuning, skipped cases or scientific gate relaxation is permitted.

The v4 register also specifies incoming landing, exact per-case overrides,
harmonic wave/current coefficients, translation and off-center force/moment
checks, and seven application replay cases. Contact energy defect is
E(t)-E(0)+trapezoidal integral of D. It must remain within2% and decrease under
the registered final time refinement; the stored foundation energy persists
between raw-force release and geometric separation. Finest static/dynamic levels
meet reference accuracy; the last two registered levels meet refinement criteria.
Coarser levels remain evidence and cannot be relabelled as qualified outputs.

The rejected 8 m grounded span cannot accommodate 10 m of non-shortening line
within a monotone grounded/suspended geometry. The prospective 9 m span is
checked for reference existence before a product solve. The prescribed-kinematics
companion uses heading 30 degrees and nonzero normal/tangential translational
velocity and acceleration; each of twelve exact wave phases checks endpoint
forces, named assembled components and added nodal mass. It is an instantaneous
assembly check, not a claimed response trajectory. Dry line inertia is included
once. Landing displacement scale is hypot(q0,v0/omega_n), retained at zero crossings.

`test_oracles.py` checks terminal closure, global force balance, rejection of the
impossible geometry and differential contact force/storage/power laws. Product
cases use public installed APIs and preserve every accepted continuation stage or
time frame. Dynamic force and moment balance includes actual structural inertia.
Failed predicates stop the candidate, with the missing inventory recorded.

## Explicit continuous contact law

V4 uses the prospectively adopted, opt-in `marine_seabed_contact_v2` for dynamic
contact fixtures. The physical activation depth is 1e-4 m. The coefficient C is
saturated damping; the active factor is min(penetration/depth,1). Force is
max(K*penetration-C*factor*velocity,0), with unchanged elastic storage and retained
clipping loss. This changes near-boundary damping/rebound. It is uncalibrated
development data, not a universal default or a step-size tolerance. V1, including
its saved no-root failure, stays unchanged and is not qualified by V4 results.

The scalar reference independently integrates motion and loss with bounded
DOP853 steps, exact prelanding flight, surface/ramp events and contact-gated
clipping detection. An outgoing velocity 0.2 m/s exceeds the 0.1 m/s clipping
threshold; its clipped departure is independently exact and ballistic. Eight
application replay aliases now map explicitly to generated case IDs. Point and
trajectory passivity, reference accuracy, energy and refinement thresholds remain.
