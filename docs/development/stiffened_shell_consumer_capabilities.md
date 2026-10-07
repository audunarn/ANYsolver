# Experimental stiffened-shell consumer capability record

Candidate state: **VERIFIED_AGAINST_ASSIGNED_CONSUMER_CRITERIA** for product
`535390ef` with test-fixture repair `0acbef03`. This scoped verification closes no
G6B gate and establishes no application or scientific acceptance.

`anysolver.stiffened_shell.capabilities_record(analysis)` reads the `capabilities`
property of an existing stiffened-shell GE or B2 owner and returns detached Python
JSON primitives. It does not construct an owner, compile, solve, recover, preflight,
evaluate, checkpoint or restore. Existing capability accessors, their types and
`create_analysis` dispatch are preserved.

The wire identity is `STIFFENED_SHELL_CONSUMER_CAPABILITIES_V1`, schema version 1.
`profile` is the existing GE or B2 profile identity. `raw_report` preserves every
reported field, including unknown fields, route-specific operations, policies,
domains, laws, mass assumptions and exclusions. Tuples become lists, finite NumPy
numeric scalars become Python numbers and arrays become detached nested values.
Capability dataclasses become field mappings. The two existing B2 footprint
definition types use their established descriptors, retaining law and admission
semantics. Unsupported values, non-string mapping keys, nonfinite numbers and
cyclic or excessively deep records are refused rather than represented with text
or silently omitted.

`raw_status` retains the original owner status. The envelope states
`EXPERIMENTAL_NOT_QUALIFIED`; accepted evidence is `UNAVAILABLE` with empty IDs and
`production_qualified` is false. Platform and resource qualification are
`NOT_BOUND`. Resources identify only admission of the `create_analysis` argument
`resources=None`. They do not describe B2 chunk controls, solver controls, measured
resource limits or a qualified host. Conflicting
profile or qualification claims are refused. Foreign owners and subclasses are
refused; no duck-typed mechanics implementation is admitted.

The record supplies no export operation. Its export statement concerns this
metadata record alone and does not restrict native ANYfileIO persistence or other
existing exports. No operation aliases or inferred operation union are generated:
consumers use the raw report and submit actual typed requests to the existing
owner. Source/artifact identities and accepted evidence are not fabricated.

The prepared serializer controls use uninitialized exact owner types with patched
capability properties; they establish no compiled-provider integration claim.
Separate public-facade smoke tests construct existing GE and B2 panel fixtures
and read their actual reports without issuing numerical solve requests.

The verified tests cover primitive JSON round-trip, field/identity preservation,
mutation isolation, qualification truth, refusal boundaries, no owner operation
beyond capability access, and representative existing facade routes. Preserved
`source-v1` evidence records 40 of 41 passing and one failure from an unbound
legacy test import, with process-wall duration 12.5308052 seconds. After the
self-contained B2 fixture repair, `source-v2` and `installed-v1` each passed all
41 controls; one isolated build/install also passed. Cumulative process-wall use
was 57.9778161 seconds of the 180-second allowance, with effective settings CPU0,
one thread, JIT off and 2 GiB. The verified wheel SHA-256 is
`fa5507fe14cc09949743adb7d5ae340a2499d9b813d6b80a1b7d4ea414267e82`, with 431
payload modules. ANYworkspaceAI application integration and G6B/scientific
acceptance remain open; these checks do not transfer authority from the consumed
numerical campaign or remaining fold budget.
