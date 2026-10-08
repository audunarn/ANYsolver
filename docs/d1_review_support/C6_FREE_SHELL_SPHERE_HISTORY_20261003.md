# Driven Q4/free sphere — history/work development closure

Parent18e40f9c; solver source unchanged. Extend only test/example and disposition.
[Identity](contact_c6_free_shell_history_20261003/source.json) and
[raw records](contact_c6_free_shell_history_20261003/raw.zip).

Prospective fixture: previous Q4/sphere, dt=.0005s, tEnd=.022s, four uniform nodal
forces totaling-.001N, factors(0,0),(.004,1),(.025,.5), active split.014s.
Preserve position2e-8m, velocity2e-6m/s, reaction1e-6N, work1e-12J,
impulse/momentum1e-10kg m/s and numerical restart1e-10 criteria. Independent24×24
continuum radial potential/two-body Newmark now includes shell load. Independent
six-point integration of affine force times cubic-path velocity checks every work
row; no production work helper. Check every saved total momentum/impulse row.

PASS:44steps/zero cutbacks, press/open and history knot; position error6.425985e-11m,
force error4.222548e-9N. Independent work1.1085514126e-6J versus production
1.1085514578e-6J. Applied impulse-1.6142857143e-5N s, installed example momentum
defect2.3717e-20kg m/s. Active split reproduces trajectory/work and all body fields:
max acceleration1.7053e-13m/s², centre1.3010e-18m, velocity3.7470e-16m/s,
force2.2204e-16N, energy8.8091e-20J. All per-field values retained. Changed load
history, swept tolerance and split cap reject continuation.

First run failed only an extra bitwise rigid-record comparison after numerical
restart/work gates passed. Preserve it. Correct to the existing numerical restart
criterion and check every field. No solver/scientific tolerance/resource change.
The reference helper's zero-load default changed, so its integrated energy/restart
test was rerun and passed; unaffected geometry/beam evidence was reused.

Focused v2:1pass,9.99s pytest; zero-load compatibility1pass,13.63s pytest. Runtime
and resource records retained; portable explicit selectors180s/953MiB, JIT off,
threads1 and reconciled imports. Source/installed driven examples match every field
and208 module hashes. Unchanged wheel5462ac6159aa315d3dc5d9d411b483024aeee41e7b7b7de6924d6e1088a3f4d8
is reused. Source4.583s/159711232B, installed4.565s/160198656B. No engineering
acceptance/release/savings claim; all historical failures remain.

Next D5 boundary: plastic material impact. Existing transactions carry trials but
dynamic checkpoints omit all material history and restore virgin state. A separate
profile needs accepted three-layer Q4 history, semantic validation and restore
before balance without another same-pose physical commit. Public static checkpoint
creation accepts static/arc-length only; do not mislabel transient. Reuse public
Q4 sealing/semantic validation and canonical JSON in a new versioned packet. Prove
actual yielding/unloading and state safety; this elastic case admits no plasticity.
