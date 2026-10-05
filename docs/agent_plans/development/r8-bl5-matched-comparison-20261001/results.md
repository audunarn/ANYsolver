# Matched force/normal-torque comparison — 1 October2026

**The two discrete models solve their own problems correctly, but their physical
response difference remains unallocated.** No line-law/space selection, converged
1% accuracy, locking claim, formalF03 execution or aggregate acceptance follows.

Source parent5bee12f6; external runner SHA6e1b3f25c2b479e1ade3700b57d996cef2f9709812a72108ce7e6a41e346293a,
native collector SHA92fa4515f1c61008f24bafe932e8fa2c50ea298903f2a1e5499e5be6c7dfaefb.
Native installed wheel0c45666609355e654cb726a0e4e0780d386bccfaafef1209ffd994bdd3b9d09c
binds388 module bytes. Original exact sources, commands, loads, full poses,
element covectors, retained variables, constraints, multiplier/reaction work and
all window conventions remain in [raw](raw/); [manifest](manifest.json) binds them.

Matched physical idealization:1m×.2m×.035m plate,16×4Q4 cells;32 beam stations,
same generalized section stiffness and material values, shell surface z0,
shell-top connection z.0175m, beam axis z.0675m, beam arm−.05m, same frames and
direct-root supports. The declared five-channel line ties positions/directors
and releases normal spin. External ASDShellQ4/Timoshenko has160 strong nodal
rows; native E4/B3 retained-halfcell c2 has40 weak rows. These mechanics and
trace/enforcement discretizations differ. Coincident stations do not make them
the same numerical operator. HistoricalQ6/six-channel pad references are distinct.

| Load | External applied work,J | Native applied work,J | Signed difference | Common nodal L2 beam/shell |
|---|---:|---:|---:|---:|
| Fy100N | .000412809790 | .000422027754 | +2.232981% | 3.370203% /3.440803% |
| Mz10Nm | .000015692921 | .000017693395 | +12.747623% | 6.633234% /4.067946% |

Work is qᵀF, twice linear elastic strain energy. The field comparison integrates
common nodal Q1/P1 translation and infinitesimal orientation fields with declared
1m scaling; it does not identify external nodal rotations with retained B3 cell
rotations or establish a physical energy norm. Native complete-domain rigid
virtual work includes those cell coordinates; nodal beam forces alone omit torque.

External recovered equilibrium/work/cut predicates pass through3.14e−12;
separate virgin derivative controls have worst4.059e−10 against their1e−6 limit.
Reference consistency, common rigid motion and free normal spin checks pass.
Native physical/recovery predicates pass through9.53e−13, weak gaps through
5.32e−22; each owner reports one factorization. Global ground balance agrees.
These predicates establish correct discrete solves/recovery, not physical accuracy.

Sharp fixed-region cuts retain open/closed/endpoint atoms separately. External
Mz open15.9234 versus closed−6.28047Nm includes−22.2039Nm endpoint atoms;
native distributed measures have no such atoms. Smooth unit-peak regional Mz
is1.421665Nm external versus1.483540Nm native. No preferred sharp-cut convention
hides the discrepancy. Polynomial moments and all raw actions remain available.

Independent complete source/raw review finds no consequential sign, root-role,
retained-variable, window or field-integration defect. Its findings retain all
scope and resource limitations; review is preserved beside this result.
Native cases take5.199/5.170s, sampled peaks170983424/172384256B, verified one
effective BLAS/Numba thread/JIT disabled. External cases takeabout.277s; requested
OMP/MKL/OpenBLAS=1 is **unverified effective numerical thread count**. A separate
getNumThreads probe returningNone does not repair that limitation. No runtime,
resource-performance or speedup qualification is claimed. CalculiX remains mandatory.

## Resulting action

Do not add a mesh or change the native law based on these values. Prepare one
controlled enforcement discriminator: hold external elements, material, geometry,
roots, frame and Mz load fixed, replace only strong rows with exact work-conjugate
P0 integrated rows over the same eight c2 supports. Verify actual P1/Q1 trace
integration, director/offset maps, rank/work and complete actions before use.
This is ordinary prospective bounded development under Revision8, not formalF03;
its execution still requires the existing resource/authority conditions.

If changing only external enforcement substantially changes its work/transfer,
that quantifies enforcement sensitivity in that model; residual native difference
still needs operator allocation. If it has little effect, prioritize beam/shell
same-action comparisons. An invalid work map stops the comparison for repair.
Neither outcome alone establishes engineering fidelity or selects a multiplier
space. Existing c1/c2 refinement and kernel evidence must be interpreted together,
with three-level accuracy, locking/drilling/torque and full ratio obligations open.
