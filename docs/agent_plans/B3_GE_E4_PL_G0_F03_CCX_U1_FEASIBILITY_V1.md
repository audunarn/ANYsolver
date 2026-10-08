# F03 external U1 beam feasibility: exploratory execution

21 September 2026. **U1 beam-only execution and mesh-refinement checks;
not a coupled F03 reference or any G0 acceptance.** The two committed
runner identities are `06358fd` (one-element smoke) and `cc509d4`
(five-mesh refinement). The source SHA-256 values are respectively
`ed320a695ae1adad5232525f0f8b85ab0d656ec75f07f04923c15c6f83397620`
and `710b578be9f619a3025c7d1ca9e36c8cc495503340cc3ec13ca570d9f29b5370`.

Both invocations used the executable under
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/calculix-223/CalculiX-2.23.0-win-x64/bin/ccx.exe`,
SHA-256 `27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f`,
with `OMP_NUM_THREADS=1`, a 120 s per-process limit and exclusive case
directories. Complete input, DAT/FRD/STA/CVG, stdout/stderr and parsed
records remain under the exploratory roots
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-ccx-u1-smoke-v1/`
and `.../f03-ccx-u1-mesh-v2/`. The smoke `result.json` SHA-256 is
`c395446823a5bb3f253b3d6ee85ce804aa56d4b5cee275a31c3acb6093f840dd`;
the mesh `summary.json` SHA-256 is
`a1e325a143747dd508eee94092e3f7726f0770a2a7bbc7855fce092e47a35707`.

The beam is a one-metre, root-fixed U1 general section with `E=210 GPa`,
`ν=.3`, `A=.01 m²`, `I11=I22=8.333333333333333e-6 m⁴`, `I12=0`,
Timoshenko shear coefficient `.8`, and a `+1000 N` terminal y-force.
Analytical Timoshenko tip translation is
`F L³/(3 E I) + F L/(k G A) = 0.00019202380952380952 m`;
rotation is `F L²/(2 E I) = 0.00028571428571428574 rad`.

| U1 elements | Parsed tip `uy` (m) | Relative translation error |
|---:|---:|---:|
| 1 | `0.0001860282` | 3.1223% |
| 2 | `0.0001865455` | 2.8529% |
| 4 | `0.0001879511` | 2.1209% |
| 8 | `0.0001900139` | 1.0467% |
| 16 | `0.0001913596` | 0.3459% |

All five cases exited zero, reported `Job finished`, had empty stderr and
one completed static increment. Parsed terminal `rz` was `0.0002857143`
in every case, consistent with the analytic value to DAT precision. The
tip translation improves monotonically with refinement; this is not a
certified asymptotic convergence study. The one-element result is **not**
an accurate standalone reference. Independent read-only review matched
five terminal displacement rows to the preserved DAT files, checked the
analytic shear and bending terms, solver hash, deck inventory, and exit
records. The parser is scoped to this one-step DAT layout.

The smoke deck's `*NODE PRINT RF` produced `-937.046 N` at both root and
loaded tip, which cannot be read as a valid support-reaction balance for a
`+1000 N` tip load. Its `*EL PRINT S` was not independently interpreted
as physical generalized resultants or energy. The refinement decks
requested only DAT `U`, so their FRD files have no displacement result
field and they provide no verified reaction or energy output. A coupled
external route must establish independent balance and energy extraction.

The [official U1 test example](https://github.com/calculix/examples/blob/master/ccx/test/userbeam.inp)
supports this deck syntax and the [CalculiX manual](https://www.dhondt.de/ccx_2.22.pdf)
documents the general-section parameters. These exploratory runs do not
validate a shell, four-sample pose map, continuous multiplier coupling,
signed smooth/sine loading, mixed result recovery or the required external
comparison. F03/G0B remain open.
