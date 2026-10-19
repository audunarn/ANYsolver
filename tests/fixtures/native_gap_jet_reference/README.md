# Frozen gap-jet reference sources

These are immutable pre-optimization source snapshots used by `test_general_contact_native_gap_jet_preparation.py`. The tests parse and compile only the selected original functions into explicit test namespaces; these files are not alternative importable solver implementations. Keep their numerical operations and bytes unchanged. Do not regenerate them from the optimized product to make a regression pass.

Original SHA-256:
- native_replay_arithmetic.py: fea6a5fbd8fb880e2aca7c105c254f9032c266b35a1f1dd288af14006fac465d
- native_curved_s3_work.py: 32025e9088be8985cd5371286d3e5be68a6f8d7acb543e04a90fbc3ada543024

The raw-point oracle checks complete Jet2 value/gradient/Hessian behavior, and the original contraction oracle checks bytewise reduction parity. These are regression references, not independent physical truth or scientific qualification. Any intentional future reference change needs an explicit rationale and renewed comparison; never silently normalize or edit these snapshots.
