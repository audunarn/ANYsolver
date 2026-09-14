# GE Beam3 G5 integration-closure contract

## Scope

This successor closes G5 and obligations S25--S26 after the accepted G1--G4
general-static gates.  It adds no beam or shell equations.  It qualifies only
the already implemented reference-configuration load, consistent-inertia,
modal, reference-buckling and linear-transient routes of the explicit
`ge-beam3` element, plus the existing explicit native finite-static workflows.

The gate does not qualify finite-velocity rotation dynamics, gyroscopic terms,
current-state generic `FEModel` dynamics, contact, activity/deletion, stable
postbuckling, ecosystem consumers, a default selector, or a release.

## Actual route inventory

The gate executes, rather than infers, all of these routes:

- legacy B2 and B3 reference stiffness, consistent mass, nodal load, gravity,
  load combination, Rayleigh damping, modal and short Newmark workflows;
- qualified GE-B3 public reference stiffness, consistent generalized mass,
  spatial-dead and material-dead line loads, nodal forces/couples, gravity,
  load combination, added point/edge mass, Rayleigh damping, modal, Euler
  reference buckling and short linear Newmark workflows;
- the exact explicit `ge-beam3-native` definition, finite-static solve,
  authenticated restart, recovery and provenance route accepted by G1--G4;
- rejection of follower line loads, finite-rotation transient requests,
  foreign selectors, wrong node counts and cross-formulation restart before
  candidate state mutation.

No equality between legacy and GE element matrices is required.  Legacy routes
are regression witnesses; GE routes are checked against their own frozen work,
mass, spectral and transient identities.

## Installed artifact

Build one wheel without isolation from the clean frozen commit.  Install it in
a fresh external target without dependencies.  Launch two isolated probes with
repository and source paths removed.  Each probe must prove that `anysolver`
and the GE class originate below that target, select only `ge-beam3`, preserve
the B2/B3 and shell selector identities, execute reference stiffness, mass,
load, modal and transient smoke checks, and emit byte-identical canonical
records.  The wheel and probe hashes are bound into the closeout.

## Execution and decision

Smoke precedes one complete rehearsal and two fresh formal cycles.  Each child
uses one numerical-library thread, at most 24 GiB, 600 seconds, and a 120-second
inactivity watchdog.  One worker is sufficient; a wave is capped at 1,800
seconds.  There is no automatic retry.  The two formal canonical scientific
aggregates must be byte-identical.

Terminal precedence:

1. `BLOCKED_GE_BEAM3_G5_PROCESS_OR_EVIDENCE`
2. `NO_GO_GE_BEAM3_G5_LEGACY_REGRESSION`
3. `NO_GO_GE_BEAM3_G5_REFERENCE_ANALYSIS`
4. `NO_GO_GE_BEAM3_G5_INSTALLED_ARTIFACT`
5. `PROVISIONAL_GO_GE_BEAM3_G5_GENERAL_STATIC_INTEGRATION_ONLY`

The successful terminal closes S25, S26, G5 and the general-static integration
contract.  It does not close the remaining P01--P32/U01--U10 domain-parity
rows or authorize production/default routing.  The production restriction is
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
