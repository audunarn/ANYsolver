# Independent numerical/source/artifact review — 1 October 2026

A separate Read worker reviewed the original contract, bounded correction,
admission delta, tests and retained complete artifacts. It did not execute
another solve or edit implementation. Optional local/Mistral worker availability
had failed previously; this OpenAI review is not a different-model-family claim.

No blocking defect was found for the limited same-system local derivative.
With r=Ax-b, the correction solves A delta=r and stores x-delta. Nonsymmetry and
indefiniteness do not invalidate that operation; convergence is not guaranteed.
Frozen A/Kn/RHS/initial-iterate dependencies are preserved. The screen only claims
backward-error repair; the assessment ignores that verdict and cached residual,
checks the actual stored binary64 vector, and runs all original physical guards.

Finite-denominator admission prevents false zero ratios from overflow. Exact
RHS, finite binary64 layout, owned arrays and original failed-V1 bindings prevent
candidate substitution from bypassing the mechanical system. The six source
tests establish those boundaries, not numerical acceptance. Exact confirmation
checks residuals and positive-sum denominators on twelve distinct rows, including
both original failures and all current worst rows. Their denominators remain
essentially unchanged; the reduction reflects repaired defects rather than
denominator inflation. Candidate and assessed arrays/RHS agree exactly.

The complete controls support admitting this local derivative. Work accounting
is one repair factorization, one additional correction and zero assessment
factorizations. Original failures remain failed; reused reconstruction parity
retains its unavailable numerical value. The measured slope and tiny work
change under correction are consistency observations, not forward-error bounds.

Counterexamples retained in the interpretation: sub-ulp corrections may stagnate;
ill-conditioned factors may amplify some constraint defects; a near-null drift
can improve a backward metric without establishing forward sensitivity accuracy.
No small global work norm can override a failed rowwise control. No finite
removal, drilling independence, external-discrepancy attribution or aggregate
M2/F03 acceptance follows.
