# Experimental BL5 consumer project slice — 2 October 2026

ANYfem local commit `8c411ec`, solver `09670001`. Experimental behavior only;
no aggregate acceptance, connection-law selection, F03 consumption or release.

The existing BL5 panel now has a separate objective-Q4/staged-v2 input identity.
Historical v1 serialization remains unchanged. A distinct native Project analysis
stores explicit line definitions and programmes, rejects unsupported generic
options and selector mutations, and creates the public solver owner. The helper
closes its owner after success/failure. Persistent continuation uses the solver's
opaque checkpoint, including programme identity and chart state.

Verification: 49 source consumer/installed solver checks passed in 23.593 s,
peak sampled process-tree memory 189464576 bytes. Then 70 installed checks passed
in 171.131 s, peak 232927232 bytes. These cover new strict schemas and Project
lifecycle plus existing standalone point/material/BL5 and Project regressions.
Signed-stage cancellation, rebase, restore and continuation reproduce checkpoint
bytes and physical beam positions. No failure occurred in these two runs.

ANYfem wheel SHA256:
`f591ca10417028daa74f84f1a29e442fa421868b5aaf037811985bdc86d54ea7`.
Solver wheel SHA256:
`d506e3f339bac1acc4c8475f394062955431386a1025503ac2ae12667b14be90`.
All 98 consumer and 398 solver modules match source/wheel/site bytes. All 283
imported solver/consumer modules came from the isolated installed site.
Windows/Python 3.14.2; NumPy 2.4.6, SciPy 1.17.1, Numba 0.65.1,
ANYmaterial 0.2.0, pytest 9.0.3. Effective BLAS pools and Numba used 1 thread;
JIT disabled. Supervisor: 600 s / 1 GiB. Times are verification costs, not speedup claims.

Reproduction: archived prepare.py builds with no-index/no-deps/no-build-isolation
and installs both wheels to an isolated target. run.py executes the four archived
test files under the existing bounded supervisor. artifact.json binds module and
fixture bytes; runtime.json binds actual imports/settings. No full environment is
archived. Source run used source ANYfem with the same installed solver.

Root reviewed the worker's strict standalone schema/lifecycle changes. The
separate worker read-reviewed root's Project route and negatives, finding no
consequential issue; root ran source/installed checks. This is OpenAI review,
not a different-family or scientific qualification claim.

[evidence-v1.zip](evidence-v1.zip), SHA256
`47293e32186c977c80287f7decd366aa0d176eade79152bee0f7ea175c7a6fe9`;
[evidence-v1.json](evidence-v1.json) binds its 21 entries.

Remaining: BL5 physical reference/F03, line materials/S3/distributed loads and all
unclosed programme obligations. Native Project persistence does not qualify the
physical connection or broaden solver admission. No push or publication.
