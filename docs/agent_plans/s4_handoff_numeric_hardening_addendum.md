# S4 numeric handoff audit-hardening addendum

## Registration purpose

This addendum registers a narrow follow-up to the S4 numeric handoff/director
specialist plan after independent review rejected commit `f400b86` for
fail-open or lossy numeric coercions. It authorizes no implementation until
the ANY ecosystem boss records and clears this addendum.

The follow-up remains on:

```text
worktree: C:\Github\ANYsolver\.perf2-worktrees\s4-geometry-handoff
branch:   codex/s4-geometry-handoff
base:     f400b8660d63ea5cf2fd5a95165dbcdd6c212834
```

The implementation will be a new child commit. Commit `277f9b0` and follow-up
`f400b86` will not be amended.

## Independent-audit findings to close

The follow-up must reproduce and close each reported defect:

1. `_compact_indices` can accept `uint64` maximum and convert it to the
   signed `int64` value `-1`, colliding with the unavailable sentinel.
2. `PreparedDirectorField` can accept a provenance value of `256` and convert
   it to `uint8` zero, silently changing its meaning to a valid provenance
   code.
3. `numeric_payload_fingerprint` can convert `uint64` maximum to signed
   `int64 -1`, causing distinct numeric inputs to share a fingerprint.
4. `PreparedDirectorField` can accept non-finite director values, including
   `NaN`, when constructed directly.
5. `SourceCornerSamples` can accept huge but initially finite tangents whose
   norm or cross-product calculation overflows to non-finite values; comparison
   with `NaN` then fails open.
6. `ShellSourceAssociation` can accept a `uint64`-maximum region/table index;
   packing later fails or changes meaning instead of rejecting the record at
   construction.

## Owned implementation scope

After clearance, implementation edits are limited to the existing seven
registered owned files:

```text
docs/S4_GEOMETRY_HANDOFF.md
scripts/check_s4_geometry_handoff.py
src/anysolver/shell_formulations/director_field.py
src/anysolver/shell_formulations/geometry_provenance.py
src/anysolver/shell_formulations/mitc4_plus_d_quality.py
tests/test_s4_director_field.py
tests/test_s4_geometry_handoff.py
```

This plan addendum is registration evidence, not an expansion into shared
production files.

The numeric hardening will:

- validate the original scalar domain and range before every narrowing cast;
- reject booleans where true integers are required;
- reject unsigned or arbitrary-precision integers outside the target signed
  or unsigned storage range;
- reject values that would collide with `-1` sentinel semantics after a cast;
- reject provenance codes outside the exact registered code set before
  conversion to `uint8`;
- keep integer fingerprints injective with respect to signedness and value,
  or reject unsupported values explicitly before hashing;
- require finite director arrays in direct `PreparedDirectorField`
  construction and preserve immutable C-contiguous storage;
- scale tangent validation to avoid overflow-prone raw norms/cross products,
  and reject any non-finite intermediate or degenerate normalized pair;
- reject invalid `ShellSourceAssociation` indices at construction, not during
  later packing;
- audit every integer and numeric coercion in the owned production modules for
  analogous wraparound, truncation, sentinel collision, overflow, `NaN`, or
  infinity behavior.

The audit includes, at minimum:

```text
Director provenance arrays
source face-use sign arrays
part/sheet/continuity compact index arrays
node connectivity
declared crease/intersection edge pairs
numeric payload fingerprints
source UV/tangent arrays
prepared director arrays
geometry provenance header revisions/schema
source and compact entity IDs/kind indices
lineage indices and descendant tables
shell/member/coupling association indices
packed shell association arrays
orientation signs and normalized parameters
```

If an owned coercion is already fail-closed, it will receive a focused boundary
test where that materially guards the contract; it will not be rewritten only
for style.

## Exclusions and ownership boundaries

The follow-up will not touch:

- any package `__init__.py` or exports;
- `ShellElement`, reference formulation, shared assembly, activity/deletion,
  dispatch, serialization, recovery, or `AnalysisSession` files;
- sibling repositories or live ANYgeometry/ANYmesh/ANYfem objects;
- geometry document parsing or migration;
- native-hybrid-owned paths;
- scientific tolerances, formulation equations, or performance kernels.

No direct ANYgeometry import or live geometry call will be introduced. The
numeric handoff remains preprocessing-only and hot-loop independent.

## Focused tests and acceptance gates

The follow-up will add explicit regression tests for:

- `uint64(max)` rejected by compact region/table index construction;
- large positive Python/NumPy integers rejected before `int64` packing;
- `-1` accepted only where it is the documented unavailable sentinel;
- provenance `256`, negative codes, and other unregistered values rejected
  before `uint8` conversion;
- `uint64(max)` and signed `-1` never fingerprint as the same payload;
- unsupported integer ranges either hash distinctly with signedness preserved
  or fail closed by documented policy;
- direct `PreparedDirectorField` construction rejects `NaN` and infinity;
- source corner tangents near floating-point maximum fail closed without an
  overflow-dependent `NaN` escape;
- `ShellSourceAssociation` rejects out-of-range unsigned indices immediately;
- analogous boundary cases found during the owned-code coercion audit;
- existing face-use/reference-Jacobian, crease/sheet separation, wrong/stale
  model, compact serialization, and zero-live-import behavior remain passing.

The exact lightweight gates will be:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='<worktree>\src;C:\Github\ANYgeometry\src;C:\Github\ANYmesh\src;C:\Github\ANYmaterial\src;C:\Github\ANYio\src;C:\Github\ANYfileio-occt\src;C:\Github\ANYfem\src'
python -m pytest tests/test_s4_geometry_handoff.py tests/test_s4_director_field.py tests/test_extracted_package_wiring.py -q -p no:cacheprovider --basetemp=.pytest_tmp_s4_numeric_hardening
python scripts/check_s4_geometry_handoff.py --full
git diff --check
git status --short --branch
```

Acceptance requires zero failures, no warnings caused by the new tests, a
clean post-commit worktree, no temporary/cache output, and a new atomic child
commit containing only the registered implementation paths plus any boss-
approved handling of this registration addendum.

## Performance boundary

This is a cold-path correctness and validation follow-up. It will use only
small synthetic fixtures and focused tests. No heavy qualification, benchmark,
large scaling run, or performance lease is requested. The existing lightweight
64-Q4 structural linearity check may run as part of the checker; it is not a
timed performance claim.

## Reporting contract

After boss clearance and implementation, report:

- the new child commit SHA;
- exact changed files;
- each audit finding and its closure;
- any additional analogous coercion defect found and fixed;
- exact test/checker commands and results;
- clean worktree/cache status;
- confirmation that no shared or sibling-owned path changed.
