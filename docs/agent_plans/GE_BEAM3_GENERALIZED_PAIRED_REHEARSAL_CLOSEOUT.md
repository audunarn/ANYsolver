# Paired current-material modal rehearsal and next integration gate

Implementation d5141c3777e887d3bac7134d354efe50b7aab8eb; corrected harness
freeze e4e10fbe6beb0af39f125e5fb0de457cd3733d6e, tree
a4d0f602ccc56ee013ea4e99ae14322f1913c90b. Existing numerical kernels and
their failure records retained. Only three new private production modules;
no existing beam/shell mechanics, section/state/recovery laws or defaults changed.

## Separate verified inventories

- Corrected ownership witness: one test, one record, passed.
- New paired local:32 tests and32 records, passed.
- rho100: one test, five records, all four12-mode specimens passed.
- rho10000: one test, five records, all four12-mode specimens passed.
- rho1e6: one test, five records, all four12-mode specimens passed.
- Inherited dense local:17 tests/17 records, passed at d5141c3.
- Inherited prestress/state local:three tests/three records, passed at d5141c3.

The test-only correction does not rerun or relabel the inherited records at
a new revision: all three production modules are byte-identical across the
two freezes. Old dense/prestress scientific records equal their previous
hash-bound baseline. All31 previously passing paired-local records are also
byte-identical; the corrected witness equals its complete-local counterpart.
The initial WRITEABLE harness failure remains preserved in its own archive.

## Numerical result, not qualification

All12 roots at each of twelve geometry/orientation/slenderness specimens
agree with the100-digit supplied-factor audit; largest squared-root relative
error3.915e-15. Maximum original signed Ritz error1.809e-13 and reduced
action error1.810e-13, both below unchanged1e-11 checks. Full original-factor
free-coordinate residual and physical kinetic-Gram checks pass. Root counts,
negative-root handling, source-factor identity and kinetic definition unchanged.
This audit is same-author arithmetic validation, not an independent physical
continuum reference or proof of slender nonlinear engineering performance.

Validated modes explicitly own high and low arrays. The fingerprint includes
all result fields. Missing, altered, malformed and writable halves reject;
implicit high-only full_modes access rejects. apply_mode_map consumes the
complete pair and checks identity before/after. Canonical repeat within the
local unit test is deterministic; formal external repeat cycles remain unrun.

All process trees terminal; maximum concurrent workers3. Corrected local
elapsed132.879seconds before cleanup; each slenderness lane6.421seconds or
less, peak under254MB. One thread and24GiB/600second bounds retained. No
automatic retries or historical cleanup. Raw outputs and original locations
remain intact; status binds the9747-byte external archive manifest and audit.

## Next concrete work

Use the new paired adapter in private consumer regressions before any wider
qualification or public integration. Add explicit paired-mode kinetic maps
for the existing frozen continuum closed-group tests, retaining the same
independent Ritz/ODE references, grouped cutoff, refinement levels, frequency
and principal-correlation limits. Do not simply collapse high+low first.

Cover free-body six-rigid modes, connected shared trace elimination, reversal
and proper-frame covariance, and a converged loaded conservative beam state.
The existing new-local tension/compression test is one element only; it does
not replace the actual-preload Euler/buckling refinement campaign. Adapt the
four existing bounded buckling nodes through the paired adapter without
changing their eighteen bisections or engineering checks. Preserve pending
trials and accepted material history throughout.

Freeze these consumer tests separately. Rehearse small connected/loaded cases
first, then at most three concurrent bounded continuum/prestress workers.
Only all-pass complete rehearsal permits two fresh deterministic cycles.
Stop expansion on a new failure and preserve it; no automatic retries.

Full programme remains active and incomplete: broad nonlinear conditioning,
material/fibre/load/solver/state/restart parity, curved engineering cases,
installed explicit opt-in integration, independent review and objective
finite-rotation beam-shell coupling remain required. Main and legacy paths
are untouched. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
