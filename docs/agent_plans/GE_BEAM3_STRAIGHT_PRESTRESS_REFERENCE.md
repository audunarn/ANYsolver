# Straight prestressed continuum development reference

This is a new, same-author continuum reconstruction, not independent review,
not an interval-certified oracle and not public beam qualification. It imports
no production element, mixed mechanics, AD, SO(3), recovery or mass routines.
The unchanged native source baseline is commit
`f29fb7fce7a8aab3f44ba722e7356087778b319b`, tree
`400c91fc1354e05daa423b319df44fc069e5fcdb`.

## Source and derivation

The zero-load convention is the independent displacement/rotation Timoshenko
weak form in [TU Delft's beam text](https://interactivetextbooks.citg.tudelft.nl/computational-modelling/structural_linear/timoshenko_md.html),
sections Strong form equations and Derivation of the weak form, inspected
2026-09-06. Here the work-conjugate moment is `M=+B theta_x`; the text's
strong-form moment uses the opposite sign. We derive the prestress extension
below, rather than attributing it to that unstressed source.

For straight reference arclength x, a planar perturbation about an exactly
straight equilibrium has r_x=(lambda,v_x), Q a planar rotation theta,
gamma_1=lambda*cos(theta)+v_x*sin(theta)-1,
gamma_2=v_x*cos(theta)-lambda*sin(theta), kappa=theta_x.
The elastic potential density is
`(EA*gamma_1^2 + S*gamma_2^2 + B*kappa^2)/2`.
The spatial dead axial tip load N is positive in tension, lambda=1+N/EA.
The tip potential is linear in Cartesian displacement and has zero Hessian.

The exact second variation in the bending plane is

`S*v_x^2 + 2*(N-S*lambda)*v_x*theta
 + (S*lambda^2-N*lambda)*theta^2 + B*theta_x^2`.

Let C=N-S*lambda and D=-lambda*C. Work-conjugate boundary quantities are
T=S*v_x+C*theta and M=B*theta_x. With reference line/rotary masses m,j and
signed squared frequency z, the continuum equations are

`v_x=(T-C*theta)/S; theta_x=M/B; T_x=-z*m*v;
 M_x=(C/S)*T + (N*(lambda-N/S)-z*j)*theta`.

Clamp v(0)=theta(0)=0; free end T(L)=M(L)=0. The implementation propagates
this constant four-by-four system with a matrix exponential and solves a
caller-frozen determinant bracket. It does not claim an eigenvalue count.
A separate conforming Legendre weak form checks the first signed root and
p-refinement numerically. It shares only the displayed continuum coefficients,
not the shooting matrix. Both reconstructions are same-author binary64 work.

For N=-P and z=0, T=0, theta_xx=-(P/B)*(1+a*P)*theta,
where a=1/S-1/EA. On the admitted branch EA>=S>0, the first cantilever
onset satisfies P*(1+a*P)=B*(pi/(2L))^2. We evaluate its positive root without
subtractive cancellation, and reject a nonpositive equilibrium stretch.
This includes axial shortening and shear effects; it is NOT the inextensible
Euler approximation. The shape theta=sin(pi*x/(2L)) independently checks the
clamp and moment-free tip conditions. It says nothing about a curved arch,
post-buckling branch selection, plastic stability or coupled sections.

## Frozen small development cases

Before execution: L=2, EA=3000, S=1000 in both planes, B=1 in both
planes, torsional stiffness 2; reference inertia diagonal
`[1,1,1,.002,.001,.001]`. Nodes and frames lie on the x-axis with identity
reference frames. The native section remains elastic (yield=1e6). Use actual
native force-control equilibrium, accepted history replay and retained-cell
loaded-modal assembly; no synthesized accepted states.

Use 2 and 4 macros unloaded, then 4 macros at N=-0.5*Pcrit,
-0.98*Pcrit and -1.02*Pcrit. The bracket for the first continuum squared
frequency is [-2,4]. Compare both first bending frequencies at zero/half
compression with the existing 2% engineering criterion; require refinement
improvement unloaded. Check positive/negative native signs either side of the
fixed 2% onset neighborhood without calling it a certified native root bound.
Other invariants retain 1e-11 normalized checks. No coefficient, tolerance,
existing evidence, default or qualified element changes are authorized here.

These are small correctness fixtures, not a performance sweep or formal
qualification wave. Larger/slenderness campaigns need the resource workflow.
All failed observations must remain visible; no threshold tuning against data.

## Completed development observations

The initial continuum inventory passed 18 tests in 0.45 seconds. Two additional
checks subsequently covered exact zero-load tip compliance and deliberate
omission of the prestress term; the mutation disagrees with the separate weak
form. The first five-case native execution passed its two tests in 9.34 seconds.
The final suite passed 45 tests in 59.33 seconds: 20 continuum checks, two
native engineering checks and 23 preserved loaded-modal checks. There were
no test failures or corrections to mechanics, cases or acceptance thresholds.
The separate static evidence/parser inventory passed six tests in 0.12 seconds.

The continuum critical compression is 0.6165968139807441 in the frozen units.
For four native macros the first-plane frequency error is approximately
-0.1143% unloaded and +0.00455% at half that compression. Both bending planes
pass the 2% criterion; the unloaded comparison improves from two to four
macros. At 98%/102% of the continuum critical compression both native bending
eigenvalues are respectively positive/negative. The remaining four requested
eigenvalues are positive. Their frequency accuracy was NOT a gate here.
Near-onset relative frequency accuracy is NOT claimed: small signed values
are sensitive to discretization error. This is not an exact native onset
location, proof of the full spectrum, or post-buckling branch qualification.

Both native executions produced byte-identical comparison records and accepted
state capsules for all five cases. The actual native load path reproduced the
analytic axial displacement and passed complete spatial equilibrium checks;
modal replay did not advance material history. This source-runtime evidence
does not establish equality with a different wheel/runtime combination.

All 20 files (578,310 bytes) were copied to an exclusive external archive and
verified by byte count and SHA-256 from the normal workspace context:

`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-straight-prestress-development-20260906-d38821308089`

The canonical inventory and source bindings are in
`docs/reference_cases/ge_beam3_straight_prestress_development_evidence.json`.
Original temporary outputs and all older evidence remain preserved. Only
verified relay duplicates are removed. No resource request was consumed.
Independent review remains PENDING. Next are expanded engineering spectra,
slenderness and curved/prestressed references, followed by general parity and
objective beam-shell connections. No public capability or default is enabled.
