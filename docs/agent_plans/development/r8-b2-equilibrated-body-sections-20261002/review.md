# Independent implementation review — 2 October 2026

Reviewer: separate OpenAI Read worker `/root/e02_rigid_tip_runner`; not the
implementer. No numerical runs, edits, Git integration or nested workers were
performed by the reviewer. This is development scrutiny, not different-model-
family qualification or acceptance of a complete scientific gate.

The review covered the physical B2 local recovery, reference point differential,
panel typed-load/batch propagation, public facade and tests. The original
derivation was checked independently for distributed-force/couple signs,
interior jumps, eccentric shift, actual negative attachment transpose work,
endpoint closure, and the distinction between section reconstruction and loaded
interior kinematics. No equation/sign defect was reported in that derivation.

Two consequential provenance findings were raised during implementation review:

1. The compiled body-load model identity omitted the actual axis-wrench recovery
   pullbacks. Resolution: hash their bytes along with point indices/stations.
2. Submitted typed-case fingerprints omitted acceleration, model identity and
   node inventories. Resolution: include that metadata as well as the load bytes.
   A signed-zero metadata mutation leaves the applied vector unchanged and now
   triggers the changed-after-submission guard before the next case solves.

The final follow-up reported no remaining consequential finding in the reviewed
slice. It inspected final installed identity, JUnit, coordinator and example
records: 263/263, wheel `4c14d094…d3b7c`, 391 modules, actual one numerical
thread and JIT disabled. The four changed product modules match the source
manifest and installed site; the Q4/mixed/S3 typed examples complete 1/10/100
cases with one factor, separate fields and total-force balance. Retained example
bytes match the current source.

The reviewer explicitly retained these boundaries: loaded interior pose is not
reconstructed; nodal point equations are unchanged; endpoint mixed-load
resolution, GE gravity and qualification obligations remain open. Those findings
and scope are incorporated in [results](results.md). Final records are preserved
under `installed-v2/` in [raw archive](raw-v1.zip), notably `tests/identity.json`,
`tests/junit.xml`, `coordinator.log`, and `example-{q4,mixed,s3}/`.
