# F03 independent spectral axial reference: transverse regularity remains open

24 September 2026. This is a Level-A mechanics diagnostic, not a formal F03
run, a converged continuum target, or native B3-GE/E4-PL qualification.
The high-consequence risk is a falsely reassuring tip or weak-residual match
while connection forces, energy and pointwise compatibility remain
unresolved. The private comparator uses a two-dimensional plane-stress
Fourier-sine basis in x (both edge translations zero), global Legendre
polynomials in y (natural free edges), the separately implemented classical
quadratic/Hermite beam, and a newly assembled three-channel P1 virtual-work
line. Its shell stiffness does not import Q4/CST or E4-PL operators.
The same `E=210 GPa`, `nu=.3`, `t=.07 m`, four material samples at
`(±.2,±.23) m`, both-edge supports and `10^5 sin(2 pi s) N/m` beam axial
load are used. The beam law and physical pose are still distinct from
native six-channel B3-GE/E4-PL.

Source SHA-256 at this checkpoint:
`b3_e4_f03_spectral_axial_reference.py`
`7750d6976e46a278c69499823302308d299675e348a0401db7a4af23fd1d8bfe`,
bounded runner `7041e377c3bfb471c3c424885645feb7ab0b1a655d5e7892c5b4b4fa74f01f91`,
and focused tests `2786626c511b2a541bd6ecbea7ca0fcaef7128a34c78f4113ee029fd75f89737`.
The seven-case fixed-resolution raw suite is
`B3_GE_E4_PL_F03_SPECTRAL_AXIAL_RESOLUTION_V1.json`, SHA-256
`249c4262178954f7004e8d6c7dea28755619461b5f9266b2d2e16f8c07842881`.
Nine additional high-order roots named
`B3_GE_E4_PL_F03_SPECTRAL_NX*_V1/` contain their exact source hashes,
command, dependencies, one-thread setting, 8 GiB sampled-child RSS and
300 s wall limits, raw stdout/stderr, parsed result and status. All nine
completed; maximum sampled child RSS was 4.843 GB and maximum wall time
34.43 s. The source admission maxima widened during exploration; each
root binds its actual bytes, and the changes did not alter the equations.
No earlier source variant is retroactively called the final candidate.

Four focused checks passed. They compare modal stiffness with closed-form
energies, the assembled mixed energy with separate two-dimensional strain
quadrature, the four-sample pose with direct field evaluation, and the P1
line wrench with exact force/first-moment integration. An initial x-origin
mapping error was found and fixed before the retained resolution suite.
The final finite systems have weak rows around `1e-22`, algebraic residual
ratios around `1e-14`, small work discrepancies, and beam-root/line-resultant
agreement within the reported numerical precision. These are consistency
checks, not physical convergence.

At fixed 128 beam elements and 128 P1 intervals, changing 64→96→128
longitudinal shell modes with 16 transverse modes changes beam tip by
`0.110%` then `0.0645%` and beam energy by `0.360%` then `0.183%`.
By contrast, at 64 longitudinal modes, increasing transverse order
`16→24→32→48→64` changes beam energy by `9.44%, 4.90%, 6.93%, 2.93%`
and root axial force by `2.28%, 1.53%, 2.31%, 1.04%` on adjacent steps.
The tip changes only `1.13%, 0.410%, 0.496%, 0.202%`. Thus the tip is
again a misleading convergence proxy. At fixed `(nx,ny,beam)=(48,16,128)`,
line intervals `32→64→128` change beam energy by `11.28%` then `8.16%`
and root axial force by `4.91%` then `2.69%`.

On the `64×64`, 128-beam, 128-line case, the 12-point-per-beam-cell
quadrature L2 gap is `1.94e-10 m`; a Gauss-station *lower bound* on the
largest component gap is `4.22e-9 m`, about `1.26%` of the beam-tip
magnitude. The weak row norm is only `6.6e-23`. The truncated Fourier
field's direct edge-stress traction may not exactly balance at finite
order; its residual is retained as a warning, not promoted to a support
reaction oracle. Interface-wrench and beam-root balance use the actual
P1 virtual-work transpose.

The likely reason global transverse polynomials converge slowly is
mechanical: four sampled material lines at `y=±.23 m` introduce
concentrated line tractions in the two-dimensional shell. Across those
lines, a continuous displacement can have a derivative kink. A global
smooth polynomial basis then approximates a nonsmooth field algebraically.
This is an inference from the weak form and observed y-order trend, not
an accepted singularity proof. The next development candidate should
place transverse spectral-element boundaries exactly at `±.23 m`, retain
the same material energy and attachment work, and compare its order
sequence with this raw global-basis evidence. It needs independent
mechanics review before any formal reference claim. The mandatory
physical torque/shear, signed stability, full mesh-ratio and external
comparisons remain open. **F03/G0B remain open; G1 is barred.**
