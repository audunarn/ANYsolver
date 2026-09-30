# Independent mechanics review — saved torque work

Reviewer `/root/e01_connection_decision`, read-only and not the implementer;
no source edits or numerical jobs. Checked geometry, frames, loads, supports,
point-map equations, capture runners, beam-port evidence and cross-work script.

The2m×1m panel,0.07m thickness, beam at y=-.5m/z=+.1m, identity physical
frames and+100Nm torque match. Root1/10/19/28/37; shell-tip9/beam-tip117.
Six global coordinates and resisting covectors are in matching order.
Native point linearization gives the same rigid-arm translations and equal
rotations as the external link. All48 beam-port columns match5.603e-14,
including retained/intermediate coordinates. No beam interpolation explanation.

The saved actions are +K_s*s. Subtracting beam reciprocal work for the same
load and map gives D=aN*sE-aE*sN=p*(qE-qN). Beam contributions cancel;
root reactions pair zero. Do not add the beam-tip load again to shell actions.
Runner and result hashes independently checked:

- runner9a844e135d434b025c7c0fbd95e32f8b7495c2b9c3c76345c66ff3045769a135;
- result2f5beeee2146fd15fbee652fd3206f32b5a2cfb45b23330e8fe43cf328662738.

Closure4.1554e-13 is correct. Membrane/normal-spin cross-work+5.135551e-4J,
plate-1.129641e-5J, total+5.022587e-4J. rz alone+5.25131966438152e-4J.
Signed percentages over100 reflect cancellation, not positive energy fractions.
Indirect normal-spin/membrane impedance is the principal supported explanation
for this coupled gap; neither model is thereby proved physically correct.

Native planar centre-PL work contains theta_z minus half the in-plane curl,
its first derivatives and retained drilling hourglass work:
`e4_pl_element.py:2112–2135,5539–5568`. External ASDShellQ4 uses different
one-point Hughes–Brezzi drilling plus stabilization. Nominal section parity
does not match these operators. Do not compare or tune parameter numbers.

**Next reference action:** define physical material spin/frame, physical
director, station/footprint sampling, moment work conjugacy and root treatment.
Half in-plane curl can define flat linear material spin, but discrete recovery
and averaging must be explicit. Such a recovered-frame or finite-footprint
reference is a distinct variant, not a silent replacement or automatic E01
accuracy oracle for the existing nodal-pose points.

Retain existing six-row points, thresholds and E01 openness. M2 can independently
advance its distinct position/top-surface director bond with free normal spin,
chart guards, actual-update derivatives, eccentric free-spin and physical work
checks. No BL5 acceptance, F03 execution or blanket formulation verdict follows.
