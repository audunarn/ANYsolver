# V12 original V5 retained-load response — development decision

**Decision:** Direct interface loading of native retained half-cell spins is
not the sole source of the V5 body-work gap. The original V5 native load
splits into two separately rigid-balanced actions: its retained-spin interface
covector and its nodal/other complement. They use the **same** native body
operator, coordinate scaling and free-body physical-pose gauge. The two new
responses reconstruct the frozen V5 displacement exactly in the recorded
binary64 representation, and their work/reciprocity identities pass.

| Original V5 native action on unchanged body | Paired work |
|---|---:|
| Full saved action | `1.74538504099805e-6 J` |
| Retained-spin action alone | `1.15586949156334e-7 J` |
| Complement alone | `1.62979809184172e-6 J` |
| Cross work, each direction | `-2.44190279731207e-44 J` |

Removing the retained-spin action reduces native paired work by
`1.15586949156334e-7 J`. The complement remains `6.76319194709104` times
the saved C3D20 resolved-beam work (`2.40980605695025e-7 J`). This is a
**within-native fixed-operator sensitivity**, not an allocation of the
native/C3D20 discrepancy: the complement is a different physical action
without a matched resolved counterpart. The observed cross orthogonality is
specific to this fixture and gauge, not a general B3-GE theorem.

One V12 numerical attempt passed in `2.7924581999977818 s` process wall,
with `164069376 B` sampled peak process-tree RSS. The retained and complement
original-operator equation ratios are `1.84e-12` and `3.94e-12`. Effective
CPU0, one numerical thread and JIT-off settings were recorded. Two native
beam RHS solves were performed; there were no resolved, coupled, external or
formal F03 solves. The distinct 120 s V12 allowance has
`117.20754180000222 s` remaining including its 60 s reserve. The successful
attempt closes this question; unused time is not transferred to another
experiment. The Python 3.14 launcher emitted a nonfatal location warning,
retained verbatim in the stderr evidence.

[Registration](v12-retained-load-registration.json),
[receipt](receipt-v12-retained-load-attempt-1.json),
[raw result](case-v12-retained-load-attempt-1/result.json), and
[source](../../scripts/r8_bl5_v12_retained_load_response_dev.py) bind the
frozen V5 input and exact code. Independent read-only review found no blocking
slot, sign, balance, operator, gauge or work error and confirmed the limited
interpretation.

The next useful mechanics check is a **matched distributed action and body
response** for the original P0/tip load. It must retain the actual native
half-cell traces, identify the resolved two-sided face/section work, and
compare load measures on common virtual fields. Do not infer a line-law or
multiplier choice from a global work ratio, or continue a saved-vector
decomposition that cannot separate the bodies and action maps. G0/F03 remains
open; no old one-use authority, external model, mesh sweep or release gate was
consumed.
