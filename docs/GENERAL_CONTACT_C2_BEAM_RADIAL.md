# C2 development slice: classical round beams against fixed radial obstacles

This opt-in static profile admits concentric elastic classical B2 and B3
beams with declared round centreline radius against a fixed analytic sphere
or infinite cylinder. It uses the actual deformed B2/B3 curve, including B3
interior motion. The existing structural B3 reference cell must be straight
with its midpoint node at the admitted structural position. Beam end caps,
finite cylinders, moving obstacles, friction and corotational beam kinematics
are not admitted in this slice.

```python
ContactSurface("tube", (beam_id,), beam_radius=0.01)
RigidContactBody("sphere", "sphere", (0.0, 0.0, 0.0), radius=0.01)
ContactInteraction("tube_sphere", "tube", "sphere",
                   normal_stiffness=None, line_stiffness=1.0e4,
                   gap_tolerance=0.004)
ContactSolverSettings(pair_motion="general",
                      line_integration_relative_tolerance=1.0e-7)
```

For a sphere, the exterior gap is `||x-c|| - (R+r)`. For an infinite cylinder
with unit axis `a`, it is `||(I-aaᵀ)(x-c)|| - (R+r)`. Here `x` is the deformed
beam centreline, `R` is obstacle radius and `r` is beam radius. The line
penalty has units N/m² and is integrated over reference beam length. It is
not a surface-pressure stiffness or a three-dimensional Hertz model.

The exact radial squared-distance polynomial has degree at most four on a
B3 cell. Its stationary points determine the independent minimum gap and
its radius crossings partition active intervals. Each interval uses adaptive
8/16-point Gauss controls, with explicit relative accuracy and finite
subdivision budget. The residual and smooth-branch tangent differentiate
the same line potential and include obstacle curvature. The fixed obstacle
receives the opposite integrated force and moment about the global origin.

A swept-path check bounds material-point travel over each linear solver
trial. It tests exact curve minima at interval endpoints and midpoints,
subdividing until the declared gap budget is certified or the finite sweep
budget is exhausted. A clear endpoint cannot hide a through-crossing.
The candidate cell limit rejects excess work without dropping cells.

[The B3 sphere example](../examples/general_contact_round_beam_sphere.py)
demonstrates displacement-controlled interior contact, integrated forces,
gap and integration diagnostics, and a version-2 checkpoint. Focused checks
in `tests/test_general_contact_beam_radial.py` include independent B2/B3
line-energy integrals, smooth tangents, cylinder-axis invariance, a
through-crossing sweep, B2 cylinder and B3 sphere coupled solves, initial
interference rejection and restart binding.

This profile is **implemented and locally tested**, not independently
accepted. C2 still requires beam–shell contact, B3 and multi-cell beam pairs,
endpoint ownership for curved obstacles, mesh/enforcement refinement,
resource measurements and independent review.
