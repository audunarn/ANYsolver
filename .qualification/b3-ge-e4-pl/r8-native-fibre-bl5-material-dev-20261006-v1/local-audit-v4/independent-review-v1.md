# Independent Read review of local material audit

Disposition: source and saved results support fixed-origin local constitutive compliance and an ordinary ELASTIC-to-PLASTIC_NEGATIVE onset for the identified fibre at the sampled last point. No concrete local-audit mechanics defect was found. This does not establish the assembled derivative, the cause of global step rejection, convergence, or material/programme qualification.

Scope: non-author OpenAI fallback Read review, 2026-10-06. No numerical imports/evaluations, solver calls, product changes, Git operations, alternative backend or arithmetic reproduction. Only this new note is written. Saved reductions were inspected, not independently recomputed.

## Inspected identities

- Executed `executed-tools-audit-v1/audit.py`: `df2f2af159b15d0247a2c35a08815010d81d0b7244a20b263dbbefb3235dcda4`.
- `summary.json`: `93c861ded8b407933d294765eccfc9afb5bf3a99800cb39c62df9319711e5ba0`.
- `audit-v1/result.json`: `2b03245ae489bfae79404f60bd40c1c2707acde87f67d036f356aab055009d65`, also bound by summary.
- Member1 base/positive/negative/last: `32227755cfb03dfb7b4d518375dc7d25016c81412c528ec0c26bc10eb5d3ba89`, `fe90984cd4233545b98e85639d5847019c1bb2225545d5e85a75bec58d09be97`, `7812c351354056c7c21e7e1f07ba22e745b17b815ab7a7327b54c4bb429190a7`, `e44e8ad8045ea4599fc6f764d3fc16e95b3b3404a85dd16e66477361d3015cfc`.
- Member2 base/positive/negative/last: `d4df3a9054ade0fbd9f8fcbf084d7d405e61358f92977a64485a4914745b6e21`, `da57cbd713ad0c1d4a0c8802e301b0131fdbd94138135709e533d3f25dd105a0`, `33e270a51fa88864c049194c6a8350c9d30ef6d8ac2041144c0b6518bd318179`, `ef526ae26f00fbf594e51d56eb92a9aef0b9e49a1bc295fa48a75b08510c679a`.
- Current fibre/generalized cell sources: `619ea47cdd6c4ba7a4872220b359cd87127b93f85d1078e88f17d055aad5e01b` / `09152a2111c5af025c56da3db5dfc7200cfea3b1c5e84d1b3a69f2cf510a3421`.
- Finite driver: `2c15cde96cee7facf5b0bd88f33504804a298b6b22bd615dfb983862352332a1`.

## Input representation, origin and isolation

The perturbation inputs are ordinary binary64 NumPy multiply/add: p0 plus/minus1e-4 times the saved retained direction, followed by a float list into the existing cell response. These are not compensated high/low input resultants. They follow the same retained-resultant update structure as `_advance`, which forms delta=amount*increment and then adds delta to resultants. The last point is the actual saved evaluation130 resultant array. Paired high/low output gradients and Hessians are combined and reduced with Decimal precision80; that improves the diagnostic reduction of the existing response, not the driver's input precision or its assembled arithmetic.

Preparation creates one owner and restores the accepted .284375 prefix, checks exact checkpoint bytes, then captures `driver._beam_origins`. These are the accepted fixed origins used by the failed pending increment, not its older predecessor histories. Every local response uses the captured origin; object identity, canonical origin bytes, generation and checkpoint bytes are checked unchanged. The audit calls the two existing native cell implementations, not an alternative constitutive law.

Call records show eight audit-phase cell responses, four per member. Preparation also records five compile-stage callbacks and six restore-stage callbacks, including one full replay assembly and two fibre-cell responses during restoration/recovery. Eight does not mean only eight inner material evaluations: each coupled cell response reports its own local iterations/evaluations. Audit-phase retained-operator and global assembly calls are forbidden; global solve/fixed continuation are blocked. This isolates local material response without re-evaluating the failed global pose.

Execution reports completed/exit0, 2.875s, sampled peak166060032B and one sampled numerical/unresolved process. Runtime binds NumPy2.5.3/SciPy1.18.1/Numba0.68.0/llvmlite0.50.0 to the intended CI tree, affinity[0], JIT disabled and numerical pools at one thread. These are recorded controls, not a resource qualification.

## Meaningful local results

The selected coordinate weights are the actual owner scale slice for the eighteen retained coordinates. Positive compliance is compared to the derivative of its conjugate gradient; the cross-branch defect/jump uses negative signs consistently with the assembled compatibility residual k-minus-gradient.

The weighted expected derivative norms are11.2358205 and38.2687416, both above the denominator floor1. Reported nominal-direction errors1.5111e-11 and2.2076e-11 therefore pass the1e-5 criterion meaningfully. Effective-rounded-input errors around2.57e-28 and5.24e-29 test the locally affine map at the actual rounded input secant; they are not independent whole-chain accuracy certificates. High/low output-pair truncation and the existing local solve remain part of the evaluated production path.

Both members have explicit stable base/plus/minus branch labels. The generalized member remains elastic. Fibre member station0/fibre_id1 is ELASTIC at base/plus/minus and PLASTIC_NEGATIVE at the saved last point. Reconstructed trial margins are approximately-2.3461,-.9711,-3.7211 and+21.217Pa, with negative trial drive and100000Pa radius. The returned response labels and margins support an ordinary negative yield onset, rather than a hardening-knot or an ambiguous boundary sample. All sampled responses report CLASSICAL_SMOOTH_BRANCH. The margin-derived crossover is near.000170624450442 and the signed material secant consistency is approximately4.39e-11; these are observed local comparisons, not a certified global event locator.

## Remaining limits and next decision

Passing local compliance does not prove that every assembled FD discrepancy is noise. It leaves pose/chart derivatives, line terms, global assembly/scaling and the binary64 KKT correction outside this local derivative check. A local endpoint compliance jump does not bound finite geometric residual curvature. The local event is supported at the sampled constitutive points, but uniqueness of an event along the whole global step and success of a branch-crossing Newton correction remain unproved.

This evidence supports considering a branch-informed trial amount within the existing trial budget and strict actual-global-merit acceptance. It does not authorize a run or justify changed laws, tolerances, floors, controls or accepted histories. The same global equilibrium/compatibility checks must judge any proposed step. No automatic arithmetic/refinement cascade or material/programme acceptance follows.
