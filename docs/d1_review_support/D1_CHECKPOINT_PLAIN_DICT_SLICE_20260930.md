# Checkpoint plain-data normalization slice

The formal SpatialV5 run on installed590d timed out at900.048s/596.00MB.
Checkpoint creation began at428.014s and never returned. Recovery1.178s and
seal0.730s are observed separately. The failed authority remains consumed;
no spatial postchecks ran. This localizes the remaining delay to checkpoint
creation, without attributing every constituent cost.

The candidate changes only `_normalize_json`'s mapping-observation guard:
exact dicts with exact str keys avoid a full model scan after their inert
snapshot. All values recurse unchanged. Subclass/custom mappings, effectful
keys/conversions/sequences, arrays, dataclass getters and serializers retain
their guards. Entry/output checks, semantic validation and seals stay intact.
This is a serialization change; contact equations and settings are unchanged.

Eight focused controls pass20.453s/423.85MB, including the existing actual-Q4
nested-mapping attack. Five producer/round-trip/negative checkpoint controls
also pass; raw supervisor measurements are linked below.

One saved complete canonical checkpoint was normalized twice on the same
432-element model with the real lifecycle guard. Only the named function was
replaced with its old installed590d AST for the baseline, then restored.
Baseline48.222628s/1307guards (48.102718s inside guards); candidate0.114138s/
0guards. Both canonical byte hashes are
`300b7828cfcebdbdf6989da38c7c2a10938ccd6d6262af1f19a0e2a3db6aab35`.
The saved input stayed unchanged. Supervisor50.431s/183.36MB.
This measures canonical normalization only, not complete checkpoint creation
or coupled-route speed. It does not qualify new installed restart by itself.

Independent read-only scrutiny found no patch correctness blocker. The next
affected gate is new-installed complete producer/consumer parity on saved
active/open roots, then spatial evaluation with unchanged mechanical criteria.
Unchanged reference/work/pressure results may be reused by explicit impact;
old artifact-specific checkpoints/timing are not silently transferred.

- [SpatialV5 resources](d1_final_spatial_v5_20260930_radial.resources.json)
- [Exact tail trace](d1_final_spatial_v5_20260930_radial.recovery.jsonl)
- [Focused controls](d1_checkpoint_plain_dict_controls_v1_20260930.resources.json)
- [Round-trip controls](d1_checkpoint_plain_dict_roundtrip_v1_20260930.resources.json)
- [Saved complete-payload comparison](d1_checkpoint_plain_dict_probe_v1_20260930.json)
- [Probe resources](d1_checkpoint_plain_dict_probe_v1_20260930.resources.json)
- [Probe helper](d1_checkpoint_plain_dict_probe_dev.py)
