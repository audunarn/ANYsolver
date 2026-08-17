# E3 MITC9i Open-Theory Reference

## Result

The independent reference track is classified
`GO_REFERENCE_E3_Q9_MITC9I_PARTIAL_PACKET`.

The packet closes the COVc transformation convention, corrected Q9 shape
functions, selected shift-parameter equations, and the drilling-polynomial
classification using an open primary source plus an independent standard-library
oracle. It is partial because the paper does not print the first and second
variations needed to reconstruct a complete consistent nonlinear element.

This status has no bearing on HW29. The reference identity has no route-gating
edge and cannot block, select, or modify the Q4 study.

## Primary-source identity and boundary

The sole normative source is K. Wisniewski and E. Turska, *Improved nine-node
shell element MITC9i with reduced distortion sensitivity*, Computational
Mechanics 62 (2018), 499-523, DOI
[`10.1007/s00466-017-1510-4`](https://doi.org/10.1007/s00466-017-1510-4).
The inspected open PDF is available from the
[German National Library resolver](https://d-nb.info/1150607610/34): 25 pages,
1,302,612 bytes, SHA-256
`5C66A76D39682F71C13208E71AFFA585FD3CD1E284185360B825572DC8BA048B`.
It identifies the article as CC BY 4.0.

No PDF, page image, figure, table, or copied passage is committed. The source
map records equation ranges and short independent descriptions only.

## Extracted theory

### COVc is a centre-basis approximation

For in-plane strain, the paper replaces the pointwise Jacobian by the Jacobian
at the element centre:

```text
E_covc = j_c^T E_cart j_c
E_cart = j_c^(-T) E_covc j_c^(-1)
```

The two maps are reciprocal for a fixed nonsingular `j_c`. They are not an
exact covariance statement away from the centre: the paper explicitly neglects
the relative Jacobian between the centre and the sampling point. The rational
oracle obtains

```text
j_c = [[2,1],[0,3]]
E_cart = [[1,2],[2,5]]
E_covc = [[4,14],[14,58]]
```

and recovers `E_cart` exactly. At the registered off-centre Jacobian, the true
covariant components are `[[25/4,95/6],[95/6,425/9]]`, hence differ exactly
from COVc.

The source uses the same centre-co-basis pattern for membrane, bending, and
transverse-shear groups, followed by MITC sampling/interpolation and the
reciprocal map back. Full integration is `3 x 3`; the sampling groups and lines
are source-mapped but are not promoted into a production element here.

### Corrected Q9 interpolation

The four corner and four midside functions form a shifted eight-node
serendipity basis. The central node is introduced hierarchically:

```text
Nbar_1 = (1-xi)(1-eta) * ((1+a)(1+e)-(1+a)(1+eta)-(1+e)(1+xi))
         / (4(1+a)(1+e))
Nbar_2 = (1+xi)(1-eta) * ((1-a)(1+b)-(1-a)(1+eta)-(1+b)(1-xi))
         / (4(1-a)(1+b))
Nbar_3 = (1+xi)(1+eta) * ((1-g)(1-b)-(1-g)(1-eta)-(1-b)(1-xi))
         / (4(1-g)(1-b))
Nbar_4 = (1-xi)(1+eta) * ((1+g)(1-e)-(1+g)(1-eta)-(1-e)(1+xi))
         / (4(1+g)(1-e))
Nbar_5 = (xi^2-1)(1-eta)/(2(a^2-1))
Nbar_6 = (1+xi)(eta^2-1)/(2(b^2-1))
Nbar_7 = (xi^2-1)(1+eta)/(2(g^2-1))
Nbar_8 = (1-xi)(eta^2-1)/(2(e^2-1))

N_i = Nbar_i - Nbar_i(theta,kappa) N_9,  i=1,...,8
N_9 = ((xi^2-1)(eta^2-1))/((theta^2-1)(kappa^2-1))
```

Here `a`, `b`, `g`, and `e` denote the four midside shifts (`alpha`,
`beta`, `gamma`, and `epsilon`), not sampling-point coordinates.

The six shift parameters locate the four midside nodes and the centre in the
natural square. For a fully rational shifted case, the oracle proves exactly:

- partition of unity;
- the `9 x 9` Kronecker interpolation property;
- the two-node-plus-midside quadratic restriction on every edge;
- reproduction of all nine monomials in `Q2`.

For a flat central-node case, the independently evaluated M1 residual is exactly
`[0,0]`. For the paper's curved-side example with points `(0,0)`, `(1,2)`, and
`(4,0)`, exact interval range bounds enclose the arc-length-equation root in
`[-53/200,-33/125]`. The paper's printed `-0.264405` lies strictly inside. The
certificate uses 8,192 rational subintervals and 18-decimal rational enclosures
of every square root; its endpoint residual intervals have opposite signs.

### Drilling constraint

In the biquadratic monomial order

```text
1, xi, eta, xi*eta, xi^2, eta^2, xi*eta^2, xi^2*eta, xi^2*eta^2
```

the linearized constraint contains eight coefficients coupling rotation and
displacement. The highest `xi^2*eta^2` coefficient contains only the ninth
rotation coefficient. In nodal drill coordinates its exact row is

```text
[1/4,1/4,1/4,1/4,-1/2,-1/2,-1/2,-1/2,1]
```

Its row sum is zero, so a constant rigid drill is not grounded, and the exact
square-integral factor is `4/25`. The source distinguishes three penalty
variants:

- retaining the full constraint, used for its main reported tests;
- deleting the highest term, which introduces one additional zero eigenvalue;
- adding the deleted term back at scale `10^-3`, tested as a sensitivity branch
  and then not used for the remaining reported tests.

The paper also discusses a nine-parameter perturbed-Lagrange alternative. It is
not the tested primary MITC9i branch and is not silently merged into this packet.

## Finite rotation and remaining gaps

Within a Newton step the canonical rotation vector is updated additively. At a
converged step the corresponding quaternion increment updates the accumulated
quaternion multiplicatively. The incremental drilling expression is stated for
an increment below `pi/2`; quaternion accumulation permits larger total
rotations.

The source says that the potential is varied and consistently linearized but
does not print enough detail to reproduce, without invention:

- the first variation of the sampled Green-strain operator;
- the closed-form second variation and consistent tangent;
- the incremental drilling residual and tangent blocks;
- separated geometric stiffness or a consistent mass operator;
- load-potential and follower-load linearizations.

Those omissions are the reason for `PARTIAL_PACKET`. The packet is a theory and
benchmark reference, not a qualified or production-ready Q9 shell.

## Bounded benchmark provenance

Only source-attributed definitions needed for future comparison are retained.
For the membrane patch, the oracle independently recovers tensor strains
`[1/1000,1/1000,1/2000]`. For the transverse-shear patch, `u_z=x/40` gives
`3/500` at `x=6/25`. The paper's report of six zero eigenvalues for its tested
unsupported elements is recorded explicitly as source-attributed and is not
represented as an independent eigenvalue reproduction.
