# Supporting source review of next E03 observability packet

Reviewer /root/coarse_e03_screen did not author these decks. No imports, tests,
solves, downloads or edits by reviewer. The first two preparations are retained
UNEXECUTED; they are not failed numerical evidence.

- V1 nonzero SPC outsideSTEP found; v2 moves BOUNDARY intoSTEP/STATIC.
- SPRING2 onlyx stiffness with possible three active translations found from
  author mastruct master (version caveat); v3 explicitly fixes all nodes y/z0.
  This leaves scalar oracle and physical x work unchanged, one active free xDOF.
- x oracle independently checked: u=[.1,0,.1,.1], g=[1,-1,0,0], p=[2,0,0,0],
  C=[1,0,-1,0], physicallambda=-1, rSPC=[0,-1,-1,0]. Equation nodes coincide.
- Source internalfmpc=fn_dep/coefficient=+1 does not equal physicallambda here,
  because pivot is loaded; recovery must subtract declaredp before solving.
- E03 output-only card reversal is exact and hashes agree: no physical byte change.

Root adopted the two reversible preparation fixes prospectively. V3 is a prepared
instrumentation control, not an executed binary-semantics confirmation. Execution
wrapper/reader verification and fresh150s authority remain pending. Stop on first
failure; no new physical launch under the old consumed primaries. Different-family
or final engineering acceptance is not supplied by this supporting review.
