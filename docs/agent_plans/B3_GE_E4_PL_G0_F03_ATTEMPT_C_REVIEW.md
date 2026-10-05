# F03 attempt-C corrective patch and resource proposal: independent review

23 September 2026. The reviewer did not implement the changes reviewed here.
This review is limited to the budget-neutral four-file lifecycle snapshot and
actual sparse-union admission fixes, plus the proposed future resource contract
in `B3_GE_E4_PL_G0_F03_RESOURCE_AMENDMENT_PROPOSAL_V1.md`. It is not a G0B
mechanics acceptance, a passed registered case, or authorization to revise the
frozen attempt-C contract.

The independent code/mechanics reviewer found **no remaining finding** after
two proposal clarifications: the resident-work estimate is now an exact byte
formula, and binding/equilibrium cumulative-work ceilings require distinct
versioned fields while other exact checks retain the current 100-million-bit
limit. The reviewer checked the snapshot's four terminal-bound files, exact
copy/hash revalidation, and log-only zero-byte exception; the bounded sparse
input reservation, actual KKT-union check under the unchanged 234,772-nnz cap,
and final block-matrix check; the proposed headrooms and memory rationale; and
the preserved `FAILED_EVIDENCE` identity of attempt C. Independent focused
tests: 78 passed. No registered case was launched by the reviewer.

A second independent coordinator reviewer found no actionable issue in the
snapshot accounting and contract. The implementer's installed-package F03
selection passed 1,341 tests with four Windows symlink-privilege skips. These
checks support a reviewable corrective patch only. The five-case registered
screen and the physical line-coupling choice remain open.
