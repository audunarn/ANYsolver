# Adopted analytical verification model

Derived and independently reviewed before FE assessment in
`supervisor_reference_review.md`; Astra adoption and metrics are recorded in
`supervisor_findings.md`. The executable is `diagnostics/arc_reference.py`.
This is a constrained cylindrical composite-strip verification model. The
free-width stiffened plate is assessed separately by `diagnostics/mesh_study.py`.

The reference family is the classical pure-moment cantilever, with
Phi=M*L/(E*I), described in the
[Abaqus large-rotation cantilever benchmark](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEBMKRefMap/simabmk-c-nlgeocantilever.htm).
The eccentric composite-section extension and its constituent loading are
derived below and independently reviewed for this task.

Use L=1m, W=.1m, shell t=.001m, beam b=.01m in y and h=.002m in z,
E=210GPa, nu=0, e=0/.002m, terminal Phi=30/60deg. Constituents are additive
shell and beam energies, including geometric overlap at e=0. Material is linear
elastic, not S355 plastic. All shell nodes at an x-station share ux,uz,ry;
uy,rx,rz=0. Only the root station is clamped. These exact zero-work row
constraints redistribute line transfer across the width without a penalty.

With As=Wt, Ab=bh, Is=Wt^3/12, Ib=bh^3/12, zero total axial force minimizes

    U/L = E/2 [As*(lambda_s-1)^2 + Ab*(lambda_s-1+e*k)^2
                +(Is+Ib)*k^2].

Hence zbar=Ab*e/(As+Ab), lambda_s=1-zbar*k,
B=E[Is+Ib+As*Ab*e^2/(As+Ab)], M=B*k, k=Phi/L.
The rigidities are3.15Nm² at e=0 and17.15Nm² at e=.002m.
Positive ry bends toward negative z. Shell and beam centroid radii are
Rs=1/k-zbar and Rb=Rs+e. Their terminal displacements are

    ux_j = Rj*sin(Phi)-L; uz_j=Rj*(cos(Phi)-1); ry_j=Phi.

Apply shell Ns=-E*As*zbar*k and beam Nb=-Ns along the FINAL tangent
(cos(Phi),0,-sin(Phi)), plus their centroid moments E*Is*k and E*Ib*k in +y.
Distribute shell resultants with weights[1/4,1/2,1/4]. Their force couple adds
e*Nb to the centroid moments, giving totalB*k. Do not add another composite
moment. These fixed dead loads are equivalent to the intended loads only at
the terminal equilibrium; the ramp is not asserted to trace circular arcs.
For this single-axis family the additive ry covector equals spatial My.

Maximum material strains at60deg are.10472% (e=0) and.27925% (e=.002m).
The oracle uses engineering strain and reference-length curvature; it is a
small-strain/large-rotation model, not a general finite-strain certification.
The benchmark always requests work_conjugate internal force, including e=0.

The required nx8/16/32,ny2 refinements use nb=nx or1.5nx. Interpolation samples
chords, not exact arcs. The original rotation-vector interpolation was exact on
this commuting single-axis field; a chosen objective mean may add a higher-order
orientation interpolation error, which is assessed without changing the oracle.
Independent prospective chord analysis predicts appreciable
nonmatching axial bias at nx32. Additional64/128/256 refinements are permitted
in order only for decreasing errors and within the unchanged numerical budget.
Every level/failure remains evidence. No loads, geometry or tolerances are fit.

Acceptance: terminal equilibrium at reviewed loads, explicit completed status
and lambda1; relative independently reconstructed residual<=1e-7; unchanged
material inputs; passed constraint postcheck. For BOTH centroid tips require
norm(u_FE-u_arc)/norm(u_arc)<=1% and abs(ry-Phi)/abs(Phi)<=1% at the finest
assessed level. Last-refinement vector/ry changes normalized by the finer
result must be<=.25%. Report component errors too. No arbitrary nonuniform
3D objectivity or free-width plate accuracy follows from this planar benchmark.
