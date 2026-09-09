# Native reference-line force Newton: development closeout

Frozen implementation `f5cbe04bdcfd0821165c24e5ec3a08102d7e727c`, tree
`cca73d0404b8dc6b7eb2c043dc4e1a2f41042f4b`, passes this private development
gate. The exact four-path extent is in the companion plan and status. The
line-load element, objective load potential, physical fibre law and static
Schur kernels remain unchanged. Only private orchestration and candidate-only
dispatch in the existing force-control driver were added.

## Separate inventories

- Initial smoke: 7 passed; supervised wall 34.491 seconds.
- Expanded rehearsal: 9 passed; 51.931 seconds.
- Hardened rehearsal: 11 passed; 51.329 seconds.
- Existing nodal-native regression: 16 passed; 52.733 seconds.
- Q4 current-state ownership regression: 12 passed; 10.432 seconds.
- Frozen cycle A: 11 passed; 73.982 seconds.
- Frozen cycle B: 11 passed; 74.187 seconds.

All 15 canonical scientific JSON packets are byte-identical between frozen
cycles. Both cycles used fresh directories and ran concurrently under one
numerical thread each, 24-GiB tree memory, 600-second wall and 120-second
CPU-inactivity supervision. Every child exited with zero active descendants;
there was no automatic retry. Exact clean-head/configured-runtime guards passed
before/after both cycles. This is not complete dependency-graph qualification
or a performance claim. No mechanical test failed in these seven inventories.

## What is now connected

The actual global force-control Newton driver receives the effective constant
plus proportional line-force pattern at each tangent, line-search trial,
accepted tangent re-evaluation and reaction assembly. Internal cell-rotation
load work is retained; the reference-nodal portion is counted once externally.
Every original assembler argument, including full-coordinate reaction recovery,
is preserved. Ordinary beam/shell types retain their original assembler.

Straight elastic, curved elastic, curved plastic and curved elastic
constant-plus-proportional cases complete two increments. Explicit line search
is exercised; repeated cutback/arc-length qualification is not claimed. The
largest stored free residual is 1.8389650462420895e-14; reaction comparison
and force balance pass 1e-11. Accepted plastic origins match the preceding
committed history. A deliberately failed Newton increment preserves virgin
state. Missing/changed authority and resealed load patterns are rejected;
mid-assembly exceptions discard uncommitted trials and reset both load scopes.

The 13 scientific packets from the nodal-native regression also exactly match
its preserved f5bc443 cycle-A archive, including bytes and manifest hashes.
This is a read-only comparison, not a historical campaign rerun. The first
archive inspection used the wrong manifest filename and stopped before writing
status; correcting it to the existing `archive-manifest.json` completed the
audit without changing any evidence or rerunning mechanics.

## Preservation and continuation

External archive:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-native-line-global-f5cbe04-20260907`.
It contains 114 data files plus its manifest: every run's scientific output,
stdout/stderr/XML, four frozen paths, seven exact runner commands and supervisor
observations. Every byte count/hash was verified. The committed archive index
is an exact copy; the status is strict canonical JSON. Original temporary run
directories and historical archives remain preserved. Only the verified
duplicate transfer directory may be removed after the final audit.

Independent review remains PENDING. No public selector, mass/dynamic reduction,
general nonlinear section parity, restart authorization, release, alias or
default change is implied. Qualified Q4/S3 and prior qualification evidence are
unchanged. The private programme is still incomplete.

Next implement load-bound typed restart/recovery and connected line-loaded
cases through this actual solver. Do not reuse the old nodal-only restart codec
for the new state schema or silently introduce prior plastic history for a
constant load. Then continue full state/section, loads/couples, mass/modal/
buckling, engineering, packaging/performance and objective beam-shell gates.
