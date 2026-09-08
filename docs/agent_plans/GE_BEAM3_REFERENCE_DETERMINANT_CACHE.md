# Reference determinant reuse successor

Base ed91ffe1abf0a4843b8cf4636e4442e784e46c41, tree
60c8558e005504a3568fb2cd839d41c35bf233a9. Three research-only paths:
this plan, ge_beam3_continuum_frequency_shooting.py,
test_ge_beam3_reference_determinant_cache.py. No production edits.

Preserve the blocked 4b16e14 group rehearsal and all historical failures.
Its straight-diagonal ODE13 eighth-root solve exceeded 60000 callbacks.
The bracket sign precheck and Brent each recomputed the same deterministic
endpoint integrations. Cache determinant scalars with exact binary64 keys
inside each solve. Do not cache failures or merge neighboring keys. Check
the existing time/callback budget even on a cache hit. No global cache,
physics approximation, changed root iteration or relaxed resource budget.

All equations, sections, masses, geometry, integration methods, tolerances,
groups, coverage and criteria from GE_BEAM3_NATIVE_MODAL_GROUPS.md remain
unchanged. Rehearse only under a new clean freeze, with no historical retry.
Compare completed straight-coupled and curved-coupled science against the
4b16e14 archive: every non-reference scientific file must be byte-identical;
reference files must match exactly after removing only the callbacks field,
which must strictly decrease. No other ignored field or numerical tolerance.

Separate inventories: cache local six tests/six scientific files; group local
13/13; inherited reference local12/four; each of three geometries one/eight.
All local smoke inventories precede at most three parallel geometries.
Only if every rehearsal and historical comparison passes, two fresh-directory
repeats of all six inventories, byte-identical science separately per lane.

Retain one numerical thread, 24 GiB and 600 seconds per worker, 120-second
CPU inactivity and 1800-second whole-wave bounds. No automatic retry.
Failed output is preserved; failed reference blocks engineering conclusions.
A native contradiction is NO_GO_GE_BEAM3_MODAL_OR_BUCKLING. A passed successor
establishes these registered comparisons only, not production qualification.
Independent review remains PENDING. Full beam and shell-connection scope
remains active. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
