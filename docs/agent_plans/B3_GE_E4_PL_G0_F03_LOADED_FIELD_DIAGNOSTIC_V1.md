# F03 classical comparator: distributed-load interior correction

21 September 2026. **Exploratory operator diagnostic only. F03/G0B remain
open.** This corrects a known limitation of the independent *classical*
finite-station comparator; it changes no ANYsolver product operator, existing
candidate, frozen v5 source, or historical evidence. The source is
`scripts/probe_b3_ge_e4_pl_g0_f03_loaded_field_v1.py`. Its commands print
complete JSON but the observations below are not a registered qualification
run or an independent physical acceptance target.

For each conventional Timoshenko element, solve a zero-endpoint particular
field for the declared distributed load. With `B=EI`, `k=G*A_s`, element
coordinate `x`, and `I_m(x)=∫[0,x](x-t)^m q(t) dt`, it uses

```text
V(x)       = V0 - I0(x)
theta(x)   = (M0*x - V0*x^2/2 + I2(x)/2)/B
v(x)       = M0*x^2/(2*B) + V0*(x/k-x^3/(6*B))
             + I3(x)/(6*B) - I1(x)/k
```

The two right-end conditions `theta(h)=v(h)=0` determine `M0,V0`;
the left-end conditions hold by construction. The field satisfies
`V'=-q`, `B*theta''=-V`, `v'=theta+V/k`. For constant `q`, an independent
closed-form check compares `v=q*[x^2(h-x)^2/(24B)+x(h-x)/(2k)]` and
`theta=q*x(h-x)(h-2x)/(12B)`. A separate strain quadrature verifies that
the bubble's energy equals half its external work for constant, smooth,
and signed sine loading at one, two, and eight elements. The 24-point
quadrature approximates the trigonometric convolutions; no certified
quadrature or continuous-gap enclosure is claimed.

All comparator ties are located at beam nodes. The particular has zero
pose at every tied station, so the original nodal KKT solve, multipliers,
support reactions, and nodal convergence are unchanged. The corrected
beam response and shell/beam gap *between* stations do change. The exact
homogeneous and bubble fields are energy orthogonal; adding bubble energy
and load work preserves the total doubled-energy identity. The former
cubic-extrema diagnostic does not apply to the trigonometric load field;
this source reports only sampled gap **lower bounds**.

Focused comparison against unchanged v5 source, using its same nodal
solve, gave:

| Case (shell/width/beam, load) | Tip change (m) | Added beam energy (J) | Old → corrected sampled transverse gap (m) | Old → corrected sampled yaw gap (rad) |
|---|---:|---:|---:|---:|
| Q4 2/4/2 smooth | `1.08e-19` | `41.142` | `3.207e-6 → 1.422e-4` | `2.067e-5 → 5.920e-4` |
| S3 8/8/8 sine | `0` | `0.54146` | `2.233e-7 → 3.015e-6` | `3.240e-6 → 1.073e-5` |
| Q4 8/64/8 smooth | `3.39e-21` | `1.13829` | `1.533e-6 → 5.238e-6` | `2.762e-5 → 3.317e-5` |

The Q4 64/64/64 smooth case retains the v5 tip `3.11584144548e-5 m`.
Its added energy is `0.0162594 J`; the corrected sampled transverse gap
is `7.03092e-7 m` and yaw gap `3.50344e-6 rad`. Its total energy-work
relative error was `3.48e-15`. This illustrates that the omission can
badly distort coarse off-station gaps while becoming small with beam
refinement. It **cannot** repair v5's nonconverged nodal trend or supply
the required physically matched, independently converged response.

Independent read-only mechanics review checked the field equations,
constant-load solution, equivalent nodal action, energy orthogonality,
and its inability to change station-tied nodal results. Next F03 work
must still derive a mesh-local signed trace/dual norm and obtain an
independent converged physical target for the actual six-channel native
coupling. No line multiplier space is selected by this diagnostic.
