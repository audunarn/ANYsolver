# Native GE-B3 physical fibre section — development equation map

Parent checkpoint: `b297c72bfa73ae439224f2af13539e09f27c8827`.
This is a new private constitutive building block, not a replacement of any
accepted beam operator or qualification record. Independent review is PENDING.

## Physical convention

For the native right-handed material triad and physical offset `rho=(0,y,z)`,
`(kappa cross rho)_x = z*kappa_y-y*kappa_z`. Therefore, in the existing
generalized order `[eps_x,gamma_xy,gamma_xz,kappa_x,kappa_y,kappa_z]`,
`b_f=[1,0,0,0,z,-y]` and `e_f=b_f.e`.
Virtual work gives `N=sum(A*sigma)`, `My=sum(A*z*sigma)` and
`Mz=-sum(A*y*sigma)`. Areas and offsets are explicit physical inputs; no
equivalent rectangle, centroid relocation, automatic roll or legacy sign map
is inferred. Rotation of the material y/z axes transforms both offset and
curvature, preserving this contraction.

Public background: the OpenSees physical-fibre input convention explicitly
specifies y, z and area at
https://opensees.berkeley.edu/OpenSees/manuals/usermanual/220.htm . Its published
section implementation at
https://opensees.berkeley.edu/OpenSees/api/doxygen2/html/FiberSection3d_8cpp-source.html
stores a negated y coordinate (source lines 190–201) before forming fibre
strain (240–275). That implementation is not imported or copied. The native
sign above is derived directly from the cross product, not from names of
legacy curvature components. These links are background, not frozen formal
execution authority.

## Incremental potential and physical recovery

Let the declared elastic background factor be F, with `Cb=F^T F`. It supplies
shear/torsion and any explicitly declared elastic generalized coupling; axial
and flexural terms in F are additive, not silently subtracted from fibres.
The complete virgin elastic section must be positive definite.

For each fibre use E>0 and a positive, nondecreasing continuous piecewise-linear
flow stress Y(p). A separately specified nonnegative tail slope governs
extrapolation. Linear hardening and a measured table with a flat tail are
distinct policies. The energy integral is analytic on each interval.

At a fixed, immutable origin `(z0,p0)`, `p0>=abs(z0)`, minimize

`Pi(e,d) = |F e|^2/2 + sum_f A_f [ E_f*(b_f.e-z0_f-d_f)^2/2
                                                + integral(p0_f,p0_f+|d_f|) Y_f(p) dp ]`.

Each scalar return has fixed sign sign(E*(b.e-z0)). Its nonnegative magnitude
u satisfies `E*u+Y(p0+u)=abs(E*(b.e-z0))`, or u=0 inside yield. Solve the
piecewise affine equation by bounded interval traversal, not iterative
material-tangent substitution. Smooth plastic tangent `Et=E*H/(E+H)`; elastic
tangent E. Exact yield and table-knot cases carry explicit semismooth labels.
Perfect-plastic plateaus are permitted and must not be regularized.

`s=Cb e+sum A*b*sigma` and `Ct=Cb+sum A*Et*b*b^T` are the first and second
variations of this potential. Stored hardening energy is
`U(p)=integral(0,p) [Y(q)-Y(0)] dq`; dissipation is `Y(0)*u`.
Thus the incremental potential equals current stored energy minus old stored
hardening energy plus dissipated work. Physical fibre stress and elastic
strain are recovered directly from the trial state, not from a generalized
plastic direction. Trial calls do not mutate or commit their origin.

## Representation and integration boundary

Use bounded 80-digit Decimal evaluation and normalized high/low binary64 pairs
for histories, recovered values and generalized response. This is numerical
arithmetic, not an exact or interval certificate. Freeze captured fibre order,
material curves and background factor in the section identity. Reject foreign
history, invalid inputs and nonfinite/unrepresentable output.

The existing ANYmaterial linear/table parameters can be captured by exact type
and copied values only with explicit `PARAMETER_CAPTURE` reinterpretation as
this native work-conjugate constitutive law. ANYmaterial documents true stress
and true plastic strain; numeric parameter capture is **not** an automatic
true-to-nominal finite-material-strain conversion or equivalent adapter. The
native strain/reference-area stress measure is bound in the section identity.
Its generic flow-stress/tangent protocol also does not define a hardening-energy
integral; arbitrary curves cannot be accepted by assuming one. A fully
measure-consistent general material adapter remains required separately.

This component is strain controlled. Integration into the retained beam still
requires a separately derived coupled station/fibre complementary problem,
station-owned transaction and restart integration, and assembled validation.
Neither the existing directed scalar law nor its one-variable-per-station
conjugate can be relabeled as a fibre adapter. Shear/torsion plasticity and
general nonlinear coupled sections remain part of the overall programme.
