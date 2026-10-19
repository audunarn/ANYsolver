# Preserved contact Read checkpoint (inspection only)

I'll start by reading the CI evidence, then trace the source paths for the six failure families.

Six failures confirmed. Now extracting the detailed tracebacks for each failure family.

Checkpoint byte diffs show last-bit float differences. Now the remaining four failure tracebacks.

Two distinct families so far: exact replay mismatches (last-bit float drift) and a binding-classification assertion. Now the last two tracebacks.

Early findings checkpoint (after evidence read):

**Six failures, two distinct families:**

1. **Exact-replay family (5 of 6)** — stored checkpoint record vs re-replayed record differ at last-bit/1e-16 scale:
   - `curved_pair_lifecycle` (job 4100): `contact.beam_a_force_n[0]` stored `-1.3813270855780865e-05` vs replayed `-1.3813270855779464e-05`, 13 leaves; test asserts byte-equal checkpoints (test line 143).
   - `curved_static` (4101): split-parity byte assert fails; same-value floats differ in last digits, `previous_sha256` diverges (test line 142).
   - `fibre_results` (4274): `tangent_error_n_per_m` stored `2.7902272984168655e-07` vs replayed `2.790227500475597e-07` (rel ~7e-10), 2 leaves — raised in `src/anysolver/general_contact/native_multi_s3_static.py:653` `_restore`.
   - `curved_s3_multifacet` (4337): same site, `tangent_error_n_per_m` `2.958106896226822e-07` vs `2.958106727472888e-07`.
   - `retained_body_pair` (4428): `beam_a_force_n[0]` stored vs replayed differ ~6e-16 abs, 12 leaves (test line 66).
2. **Binding-classification family (1 of 6)** — `curved_s3_static` (4291): after tampering only `schema`+`identity`, the refusal message also lists a `profile` disagreement, which the test asserts must not be there (test line 135). Different mechanism from the replay drift.

Next: inspect the b020 diff (fe_core recovery helper), the `_record`/`_restore`/`tangent_error` source path, and the two test files.

The b020 diff is value-preserving (identity/cache retention only). Now checking run metadata and the baseline to determine whether these failures are new at b020.

Failures span both OSes and Python 3.11–3.14, one test per shard. Now tracing the source: `_record`/`_restore`/`tangent_error` in `native_multi_s3_static.py`, and the profile binding.

`_record` stores `contact.contact.to_dict()` including the derived `tangent_error_n_per_m`, and replay must reproduce it exactly. Now the cache key and `_assemble`, plus where `tangent_error` is computed.

The replay path uses `context.make(row['mechanical'], decoded=True)` while `_record` normalizes with `context.make(mechanical.descriptor())` (no `decoded=True`). Tracing `make` and the `decoded` flag.

## Last source inspections

cd "C:/Github/ANYsolver/.worktrees/test-regime-ci-b020-20261016" && grep -rn "tangent_error" src/anysolver/general_contact/*.py | grep -v "tangent_error_n_per_m=" | grep -vi "to_dict\|fields\|'_fields_\|:23:\|:112:\|:39:\|:135:" | head -20

cd "C:/Github/ANYsolver/.worktrees/test-regime-ci-b020-20261016" && sed -n '440,510p' src/anysolver/general_contact/native_multi_s3_static.py

cd "C:/Github/ANYsolver/.worktrees/test-regime-ci-b020-20261016" && sed -n '140,175p' src/anysolver/general_contact/native_retained_line_plane.py && sed -n '100,120p' src/anysolver/general_contact/native_retained_line_plane.py

cd "C:/Github/ANYsolver/.worktrees/test-regime-ci-b020-20261016" && grep -rn "def make\|decoded" src/anysolver/general_contact/native_beam_context.py src/anysolver/general_contact/*.py 2>/dev/null | grep -n "def make\|decoded" | head -25

cd "C:/Github/ANYsolver/.worktrees/test-regime-ci-b020-20261016" && grep -rn "def make" src/anysolver/general_contact/native_fibre_layout.py src/anysolver/general_contact/native_fibre_backend.py 2>/dev/null; grep -rln "layout" src/anysolver/general_contact/native_fibre_context.py && sed -n '1,140p' src/anysolver/general_contact/native_fibre_context.py

cd "C:/Github/ANYsolver/.worktrees/test-regime-ci-b020-20261016" && grep -n "def make\|decoded" src/anysolver/_ge_beam3_retained_fibre_state.py | head && grep -n "class Layout\|class Context\|def make" src/anysolver/_ge_beam3_retained_fibre_state.py | head