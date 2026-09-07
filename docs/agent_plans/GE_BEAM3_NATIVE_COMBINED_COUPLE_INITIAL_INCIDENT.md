# Initial combined-couple rehearsal coverage incident

The unfrozen initial curved-plastic fixture failed its explicit positive
plastic-history assertion: zero positive accumulated plastic rows. Its solver
completed and the other 31 selected checks passed; this cannot be accepted as
plastic-state coverage. No mechanical equation or acceptance tolerance failed
or was changed to resolve this coverage defect.

Initial nodal moment: (.015,.01,-.008).
Distributed couple density: (.07,-.04,.05).
The nodal bending components oppose the distributed bending components.
Correct only the new, unfrozen fixture to (.015,-.01,.008), maintaining its
magnitude and the positive-plastic-history assertion. Keep all section,
yield/hardening, physical operator and Newton controls unchanged. Apply the
same fixture direction to all three geometry shards and rehearse again before
freezing. This is a deliberate examined correction, not an automatic retry.

Initial curved rehearsal: 31 passed, 1 failed, 77 deselected.
Directory: `C:\Users\AUDUNA~1\AppData\Local\Temp\ge-beam3-native-combined-rehearsal-curved-plastic-k43cmywx`.
Whole-result file: 53417 bytes; SHA-256 `458abbc3b48b0fe143dd5f996f932dddb9c739b3a5f53cb8d3e667994299c610`.
Initial test source: 14418 bytes; SHA-256 `488049bcb2b23bf97b739a5b5ca18f1a65032cf366ac39701c4b68605f425411`.

The initial local lane passed 13 tests (one expected negative norm-range
warning); the initial connected-plastic lane passed 32. Preserve both, the
earlier three-test smoke, the failed curved result, raw stdout/stderr/XML,
all seven initial source files and their hashes. Initial outputs must not be
mixed into the corrected scientific replica comparison.

The corrected curved smoke passed recovery and actual continuation/unload,
including the unchanged positive-plastic-history requirement. Corrected
complete rehearsals and frozen cycles remain mandatory. No full production
qualification or default activation follows from this development gate.
