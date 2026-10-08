# B2 consumer mass/modal persistence — development result

Implemented/tested experimental behavior; no aggregate acceptance or release.
ANYfem source `a615c4b299e603264f67d292c8a4415168b1b9c6`; solver product unchanged
at `0da6cd12b755ab78b9634e2a4b5b880058f2e457`, integration `6adfb164`.

Explicit `SCHEMA_MASS` stores each shell's nullable density and each member's
nullable mass source/origin/full per-length matrix. Default static-v1 semantics
and fields are preserved. Save/reopen uses the public owner for static batches
and checked reference modes; no mechanical operator or default changed.
Partial mass and general affine maps remain usable static inputs. Unsupported
modal requests fail explicitly. Cancellation, backend non-success and programming
exceptions retain their meaning; delegated owners always close.

Focused source 19/19; exact isolated installed 43/43 covering the consumer,
unchanged GE consumer and current B2 modal regression tests. No passed prior
campaign was rerun beyond this impacted installed boundary. Full unchanged
solver/source-wheel identity supports reuse of the existing artifact. See
identity.json, imports.json, execution.json, installed.log and review.md.

Final guarded time 33.3701286 s, peak RSS 220,983,296 bytes. Thread count one
and JIT disabled were asserted in the actual Python 3.14.2 test process. These
are resource observations, not performance claims. Windows only; Linux/full
platform graph and final qualification remain unfinished.

Commands: build consumer with `python -m pip wheel --no-cache-dir --no-deps
--no-build-isolation`; install existing solver and new consumer wheels with
`python -m pip install --no-cache-dir --no-deps --target site`; execute
`python run_bounded.py` from the isolated run root. run_installed.py binds
source/wheel/installed modules, copied tests and effective settings before the
selected tests. Test fixture helper is copied without dispatching its CLI.

Earlier setup failures are preserved: pip cache ACL, omitted direct precheck
PYTHONPATH, missing imported test fixture, then missing fixture helper. None
completed numerical tests or produced accepted mechanics evidence. Same selected
checks passed after copying dependencies. Original manifest identifies all raw
files and source inputs; review/results are subsequent independent disposition.

Mandatory F06, connection, foundations, native-project persistence, complete
spectral/material/topology/load/capacity, external, scale and release obligations
remain visible. No F03 authority was consumed and main is unchanged.
