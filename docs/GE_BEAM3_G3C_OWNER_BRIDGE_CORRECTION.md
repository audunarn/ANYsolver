# Initial mixed-owner incident and guard corrections

Initial implementation 015a53469383b0b41422d969b67387db59fe09f5,
tree 54102e1d1433fbc94ae421ab6e2b85922049c3dd is preserved unchanged.
Its one-node smoke FAILED during virgin-owner runtime-guard initialization:
15.818761600006837 seconds, peak 240590848 bytes, exit 1, no remaining child.
No full lane or graph acceptance occurred. Raw output remains in
Temp/anysolver-g3c-owner-development-ahd8fa73. Process record SHA-256
28596e633cc548a98fd1a20565bd9cfe9d4d8a6a3a30a615c55d269ad0e0f623;
input lease d4b230585038a920150f4154f8d617bdf48cf0d8d65bfe3fc02ef1b1150cad0f.

The independent initial review is copied unchanged. It rejected MOI-01,
unauthenticated/dynamically released lock permitting failure after publication,
and MOI-02, mutable common-transform constants and incomplete imported-method
coverage. A subsequent independent source inspection also found that exceptions
inside full authority validation did not always permanently poison the owner.
No reviewer mechanics had run. These findings are not scientific contradictions.

This correction authenticates the exact acquired lock and releases only its
captured local reference. Frozen transforms use immutable tuples and exact
value checks in both defining and consuming modules. Dispatch now captures
imported/inherited class methods and properties, including section/reference
methods, through function/code-object identities; it does not treat marshal
serialization as a code-identity primitive. Dispatch mismatch diagnostics name
changed bindings rather than reporting only a generic guard failure. Every
exception during authority validation permanently poisons the owner. Ordinary
invalid commands are still rejected outside that authority-failure path.

Six regression nodes cover lock replacement, two transform-module replacements,
two imported-class replacements, and restoring an authority provider after a
detected read failure. The new full inventory is 18 nodes, separate from the
one-node smoke. No mechanics, coefficients, thresholds, source evidence,
fixture topology, loads or defaults are altered by these guard corrections.
The failed command is not retried: a newly frozen corrected candidate receives
a new exclusive development directory. Keep the failed record and review.

Full graph/restart/recovery/formal qualification remains open. Subsequent
independent implementation review must verify the actual corrected assertions.
