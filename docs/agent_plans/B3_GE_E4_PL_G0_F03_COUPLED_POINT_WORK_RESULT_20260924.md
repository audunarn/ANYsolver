# G0 F03 composed shell/B3 point-work diagnostic — 24 September 2026

Status: **bounded one-station work and curvature check passed; G0B remains
open.** This is a derivation diagnostic, not a weak bonded line, production
mixed owner, material-trial qualification, or registered scientific case.

The diagnostic composes three existing seams at one material station:

1. The flat E4 Q4/S3-V2D additive-coordinate shell finite pose.
2. The actual native retained B3 half-cell spatial port.
3. The existing objective `RigidPoseJoint` relative-pose Log law.

For nonzero physical multipliers, it pulls the joint scalar Exp-chart
Hessian through the two station maps and adds the joint residual contracted
with each map's mixed position and angular-chart acceleration. The angular
acceleration is derived from the mixed frame-matrix variation after removing
the symmetric product of the two first-order spatial rotations. This uses
the scalar chart Hessian, not the spatial residual Jacobian as an
unjustified symmetric substitute.

The shell reference is uniformly translated before capturing the joint
reference in the eccentric cases. That translation is stress-free for the
flat shell idealization and creates a declared master-frame offset of
0.11 m to the native beam axis. The same test also runs at zero offset.

With `C:\Python\Python314\python.exe`, **4 focused cases passed**: Q4 and
S3-V2D, each at zero and nonzero eccentricity. The direct oracle perturbs
both shell total coordinates and the actual native `Context.advance` state,
evaluates the joint work from value-level poses, and compares central first
and four-point mixed second differences with the analytic pullback. The
captured virgin reference has zero six-component constraint gap.

Independent read-only mechanics review found no actionable issue in the
chain rule, angular correction, or eccentric reference test. It confirmed
the evidence is limited to one bounded point. Large-origin joint-reference
construction was not exercised by this test, although the native station
port itself retains compensated positions.

The next required work is an authenticated multi-element E4 material trial
from one accepted predecessor and a fixed-host segmented line integral with
exact multiplier spaces, full coupled KKT and stability studies. Eccentric
face-layer sampling and chart transport also remain open. No one-use
scientific registration was consumed; G1 remains barred.
