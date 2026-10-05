# F09 exploratory extreme graph probe: interrupted without result

22 September 2026. A local, unregistered two-member scalar physical-B2
exploration used `area=2^-80`, `E=1`, `nu=.3`, `Iy=Iz=J=1`, unit shear
factors, the oriented elbow from the existing test fixture, and three
terminal load vectors. It attempted to compare the assembled binary64 solve
against an independent exact-rational sectional force-method energy.

The process produced no case output while repeatedly constructing the
exact-rational station operator and was interrupted by its owner. Its command
returned exit code 1 with no numerical result. No result is inferred, and
this was neither a registered F09 execution nor a source-frozen performance
measurement. Do not reuse it as evidence of conditioning acceptance or
failure. A future extreme graph experiment must cache a single local
operator per member, bound runtime and memory, preserve per-phase output,
freeze the reference inputs, and register a terminal policy before running.
