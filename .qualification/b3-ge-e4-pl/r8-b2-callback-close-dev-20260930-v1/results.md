# B2 batch callback-close lifetime repair — development slice

The accepted point/static mechanics source11819ab8 exposes an owner-lifetime
defect: a completion callback closes the panel, clearing its factor handle,
then batch return reads that handle for counts. The preserved unchanged-wheel
counterexample fails with AttributeError after the final case (exit1).

The repair changes only ExperimentalB2Q4PanelAnalysis.solve_linear_many.
Each numerical result supplies scalar work counts before its completion callback.
Owner closure stops before another case, returning the complete selected prefix
with cancelled status and an explicit reason. Closure after every submitted case
completed returns completed. Original callback programming/memory errors still
propagate. No local factor reference survives closure or an exception traceback.
This is the callback boundary contract, not arbitrary concurrent owner closure.

First candidate wheel2c9ba0f9... passed67/67 but retained the factor handle during
callbacks; independent review identified that lifetime limitation. The final
scalar-count candidate wheel
0a7532a62f4b03ccc718a391f7a21d571dd917a2f01deac7cb745fee5ba87e8b
passes67/67 installed (48 B2/19 ANYfem), including eight new consequences checks:
intermediate/final closure, closure plus cancellation, exact physical selections,
one factor/no later solves, idempotent closure, further-solve rejection and
original RuntimeError/MemoryError identity. Weak-reference assertions establish
factor release inside callbacks and with the original traceback retained.

All386 solver and97 unchanged consumer modules match source/wheel/site;
267 observed imports are onsite. Consumer wheel e3f755fe... is unchanged.
Python3.14.2, one effective numerical thread, JIT disabled. Final pytest8.08s;
guarded route12.440432s/224030720B peak, exit0, no resource failure. These are
verification costs, not a paired speedup or large-model performance claim.

AST comparison against11819ab8 proves only solve_linear_many changed;
385 other kernel modules are byte-identical. Reuse the prior75 unaffected
GE/L1/fibre/finite regressions and65 accepted point/static scientific cases
only at their unchanged mechanics scope. New source requires and received fresh
B2/consumer artifact verification. Independent source/artifact/result review is
recorded in review.md; aggregate F13, M3, G0B and the programme remain open.

The before-fix failure, superseded passing-but-reviewed V1 and final V2 raw
logs, inventories, inputs, installed identities and wheels are preserved together.
