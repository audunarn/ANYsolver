# Q4 plastic impact — material ownership and restart development slice

Parent26402e72; exact final hashes and raw evidence are captured in
`contact_c6_q4_plastic_20261003/source.json` and `raw.zip`. This is development
verification, not engineering acceptance, installed admission or release.

## Discriminator and preserved boundaries

Square x,y=±.5m,h=.05m,rho=1kg/m³,E=1e5Pa,nu=.3. Exact DNV curve has
sigma_prop=sigma_yield=sigma_yield_2=20Pa,eps_p_y1=.005,eps_p_y2=.01,K=20,n=.2.
Physical coordinates are affine strain[epsilon,-epsilon,0] and rigid normal w;
their verified masses are1/120 and.05kg. Initial rates.2/s and−1m/s; initial gap
.0008m,normal regularization4e7Pa/m,gap budget5e−5m,dt2.5e−5s,end.003s.
Three layers retain accepted constitutive update parents.

Independent scalar reference uses closed affine elastic/plastic and open/contact
Newmark equations. It calls no production material/contact/solver helper.
Position1e−11m,velocity1e−8m/s,acceleration1e−5m/s²,plastic strain/alpha1e−10,
inferred stress1e−7Pa; relative bounds where stated remain in the test source.
Restart position1e−10m,velocity1e−8m/s,acceleration1e−5m/s² and core state1e−9.
Reference equilibrium retains1e−9 normalized residual. These are local development
checks; programme qualification criteria are unchanged.

## Observed source checks

51 material-packet checks pass: real nonvirgin state, compact assembler parent,
owned restoration, exact model/pose/layer/IDs, semantic tampering with repaired
hashes, effectful API mutation and unsupported lifecycle/state rejection.
Lead inspected both files and runtime evidence; a different worker scrutinized
the helper and driver. Same-family review does not establish engineering acceptance.

Ten new driver outcomes and two affected legacy outcomes pass over four bounded
runner selections, not one full-suite run:

| Selection | Outcomes | Complete elapsed | Sampled peak RSS |
|---|---:|---:|---:|
| Reference and yielded active split | 2 passed |162.54s|194240512B|
| Yielded-parent rejected path and physical-mode check |2 passed|43.15s|183205888B|
| Exception and cancellation after yield/model reuse |2 passed|158.35s|191389696B|
| Explicit admission/tool controls and two legacy restarts |6 passed|7.77s|187334656B|

Material codec:51passed,24.52s,169357312B. All final records confirm reconciled
source imports,JIT off,Numba/BLAS threads1,no runtime errors,180s/953MiB limits.
Rejected path is a controlled failed swept-gap gate after a yielded commit; the
reference follows the actual accepted cutback grid and checks no plastic-history
double counting. Cancellation/exception fire before the first yielded candidate
commit and leave the same model reusable. Both mechanisms are distinguished.

Review caught lost fingerprinting of existing moving-tool work controls and
checkpoint/material-export aliasing. Both are corrected with focused regressions.
Restart restores sealed accepted history before force balance and discards the
initial observation instead of overwriting its accepted parent.

## Failures retained

- Codec a: unsupported LinearHardeningCurve fixture; b: wrong expected exception
  type in a lifecycle test. Constitutive/lifecycle kernels remained unchanged.
- Integrated a: fixture used nonexistent Node.coordinates; b: mass tuple misuse
  and residual-only initial state missing required algorithmic parent. Plastic
  initialization now evaluates its tangent, retaining that parent.
- c: shared180s cap reached; partial outcomes do not establish a pass. Resource
  record reports190.07s including termination. No cap increase.
- d: independent Newton oracle stalled at floating-point cancellation. Closed
  affine branch solves replace that oracle, preserving equilibrium tolerance.
- e: trajectory/core state and restart comparisons reached a nonexistent
  compact-state layer_stress field. Corrected to independent elastic-strain
  stress inference; no production state invention or scientific gate change.

## Package and remaining work

New isolated wheel/example matches every numerical field and all204 imported
module hashes. WheelSHA256cb8105e15051d98531ab4513ff8897e144d26211d2e435c31ef06193e79cdd7c;
source77.89s/165937152B,installed78.95s/166027264B. Both have actual target imports,
JIT off,Numba/BLAS threads1 and180s/953MiB caps. This verifies a development
artifact, not an accepted/released package.120steps/zero cutbacks,first yield.00085s,
maxalpha8.000073671e−5; minimum represented gap−3.540065827e−5m within5e−5m.
Peak plane reaction1382.716049N; final open,unloading observed. DNV plateau
remains below.005 equivalent plastic strain.

Independent exploratory endpoint accounting finds initial energy.0251666667J,
final KE.0280013600J,elastic storage1.672767015e−5J and exact plateau plastic
dissipation8.000073671e−5J. Excess.0029314218J,or11.648%; the existing1% impact
target is unpassed. A prospective half/quarter-dt discriminator at end.0012s
tests contact release/temporal error versus work-map error under identical
mechanics. Its results are retained separately; this is not formal qualification.
Half-dt1.25e−5s gives0.26977% energy excess (96steps,64.44s,164700160B);
quarter-dt6.25e−6s gives0.46223% (192steps,120.22s,170803200B). Both end.0012s
after contact release while plastic loading continues. The base ends.003s after
unloading. This conservation discriminator uses the same initial energy, mass,
plateau dissipation and zero external work; it is not matched-end formal temporal
qualification. Source/module hashes match across all cases. Error decreases
substantially from the coarse run but is nonmonotonic between the two fine runs;
no monotonic refinement claim. Contact event phase/timestep effects are supported,
and prospective event control/matched-end qualification remains necessary.

Final independent source delta review found no new defect in direct reference
branch algebra, compact stress inference, helper/driver state ownership or the
example. It did not execute these checks independently or provide engineering
acceptance. Both review-caught concrete defects and the finite test limitations
remain recorded above.
Existing installed accepted-shell artifact remains unchanged. Full D5/C6 remains
open: coupled impact-induced plasticity, material/work accounting, refinement,
broader geometry, free-body combinations and independent engineering acceptance.
Complete profile evaluation is about78s for120 steps in these runs; no speed-up
or delivery-date claim. Do not turn the finite checks into a broader material
admission claim. Native friction remains separately restricted by the unresolved
closed-strip tangent bound; its consumed runs remain untouched.
