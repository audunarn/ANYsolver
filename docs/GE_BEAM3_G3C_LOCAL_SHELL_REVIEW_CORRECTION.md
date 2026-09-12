# G3c local shell review correction

Preserve candidate c1d571a143d0b3b62eafd3aa240a1a84cc7c298f and its passing
author smoke (2 tests) and full development lane (26 tests). Independent source
review did not execute mechanics or report a mechanics contradiction. It found
SH-01 (mutation test altered different objects than the passed arrays) and
SH-02 (required per-channel/station transport coverage incomplete). The canonical
incomplete review is retained unchanged; no partial local acceptance is claimed.

Original raw runs remain in Temp and in external archive
C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-g3c-shell-development-20260912-c1d571a.
Eight-file archive manifest SHA-256:
adbedcce2d223a4f323abbf94ba475f122070ca6aa1fcd7b677223d45d97f2ba.
Full child completed in 20.6520871 seconds, peak 237977600 bytes, active process
count zero; smoke completed in 17.1261693 seconds, active count zero.

Correction adds no new shell mechanics. The facade now returns explicit owned
reference/current station positions and separate global source strain/resultant
tensors for each physical work channel. Source-engineering derivative row and
reference-global local-d column conventions are named. No composite finite Q4
resultant is exposed. The mutation test now changes the EXACT arrays passed to
evaluate after their capture. New comparisons check every channel's signed
energy/force/tangent, weights, physical station map, engineering derivatives and
reference/current tensor/vector fields through all frozen D3/D4 numberings,
passive transforms, common motions, director reversal and unchanged-pose rebase.
Two additional tests deliberately corrupt station fields/positions/weights/
derivatives/frame/current tensors and require rejection.

Corrected full lane inventory: 28 nodes (the existing 26 plus two corruption
tests); smoke stays two nodes. Same limits and no retry. Run fresh smoke and
full development lanes only after this successor is cleanly frozen, then obtain
independent implementation review. Existing source/equation packets, thresholds,
Q4/S3 mechanics, physical recovery APIs and graph/parity obligations are unchanged.
