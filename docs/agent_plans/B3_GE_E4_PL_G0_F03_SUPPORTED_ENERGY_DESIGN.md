# Classical F03 supported energy: separate proof and numerical screen

The classical panel stiffness is a sum of `t w det(J) Bᵀ D B` terms. Thickness,
weights, Jacobians, and the plane-stress constitutive matrix are positive.
For regular Q4, the strain components are polynomials in the reference cell;
the 2×2 Gauss points annihilate a zero-energy polynomial at all points. A
zero-energy Q4 displacement is therefore an infinitesimal rigid motion.
The same holds for constant-strain CST triangles. Adjacent elements share a
full edge and both displacement components at its two endpoints, so their
rigid motions coincide. This connected panel has only three global rigid
motions. Fixing both displacement components on its left and right boundaries
eliminates all three.

The beam stiffness is the integrated positive `EA (u')² + EI (theta')² +
GA (v'-theta)²`. Three-point Gauss quadrature exactly integrates its polynomial
strain products. Zero energy implies constant `u` and `theta` and a linear
`v` with slope `theta` on every element. Shared nodal fields propagate the
same rigid motion through the chain; fixed root `u`, `v`, and `theta` remove it.
Thus the uncoupled supported primal block is mathematically positive definite
for the admitted mesh, topology, section, and support definitions. This
argument depends on correct assembly and support indexing; it is not a
floating-point eigenvalue enclosure or a claim about the indefinite KKT block.

`_b3_e4_f03_supported_energy.py` adds an independent sparse numerical screen.
It eliminates supports, applies positive Jacobi congruence (inertia preserving),
and requests the *smallest algebraic* eigenpair. A sufficiently negative
Rayleigh quotient is an explicit negative-energy witness, including when a
small positive mode sits closer to zero. A nonnegative result is only a
screen: Lanczos convergence does not certify that no unobserved negative mode
exists. Nonconvergence fails explicitly. This code forms no dense global
matrix, runs no registered Nm128 case, and does not change the scientific
adjudicator or its existing qualification outcome. A future numerical
certificate for an arbitrary assembled sparse matrix would require verified
inertia of a symmetric sparse LDLᵀ factorization or a rigorous lower bound.
