# Explicit virgin-energy conditioning diagnosis successor

Base75a689347e047ef9caab8a0aeca3a7358d5797dd, tree
6e968ec67610795dafdb72edd33bf0505ae589c4. Three new research paths:
this plan, ge_beam3_generalized_energy_chain.py,
test_ge_beam3_generalized_energy_slenderness.py. Original diagnostic files,
7b0a64d failures and native force/tangent implementation remain untouched.

The original diagnostic stopped on an exact-symmetry assertion before saving
rotated raw blocks. This successor first saves every raw high/low Hessian and
residual, then records the supplied compliance skew. For the energy audit only,
form its symmetric part: x.T S x = x.T((S+S.T)/2)x in exact arithmetic.
Average each binary64 pair exactly using Fraction, then round once; report
the maximum rounding error as an exact rational. Require exact transpose
pairing of kinematic blocks. Zero-stress and zero-geometric-Hessian checks
remain unchanged. No native force symmetrization or tolerance waiver.

Reuse the identical rho100/10000/1e6 specimens, four straight/curved/rotation
variants each, material/inertia, native quadrature and80/100-digit supplied
factor audit from GE_BEAM3_GENERALIZED_SLENDERNESS_DIAGNOSTIC.md. Preserve
the1e-40 Decimal convergence requirement, positive clamped audit roots and
recorded1e-11 native root/covariance comparisons. These remain observations,
not engineering gates. Save raw evidence before every possible factor failure.
State must remain byte unchanged, and native returned/rejected results are
recorded without automatic retry. This is not an independently authored
mechanics reconstruction or production qualification.

Local inventory: three explicit symmetric-energy/work-boundary tests, three
scientific files. Then three parallel rho inventories, one test/four complete
observations each, raw counts conditional on native typed rejection. One
invocation only; no repeated failed requests or qualification cycles.
Compare unrotated supplied input factors and Decimal roots to the preserved
7b0a64d outputs after completion; they must be byte-identical, not merely close.

Retain one numerical thread,24GiB and600seconds per child,120second CPU
inactivity, at most three workers and1800seconds per wave. Decimal bounds
remain120seconds per invocation and100Jacobi sweeps. No mechanics, public
alias, defaults, engineering thresholds, old evidence or source limits change.
DIAGNOSTIC_OBSERVATIONS_COMPLETE is nonclassifying. Full goal active,
independent review PENDING. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
