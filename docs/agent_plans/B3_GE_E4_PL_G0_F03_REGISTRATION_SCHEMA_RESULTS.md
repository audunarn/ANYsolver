# F03 local scientific registration schema: bounded prerequisite result

23 September 2026. This batch adds the canonical registration schema and
synthetic contract tests. It does not create a scientific registration or
execute a scientific case. G0B remains open and G1 remains barred.

The schema binds exact source and accepted-main commits; separate source and
run roots; current ordered five-case topology, inventory and plan identities;
plan archive bytes; source, interpreter and package file bytes; hardware and
thread settings; process and resource limits; numerical tolerances; exact
child command templates; and terminal precedence. Each registration is
exclusive. Read and write both validate owned regular files and current
identities. A digest sidecar left incomplete by interruption invalidates the
single-use attempt; no automatic retry is implied.

Independent read-only review found three issues and verified their closure:

1. Fabricated or stale case/topology/plan hashes were accepted. Registration
   now recomputes those identities and validates actual plan archives.
2. The writer could follow an aliased run root. It now rejects reparse roots
   and physical source/run aliases.
3. Source, runtime and package hash claims were not checked against files. Both
   write and read now stream-hash bounded no-follow owned files.

Final review: no remaining findings. The reviewer ran 19 focused tests with
one Windows symlink-privilege skip, plus 68 bounded tests with the same skip.
The parent ran 58 registration/archive/lifecycle/producer tests with the same
skip; zero failures or errors. Parent JUnit:
`C:/Users/AudunArnesenNyhus/AppData/Local/Temp/f03-registration-schema-20260923.xml`.
That JUnit predates the third issue's final synthetic tests. Those tests were
run separately: 19 passed and one identical skip.

The `clean_source` field and commit IDs are recorded claims. The future
coordinator must verify Git HEAD, the clean tracked source, accepted main,
runtime/package versions and origins, and exact command materialization before
registration and before every launch. The child must independently verify its
registered environment after writing its start marker. The registration
schema alone grants no launch authority.
