"""Independent reproduction of one campaign case without the runner's code.

SS plate, t = 0.01, q = 1 kPa, meshed with right triangles whose smallest
angle is exactly 20 deg (cells hx = 1/8, hy = hx tan 20, 22 rows), solved via
the *public* pressure LoadCase route.  Reference: Timoshenko & Woinowsky-
Krieger Table 8 (square SS plate, w_max = 0.00406 q a^4 / D) plus an
independently coded Kirchhoff Navier sum for the exact b/a.
"""

import math
import numpy as np
from anysolver import FEModel, LoadCase, create_shell_element, solve_linear
from anysolver.boundary import BoundaryCondition

E, NU, T, Q = 210e9, 0.3, 0.01, 1.0e3
nx, ny = 8, 22
hx = 1.0 / nx
hy = hx * math.tan(math.radians(20.0))
a, b = nx * hx, ny * hy
model = FEModel("independent")
model.add_material("steel", E, NU, density=7850.0)
nid = lambda i, j: 1 + i + j * (nx + 1)
for j in range(ny + 1):
    for i in range(nx + 1):
        model.add_node(nid(i, j), i * hx, j * hy, 0.0)
eid = 0
min_angle = 180.0
for j in range(ny):
    for i in range(nx):
        for tri in ((nid(i, j), nid(i + 1, j), nid(i + 1, j + 1)), (nid(i, j), nid(i + 1, j + 1), nid(i, j + 1))):
            eid += 1
            model.add_element(eid, create_shell_element(eid, list(tri), "steel", thickness=T, reference_normal=(0, 0, 1.0)))
            p = [np.array(model.mesh.get_node(n).coords()) for n in tri]
            for k in range(3):
                u, v = p[(k + 1) % 3] - p[k], p[(k + 2) % 3] - p[k]
                min_angle = min(min_angle, math.degrees(math.acos(u @ v / np.linalg.norm(u) / np.linalg.norm(v))))
edge = lambda f: [nid(i, j) for j in range(ny + 1) for i in range(nx + 1) if f(i, j)]
model.add_boundary_condition(BoundaryCondition("x", edge(lambda i, j: i in (0, nx)), {"uz": 0.0, "rx": 0.0, "ux": 0.0, "uy": 0.0}))
model.add_boundary_condition(BoundaryCondition("y", edge(lambda i, j: j in (0, ny)), {"uz": 0.0, "ry": 0.0, "ux": 0.0, "uy": 0.0}))
load = LoadCase("q")
for e in range(1, eid + 1):
    load.add_pressure_load(e, Q)
u, info = solve_linear(model, load)
# centre (a/2, b/2): i = 4 exactly; j = 11 exactly
w = abs(u[model.mesh.dof_manager.get_node_dofs(nid(nx // 2, ny // 2))[2]])
D = E * T**3 / (12 * (1 - NU**2))
navier = sum(
    16 * Q / (math.pi**6 * m * n * D * ((m / a) ** 2 + (n / b) ** 2) ** 2) * (-1) ** ((m + n) // 2 - 1)
    for m in range(1, 200, 2)
    for n in range(1, 200, 2)
)
print(f"elements {eid}, min angle {min_angle:.6f}, a={a:.6f}, b={b:.6f}")
print(f"FE w_c = {w:.6e}; Navier(Kirchhoff) = {navier:.6e}; table(square) = {0.00406 * Q * a**4 / D:.6e}")
print(f"error vs Navier = {abs(w - navier) / navier:.4e}")
