# Tor editor plan — S4 drill-constraint certification

Authority: `ANYSOLVER_S4_DRILL_CONSTRAINT_CERTIFICATION_PLAN.md`, raw
SHA-256 `90B5C4903EE6A9C06056F7E1F3AB21DAE0626C185A27627843A04BF289430E3A`.

Base: commit `587fa2efabcd48ada8a258ecf7301070b47f2b32`, tree
`de137d6a72548b5d5908d799b96f0586dff2ba8f`, branch
`codex/s4-drill-constraint-certification`.

Tor is the sole editor. The exact owned paths are:

- `pyproject.toml`;
- `docs/agent_plans/s4_drill_constraint_tor_agent.md`;
- `docs/reference_cases/s4_drill_constraint_cases.json`;
- `docs/reference_cases/s4_drill_constraint_oracle.py`;
- `docs/reference_cases/s4_drill_constraint_oracle_output.json`;
- `docs/S4_DRILL_CONSTRAINT_DERIVATION.md`;
- `tests/test_s4_drill_constraint_derivation.py`.

All accepted Eq. 21/Eqs. 24-25 source, prior proof/cases/oracle, geometry
handoff, activity, assembly, element, solver, export, serialization,
nonlinear, recovery, buckling, batch, sibling, and publication paths are
read-only and excluded.

The implementation must use the exact L2 normal equation, arbitrary-precision
rules, evidence matrix, pass/no-go semantics, and exclusions in the governing
plan. No threshold, fixture, precision, equation, or topology may be changed
after observing a result without a content-addressed plan amendment and
independent review.

Tor must pause before staging. Heimdall audits the precision/oracle boundary;
Forsete audits the mathematical and physical interpretation. A commit is
allowed only after both audits and every focused gate complete without a
material finding.
