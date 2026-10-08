# Native history curvature certificate - development checkpoint

Implemented a conservative second-derivative chord bound for complete-panel separation. For every material point, g(t)>=min(g(0),g(1))-M2/8 on a unit segment. Exact spatial endpoint minima and bounds on changing target normal, affine base motion and spatial rotation supply M2. One interval is charged on success; old Lipschitz fallback and all caps remain.

Saved rebase now passes using37/128support units,480queries,9panels, scaled integration error0.14930. Fifteen existing support checks also pass (16checks15.40s total). Independent analytical shallow rotating-arc check and prefix-cost check pass(2checks3.95s). Admission support cost106->12 for first history and109->15 with zero rebase. No balanced runtime speedup claim.

Actual coupled owner commits first load and passes zero-motion rebase/equilibrium/storage checks. Second load fails at integral call16 in historical regional-cover admission, shared support128. Test105.67s, process110.964s, sampled peak238129152B; native120s/context unchanged. Split restart not reached. Saved second-load input is replay_owner_second_load_rejected_path.json. No engineering acceptance or installed-native claim.

Failed one-interval scheduling, segment-count scheduling and projected-speed attempts were discarded; logs and decisions retained. Independent review supports the chord mathematics with existing binary64 padding limitations; see replay_regional_review.md. Earlier review/failed evidence remains unchanged.

Raw logs/runtime/resource/source snapshot: replay_curvature_raw.zip; manifest replay_curvature_results.json. All JIT off, source imports verified. Routine180s/953MiB, named coupled900s/3814MiB outer with stricter120s native context. Next replay second-load failure locally; determine whether actual nonmonotone history or a conservative whole-history cover causes refusal. No unchanged coupled retry or automatic cap increase.
