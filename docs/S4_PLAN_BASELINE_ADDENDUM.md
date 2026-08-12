# S4 improved execution addendum: live baselines and ownership

This addendum records the authoritative execution-time baseline for
`ANYsolver_S4_improved_Codex_plan_geometry_0_2.md`. It supersedes only the
stale dependency-version statements in that plan; its MITC4+/D theory,
performance, qualification, and delivery requirements remain unchanged.

## Fetched repository baselines

The following `origin/main` references were fetched on 2026-08-12 before S4
implementation work began:

| Repository | Fetched `origin/main` SHA |
| --- | --- |
| ANYsolver | `61e2f45ae2ca4fa87a6e149b0f89fabf209e5279` |
| ANYgeometry | `f2d7793d7d32a6dcd772c7ed8701aca11b459288` |
| ANYmesh (the active ANYmesher repository) | `e31f8c700b91796b93a8d2b21a6d44f70145eaed` |
| ANYfem | `c1c8ccb662eb8ecd8e4f08242855adf5b5d45166` |
| ANYmaterial | `4626887667f4c251479d26f321b9e73b046a2783` |
| ANYio | `82a0f5f110361fcd902cd3aac5d4c6beeaa187fa` |
| ANYfileio-occt | `571231dc4c7d8b4131daac6b719a6b93125a20b4` |

The ANYgeometry, ANYmesh, and ANYfem working checkouts contain active
native-hybrid work. They are read-only inputs to this branch. The S4 work is
isolated on `codex/S4_improved-integration`, based on the clean fetched
ANYsolver commit above, with `S4_improved` reserved as the delivery branch.

## ANYgeometry compatibility boundary

The active public ANYgeometry line is `>=0.2,<0.3`. The live package identifies
itself as `0.2.1`, and its forward geometry-document boundary is schema 4.
Schema 4 adds strict structural/replacement state beyond schema 3. The S4
handoff and compatibility fixtures therefore treat the live boundary as:

```text
ANYgeometry public API: >=0.2,<0.3
live package observed: 0.2.1
forward document schema: 4
legacy strict document schema: 3 (owned and migrated upstream)
```

ANYsolver will not parse, migrate, or reconstruct ANYgeometry documents. It
will consume a neutral immutable FE/provenance contract produced upstream,
including compact schema/version/audit metadata and model-bound source-handle
indices. Any schema-3-to-schema-4 document migration remains owned by
ANYgeometry/ANYfem adapters through public owner APIs.

No live ANYgeometry object or API call is permitted in element integration,
assembly, Newton, arc-length, constitutive-update, mass, geometric-stiffness,
or recovery hot loops. The improved element remains usable without geometry
provenance.

## Concurrent integration boundary

The native-hybrid task currently owns activity/deletion behavior and shared
assembly hot paths. Initial S4 work is confined to new formulation, reference,
director/provenance, recovery, qualification, and documentation modules.
Changes to shared dispatch or assembly files occur only during final
integration. The merge order is:

1. native-hybrid commits its activity/deletion and assembly changes;
2. the S4 integration branch inspects and incorporates that committed branch;
3. S4 public dispatch and optimized assembly integration is applied on top;
4. the combined branch runs both native-hybrid activity/deletion regressions
   and the full S4 qualification/regression gates before delivery.

No S4 milestone may treat activity behavior as qualified merely because an
S4-only suite passes.
