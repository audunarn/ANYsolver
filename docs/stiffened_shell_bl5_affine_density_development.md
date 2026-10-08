# Experimental affine-density BL5 pairing

The existing `ExperimentalBL5Line` accepts the separately identified
`basis="discontinuous_p1"`. The continuous five-channel BL5 pose/director law
is unchanged. This is a development candidate, not a selected or qualified
multiplier space. Existing P0 and continuous-P1 behavior/identities are preserved.

On each support `[x_left, x_right]` all five channels use the same density:

```text
xi = 2*(x-x_left)/(x_right-x_left) - 1
lambda_c(x) = a_c + b_c*xi
constraint rows = integral(g_c ds), integral(xi*g_c ds)
```

Coefficients are physical densities, not integrated forces or display moments.
Translation coefficients have force/length units; director coefficients have
moment/length units. Recovery reconstructs the density before the actual
transpose variation map. Integration remains split at both original meshes;
neither beam nor shell is remeshed. The affine coordinate uses actual physical
support endpoints, including unequal lengths of complete members. Existing
reference-correspondence and native regularity guards still apply.

`multiplier_span` must be an even count of complete native member pairs, divide
the trace exactly and start at a member boundary. A slope mode on one constant
retained-director half-cell is deliberately inadmissible. Ten rows per support
are ordered by channel, support, constant/slope. The descriptor binds the basis,
so even equal row counts do not make P0 checkpoints compatible.

The initial complete uniform-trace development rule in
`scripts/b3_e4_bl5_coherent_aggregation_dev.py` is:

```text
span_halfcells = 2*ceil(max(1, halfcell_count/shell_trace_segments))
```

It applies to all five channels and requires exact support coverage. It covers
at least two local shell-trace lengths and a complete native member. Seven-ratio
construction checks are not seven-ratio stability evidence. Bounded reciprocal
off-ratio assembled controls, actual-update multiplier curvature, finite stepping,
station recovery and checkpoint continuation are distinct development checks.

The independent affine carrier reference constrains both displacement moments
for continuous Timoshenko normal-spin bending on the same physical supports.
Its `controls().energy` is **twice strain energy**, as in the preceding P0
reference, and is compared to full applied work. It does not model Saint-Venant
torsion, a flexible shell or a weld footprint. The one native decision screen
uses the existing 16x4/32-halfcell rigid-carrier fixture and the same 8/16/32
reference supports; no finer native mesh or formal F03 execution is implied.

Advancement requires physical transfer, shear/drilling/locking and full supported
mixed-system checks plus a justified new multiplier norm. Rank, small weak gaps,
tip agreement and the old P0 beta values cannot qualify this candidate. No
consumer or production-supported-domain expansion follows from this change.
