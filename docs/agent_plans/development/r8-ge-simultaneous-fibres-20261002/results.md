# Two-stiffener simultaneous material history — 2 October 2026

Delivered development behavior: a runnable public GE example and focused lifecycle regression exercise two parallel native stiffeners, physical beam-fibre plasticity and Q4 J2 plasticity in the same accepted increments. Installed execution and separate source/evidence review pass. This closes a missing development test, not aggregate G3/M4 acceptance.

The 2 m by 1 m panel has two Q4 elements, four B3-GE elements and six objective eccentric six-pose point bonds. One two-element member has four physical fibres; the other has an elastic generalized section with matching virgin axial/bending stiffness. Physical-fibre elastic background supplies only shear/torsion. Shell strength is 1 MPa; one fibre per section yields at 100 kPa. These deliberately low strengths exercise history and are not a steel design. The public example declares per-member endpoint forces 1500, 375, −1500 and 1650 N. Static inertia metadata confers no dynamic qualification.

## Observed behavior and checks

Accepted positions are .5, 1, 2, 3 and 4. Actual shell-alpha increments and actual last-step fibre plastic increments are simultaneously active at 1, 3 and 4. Reversal is checked against signed fibre flow and current fibre stress, rather than inferred from the load sign. The unloading stage also has fibre plastic flow; it is not elastic unloading. Generalized-member material histories remain exactly elastic while its retained resultants are nonzero.

The test checks the complete compiled station/fibre inventory, compensated signed/accumulated histories and unique finite energy records for both physical elements. Independent integration of station measure × fibre area × initial flow strength × absolute plastic increment matches the reported incremental fibre dissipation. Shell stress/plastic-strain work is checked locally. These checks do not establish a global energy balance or a plastic potential.

Physical force/moment balance includes the actual deformed moment arms. Equilibrium is at most 5.84e−9 under the unchanged 1e−8 criterion; constraints satisfy 1e−9. Full histories are captured before assertions. Lifecycle checks cover:

- A propagated exception after a simultaneously yielded trial, preserving accepted state and callbacks.
- Numerical rejection at positions 4 and 3.5 with halving/exhaustion, preserving the accepted prefix.
- Cancellation after positive-dissipation candidate recovery, before atomic publication; candidate arrays are retained.
- Actual shell-chart rotation reset from a nonzero chart to zero, generation 4→5 at unchanged position 3, identical irreversible histories and physical-state parity.
- Prefix restore, continued accepted histories, chart-rebased/restored continuation and exact final checkpoint equality where promised.

The public example completes the staged programme and reproduces its final checkpoint from a restored prefix. No solver product code, law, tolerance, selector, default or package version changed.

## Source, installed execution and retained failures

Product base613e43f7 / checkpointb4c10f00. Final example SHA `f9d156f71faab5f3596d923c05b95a834a720e15212573fc7231ca8e0a92f761`; test SHA `5430cef09a45dde798ddf6812c7b37e53ed0bddbc43a07c01d3433d94896f3f8`.

Reused unchanged solver wheel SHA `4c14d0942410f97b6e2ab397eb0d4e567cbff4169c05b391c5685c4df40d3b7c`. All391 product source/wheel/site modules match; both installed runs record213 imports from that site. Python3.14.2, effective numerical threads1, JIT disabled; complete dependencies and commands are in the raw records. Serial600s/1GiB supervision:

| Execution | Result | Full route seconds | Sampled peak process-tree bytes |
|---|---|---:|---:|
| Final installed lifecycle test | 1 passed |119.0302|180449280|
| Installed public example | completed, restart identical |74.3341|155455488|

These are execution costs, not a performance claim. Pytest emitted one harmless record_property/xunit2 reporting warning, retained in the log.

The initial500N/member fixture failed the intended simultaneous-activity assertion. Captured shell alpha remained zero and maximum layer stress459327.6 Pa was below the unchanged1 MPa law; the fibre was active. The revised load history activates the intended physics without changing laws or acceptance criteria. The initial unsupervised example has no retroactive resource/configuration claim. The bounded activation failure and a subsequent passed source-test predecessor remain retained separately from the final installed test. Review then strengthened inventory, real rebase, rejection and cancellation coverage; only the final installed run verifies those additions.

[Raw manifest](raw-v1.json) binds152 files in raw-v1.zip, SHA `45d4776f1c7e57696bfcd5a13a2674ceb0e56d634c7eae5cd90abad2ec7ea018`. It includes exact source variants/fixtures, full accepted/candidate states, commands, resources, imports and supervisor. Archive-member hashes were rechecked. Payload scan against the three known current inherited credential values was clear. The separate historical dissemination restriction remains; this scan does not remediate that history. The unchanged wheel is retained with the preceding B2 installed evidence and is not recopied.

Separate Read review is recorded in [review.md](review.md). The reviewer did not implement the slice. This is independent source/evidence scrutiny, not a different-model-family qualification claim.

## Next action and remaining scope

Integrate the example into the existing ANYfem native Project/staged input workflow and verify save/reopen plus accepted-state continuation. Do not repeat this unchanged installed campaign. S3 simultaneous plasticity, general biaxial loading, large noncommuting rotations, typed recoverable material failure, successful cutback histories, physical external accuracy and the full material/attachment envelope remain open. No line-law finding, F03 authority, aggregate gate or release status changes. The complete Revision8 goal remains active.
