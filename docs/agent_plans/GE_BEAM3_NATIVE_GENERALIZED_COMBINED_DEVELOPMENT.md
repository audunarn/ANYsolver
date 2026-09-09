# Native generalized combined-couple development

Base: f785a4db4cea86d60739acc1b80274c87d39d3f7.
Add a private generalized-section spatial-nodal-couple programme and its own
complete-chain restart schema. Retain existing elemental generalized mechanics,
the distributed load pattern, stationary condensation, recovered material
resultants and all physical-fibre / B2/B3 / Q4/S3 mechanics and defaults.

Spatial nodal work is m dot delta-theta; the increment-chart force is A.T m
and its tangent is (dA).T m. Count each shared node once globally.
Combine it with the frozen reference-line and distributed spatial-couple work.
Use GENERAL factorization. Constant spatial couples do not confer a scalar
potential, conservative symmetry, modal/buckling or dynamic authority.
Do not add applied numerical/external moments to section recovery.

Port the preserved physical-fibre combined work map without coefficient edits.
Use the exact new generalized history codec, separate load policy/schema and
ContextVars; no cross-schema history inference. Validate full accepted load,
state, material-origin, shared-rotation and predecessor chains with external
SHA-256, strict canonical bytes, 2-MiB/65-snapshot bounds and 60-second replay.
Reject direct or unauthenticated restart before mechanics.

Cases retain previous generalized C/M/Y/H, line/couple densities and three
geometries. Add nodal moment (0.015,-0.01,0.008) at node 3, which is a shared
junction in the connected case. Include two increments, exact continuation,
unloading, failure rollback and work/resultant recovery. Assert plastic
evolution in both plastic fixtures; do not tune the law or loads against results.
Use a separately explicit diagonal elastic section diag(4,6,8,2,3,5), M=I,
Y=1e6, H=.6 for the analytical combined torsion fixture.

Local checks: independent Rodrigues nodal work, analytic torsion/reactions,
zero-nodal limit, fixed-node reactions, load/store/pose ownership and range
guards. Directional checks use the previously documented four-step protocol
(2e-5,1e-5,5e-6,2.5e-6), preserving every raw estimate. Fine raw and Richardson
errors must satisfy the unchanged 1e-7 limit; underresolved coarse errors
must decrease by a factor below .3 at each halving. No mechanics tuning.

Smoke before complete rehearsal, then clean implementation freeze and two
fresh deterministic cycles with byte-identical scientific outputs. Separate
local and geometry inventories, plus old distributed/generalized/fibre,
Q4 ownership and legacy B3 regressions. One numerical thread, 24 GiB per
process tree, 600-second child wall, 120-second CPU inactivity, at most three
children and 1,800-second waves. No automatic retry; preserve any failed
attempt and source before explicit correction. Independent review PENDING.
Private development only; full production goal remains incomplete.
