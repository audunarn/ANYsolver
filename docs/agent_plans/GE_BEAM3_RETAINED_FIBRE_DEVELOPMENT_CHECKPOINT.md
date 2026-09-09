# GE-B3 native retained-fibre element and state — development checkpoint

Parent `3f017c6df8ad6d5c4b66bc4ea6e13b958c3da7f7`, tree
`2ca35de89f0edf2461bd6fbd6fda37b21d874592`.
Independent scientific review **PENDING**. Production qualification **false**.

## Native FEModel integration

The new private `NativeRetainedFibreElement` is a real `Element` container in
`FEModel`: three nodes, six external DOFs each. It does not inherit from
QuadraticBeamElement, wrap legacy corotational mechanics, masquerade as the
older directed-plastic element, or enter an existing beam batch path.
Its descriptor binds element/node IDs, section, reference, quadrature and the
coupled fibre operator. Model capture rejects changed ownership, geometry,
sections, boundary/DOF maps, formulation/provenance traits and unsupported
mixed-element, activity or MPC layouts. Ordinary stiffness/mass/geometric,
nonlinear/internal-force and stress routes fail explicitly; only the private
retained-fibre driver is implemented. The descriptor is not a qualified generic
model-interchange serialization format.

For the preserved centered kinematics `k(q)` and fibre conjugate `Psi*(p)`,
`Pi(q,p)=p.k(q)-Psi*(p;origin)`. With `J=dk/dq` and
`G=sum_i p_i d2k_i/dq2`, the complete residual and tangent are

`r=[J^T p; k-gradient(Psi*)]`,
`H=[[G,J^T],[J,-Hessian(Psi*)]]`.

The 42-variable local saddle uses 18 nodal coordinates, six internal cell
rotations and 18 internal forces/moments; it does not add nodal DOFs. The new
operator uses analytic SO(3) derivatives and the actual coupled material
potential. Paired material gradients/compliances remain paired through local
construction. Physical fibre recovery carries native work-conjugate strain,
stress, history and current/reference frames.

## State and transaction contract

`GE_BEAM3_RETAINED_PHYSICAL_FIBRE_ACCEPTED_CHAIN_V1` binds a new history chain;
older directed-plastic or elastic capsules are not a cross-formulation restart.
Only geometric `make`/`advance` operations and their immutable array state are
reused from the earlier retained layout, not its assembly, recovery, material
law or checkpoint implementation.

The complete model and program are captured before execution. Origins remain
fixed within each global trial. A state is staged only after equilibrium and
compatibility satisfy `1e-11`; its proposed histories, reactions, recovery and
material hashes are assembled into a canonical capsule before the single
publication point. A failure/cancellation before publication preserves the old
capsule. Cancellation after publication preserves the newly accepted capsule.
Cheap cancellation/deadline checks enter material arithmetic; full model guards
run around assembly and publication, not at each inner arithmetic operation.

Replay rebuilds every accepted record from the previous accepted fibre history,
checks its physical response and regenerates the exact capsule bytes. It does
not advance geometry or rerun Newton load steps. Duplicate/nonfinite JSON,
noncanonical bytes, foreign models/schedules/histories, altered state/reaction/
recovery data, invalid paired histories and rewinds fail closed. Optional
external byte-hash authority protects metadata, such as iteration counts,
that physics alone cannot prove. The capsule limit remains 2 MiB.

Private development bounds: at most 256 assembled coordinates, 120-second
cooperative controller/context deadline and the previously bounded cell solver.
The tested program has 24 maximum global Newton updates and at most eight
backtracks. These are small correctness runs, not benchmarks, formal resource
executions or claims about engineering-model throughput.

## Separate inventories and deterministic evidence

- Initial operator/container checks: 11 passed, 4.084 seconds.
- Assembled loading/reversal/restart smoke: 2 passed, 105.635 seconds.
- State guard lane: 30 passed, 28.780 seconds; two assembled tests deliberately
  excluded from this lane because they had just run in the smoke inventory.
- Expanded complete development suite: 50 passed, 144.266 seconds.
- Final frozen cycle A: 54 passed, 146.243 seconds, no skips.
- Final frozen cycle B: 54 passed, 145.727 seconds, no skips.

The final cycles have **13 byte-identical JSON pairs**, including full/paused
checkpoints, physical recovery, accepted-state progress and operator checks.
They cover a curved two-macrocell model at contrasts 1 and 10^12 through seven
loading/unloading/reversal targets. Resumed and uninterrupted capsules agree
byte-for-byte. Accepted spatial force and moment balance uses current lever
arms. The largest accepted normalized metric is `1.1383291045689652e-12`; the
largest observed Newton count is 5, and the largest full capsule is 135,411
bytes. Local order-8 station/recovery coverage is also checked; assembled
history campaigns here use order 4.

The final provenance guard was added after same-author review of the 50-test
version; both final cycles test it. None of these checks constitutes independent
scientific review. No resource request was created, consumed or reused.

## Preservation and next work

Archive: `C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-retained-fibre-development-20260907-b0d6fb843241`.
64 content files, 2,674,957 bytes; manifest 10,175 bytes, SHA-256
`12524faf14b5f890a9a02444c55a7066f100dd2f17934bfb081a2a936f0650a8`.
All inventories and original external test outputs are preserved. Final source
hashes bind the last two 54-test cycles, not all earlier source variants.

Next extend the fibre driver to explicit-policy current-state mass/modal and
buckling operators, retaining the distinction between frozen material history
and last-increment algorithmic diagnostics. General nonlinear coupled sections,
measure-consistent material adapters and perfect-plastic limit cases still need
qualification. Distributed loads/couples, cutback/arc-length/postbuckling,
broader straight/curved/slenderness/arch/ring campaigns, generic interchange,
package/performance gates, independent review and objective eccentric/curved
beam-shell connections remain required. No existing B2/B3/Q4/S3 mechanics,
public selector, default, package version or release changed.
