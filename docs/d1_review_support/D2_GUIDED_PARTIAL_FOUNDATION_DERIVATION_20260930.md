# Guided partial-foundation scalar reference

Development continuum comparator; no production contact calls or general nonlinear
qualification. Fixed candidate: `x=s+0.1`, `0<=s<=L=1 m`, width `B=1 m`, fixed
target coverage `0<=s<=Ls=0.9 m`, tail `T=L-Ls=0.1 m`. Source normals are guided,
normal displacement w is positive upward, and downward load is `q=0.5 Pa`.

## Mechanics and dimensions

With `E=1e5 Pa`, `nu=0.3`, `t=0.05 m`, `ks=5/6`,

`D=ks*E*t/[2(1+nu)]=1602.5641025641025 N/m`.

The small-motion transverse-shear scalar problem is

`-D*w''-p+q=0`, `w(0)=0`, `w'(L)=0`,

`p=kappa*max[-(g0+w),0]` on coverage and `p=0` on the tail,
with `g0=1e-4 m`, `kappa=1e6 Pa/m`, `beta=sqrt(kappa/D)` in `1/m`.
Thus `D*w''`, p and q have units Pa; integrating pressure along s gives N/m,
and multiplication by B gives force N. The physical source pressure acts upward,
the fixed target receives its opposite, and the clamp normal reaction is
`Rclamp=-B*D*w'(0)` upward. This is a continuum local foundation law; finite-mesh
weak projected pressure is not assumed equal to pressure at a point.

## Regimes and the unique front

Admitted parameters: positive finite D, q, kappa, B, L and `0<Ls<=L`, with `g0>=0`.
The contact-free displacement is `w=q*s^2/(2D)-q*L*s/D`. There is no contact if

`g0 >= q*Ls*(2L-Ls)/(2D)`;

equality gives zero pressure at the cut. If `g0=0`, contact starts at the clamp
(`a=0`). If `0<g0<` this critical gap, there is exactly one front `0<a<Ls`.
On `0<=s<a`,

`w=q*s^2/(2D)+b*s`, `b=-g0/a-q*a/(2D)`.

Let `lambda=beta*(Ls-a)` and `phi=w+g0`. The active solution is

`phi=-q/kappa+(q/kappa)*cosh[beta*(Ls-s)]/cosh(lambda)`
`     -(q*T/(D*beta))*sinh[beta*(s-a)]/cosh(lambda)`.

It solves `phi''-beta^2*phi=q/D`, `phi(a)=0`, `phi'(Ls)=-q*T/D`.
Matching slopes gives the supplied front equation

`q*a/(2D)-g0/a+q*tanh(lambda)/(D*beta)+q*T*sech(lambda)/D=0`.

The implementation instead brackets the equivalent nonsingular function

`g_required(a)=q/D*[a^2/2+a*tanh(lambda)/beta+a*T*sech(lambda)]`.

Its derivative is

`q/D*[a*tanh(lambda)^2+tanh(lambda)/beta+T*sech(lambda)`
`     +a*T*beta*sech(lambda)*tanh(lambda)] > 0` in the open interval.

Endpoint values are zero and the critical gap. This proves existence and
uniqueness and avoids division by a at the left bracket. Open-covered phi is
`(a-s)*[g0/a-q*s/(2D)]>=0`; active phi is nonpositive. The displacement decreases
through coverage, so the covered minimum gap is at Ls. On the uncovered tail,

`phi=phi(Ls)-q*T*xi/D+q*xi^2/(2D)`, `xi=s-Ls`.

Negative tail gap carries **zero pressure**: it is outside the contact footprint.
At Ls displacement and slope are continuous; curvature/pressure can jump.

## Closed forces and stable evaluation

For active `a<=u<=v<=Ls`, divide the following force by B for force per width:

`F(u,v)=B*q*[(v-u)`
` -(sinh[beta*(Ls-u)]-sinh[beta*(Ls-v)])/(beta*cosh(lambda))`
` +T*(cosh[beta*(v-a)]-cosh[beta*(u-a)])/cosh(lambda)]`.

Clip each bin to `[a,Ls]`; empty, open or uncovered portions contribute zero.
No pressure quadrature is needed. In particular,

`Fcontact=B*q*[(Ls-a)-tanh(lambda)/beta+T*(1-sech(lambda))]`,

`Rclamp=B*[D*g0/a+q*a/2]`, and `Fcontact+Rclamp=B*q*L` follows directly
from the front equation. At `a=0` use the continuous slope expression
`Rclamp=B*q*[a+tanh(lambda)/beta+T*sech(lambda)]`.

Hyperbolic ratios use negative exponentials, never large cosh/sinh values.
For `tau=beta*(s-a)`, the cancellation-free active first term is
`(q/kappa)*expm1(-tau)*(1-exp(-2*lambda+tau))/(1+exp(-2*lambda))`.
Closed bin differences use 80-digit Decimal exponentials before rounding to
binary64, avoiding subtraction of large overflowing primitives.

## Interface, check and uncertainty proposal

`make_reference(D=...,q=.5,gap=1e-4,kappa=1e6,length=1.,supported_length=.9,width=1.)`
returns an immutable object with `displacement(s)`, `pressure(s)`,
`force_between(u,v)` and `summary()`; `gap(s)` and `derivative(s,order=1|2)` are
also available. Coordinates are scalar or NumPy arrays, measured from the source
clamp. Forces already include width.

The one fixed-candidate self-check compares the binary64 front with an independent
80-digit monotone solve, checks differentiated ODE/BC/front/cut identities and
force balance, and checks closed bins against independent Gauss integration.
Interior five-point differences retain their perturbations and errors. Numerical
self-check tolerances are not new coupled or scientific acceptance tolerances.

For later reviewer scrutiny, bound root error using the monotone Decimal bracket
and evaluation envelope divided by a lower bound on `g_required'`. A front error
`ea` produces a displacement envelope with
`|dw/da| <= q/D*[tanh(lambda)/beta+T*sech(lambda)]` on this solution; pressure
uses kappa times that envelope. A total-force front-error bound is
`B*q*(1+T*beta)*ea`. Add stable-form arithmetic and bin-antiderivative rounding
envelopes, accounting explicitly for samples close to the front/cut. Do not
transfer these arithmetic bounds to finite-mesh error or moving geometry.

The lead's distinct mesh comparison retains its declared gates; this oracle
does not alter them or regrade the retained radial timeout/NONPASS evidence.

## Retained fixed-candidate self-check

`d2_guided_partial_foundation_reference_v1_20260930.json` records the complete
checks, inputs and exact executed source identity; companion `.inputs.json`,
`.log`, `.resource.json` and `.runner.source.py` preserve the bounded command.
The one process completed in 0.281865 s at 38.801408 MB, exit zero.

Measured reference: `a=0.7564271912760346 m` (world `x=0.8564271912760346 m`),
`Fcontact=0.09903353861433664 N`, `Rclamp=0.40096646138566333 N`, balance residual
zero. Covered minimum gap is `-1.7194095417734878e-6 m`; uncovered tip gap is
`-3.279409541773487e-6 m` with zero pressure. The independently solved 80-digit
front differs by at most `4.905634684512983e-18 m`. Analytic ODE residual is
`3.33e-16 Pa`; retained finite-difference relative load residual is `8.10e-9`;
bin quadrature cross-check error is at most `2.08e-17 N`.

Helper/snapshot SHA256:
`ce407a6078eb76e01b552a6cb2353cf1b09bef847a1b2ccd5dc3adeb3c6373c1`.
These are scalar oracle checks, not acceptance of a finite-mesh contact result.
