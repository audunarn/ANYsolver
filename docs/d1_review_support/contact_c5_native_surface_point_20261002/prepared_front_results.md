# Prepared native stationary-front bounds — development, 2 October 2026

**Prepared proof controls pass locally; mixed integration remains unpassed.**

PreparedStationaryBand binds complete angular cover, branch brackets, uniform coefficient
roundoff controls, strict B and N' bounds, and endpoint bounds. Preparation consumes shared
support intervals. Per-angle queries perform bounded Brent/actual coefficient evaluation
without recomputing geometric slabs. Existing axial_contact_front still prepares validation
geometry internally; these calls are not bare scalar arithmetic or unmeasured speed gains.

For residual bound r=|N_float|+eN, m=min|N'|, L=max|N'|, dt=r/m. H coordinate uncertainty
uses padded A/B plus (r*dt+.5*L*dt²)/min|B|². All quotient extremes, identity, bracket,
endpoint sign and axial uncertainty gates remain. eN propagates product errors before
cancellation. Existing fixed-angle slab route remains an oracle/default path.

## Independent scrutiny and corrective work

Owned OpenAI reviewer accepted the displacement formula and cache identity/budget design,
but identified missing coordinate/velocity/relative-distance amplification in initial
max-scale roundoff controls. Replaced that approximation with explicit coordinate->edge->
cross-product->coefficient-dot error propagation, including C,C',C'', all six coefficients,
absolute work-map inputs, original native pose/motion magnitudes and error products. Review
found no additional concrete missing term after this correction. The large operation factor
remains a development control, not a formally verified floating-point proof.

A whole-time open-interior certificate uses A+Bxi=B(xi-H), fixed nonzero B sign and every
stationary/endpoint H interval. It must hold for every captured segment before skipping
material history reconstruction. It rejects hidden pulses even with both endpoints open.
Intervals beginning exactly at an outward extremum bound can have zero gap at an edge,
but all quadrature points are strictly interior; final >=/<= boundary convention tested.

## Retained runs

- Initial analytical/slab/identity/budget comparison:4passed.
- Initial prepared integrated candidate: failed at2048queries/4096pointpaths,panel12,
  support49.73.54s test,79.076s runner,255971328bytes sampled peak.
- Open-side proof +/-B, hidden pulses and moving target slab controls:7passed.
- Integrated candidate with strict open-side >/< test: same query cap/panel/support49;
  72.60s test,78.022s runner,255688704bytes. No speed-up/pass claim.
- Explicit propagated roundoff correction:7affected controls passed again.
- High-coordinate cross-dot amplification counterexample:1passed using Decimal reference.
- Final interval-interior boundary convention:2passed; integrated effect NOT yet run.

Ten distinct local controls pass, with changed error semantics rechecked. Both integrated
failures retain unchanged180s/953MiB,support128,query2048,pointpath8192 and other settings.
Raw logs/runtime/resources in prepared_front_results_raw.zip; final source hashes and all
resource records in prepared_front_source.json. No native acceptance/installed claim.

## Next action

One unchanged mixed-case retry is now justified by the corrected outward-bound interior
convention (previous shortcut missed intervals whose left/right edge equaled the bound).
Use ANYSOLVER_RUN_UNRESOLVED_MIXED_FRONT=1 and existing controls. If query cap remains,
retain the result and identify the dominant component/refinement demand before changing
quadrature; do not grow caps or continue blind retries. Multi-segment work and saved coupled
secondload/split restart remain open. No saved fullpatch run is authorized by this note.
