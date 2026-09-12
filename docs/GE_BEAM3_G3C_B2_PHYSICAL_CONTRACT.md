# Approved private B2 successor: local-to-graph contract

The user explicitly approved the private B2 operator successor on 2026-09-13.
This supersedes only the preserve-exact-scalar-B2-route constraint identified
in MO16. It does not modify public legacy behavior, Q4/S3, native GE-B3 or B3.
The proposal remains an immutable historical design artifact; its pending
approval statement records its earlier status, not the current approval.

The canonical companion JSON freezes the identity, six scalar fixtures,
equations' source bindings, exact seven-node audit inventory, numerical core,
adapter and graph inventories, unit/range transforms, state/transport recipe,
limits and scientific thresholds. The equations in the proposal apply without
coefficient tuning. Independent equation review precedes implementation.

The core replaces the floor-bearing scalar bending/shear stiffness with
physical flexibility. Recover physical strains/resultants and their derivatives
from the same potential. Prove six physical basic modes and six rigid nulls.
For tiny clamped cases, compare energy/work RELATIVELY to nonzero physical
scales: the inherited max(1,norm) check alone would hide this obstruction.
No material floor, admission narrowing or effective-as-physical rigidity.

The SHEAR_SOFT fixture has A=2^-80, EI=1 and L=1. Form the two positive
flexibility eigenvalues independently and retain modal factors for force,
energy and recovery. Subtraction of nearly equal F entries cannot establish
the small mode. Dense tangent conditioning is a separate issue: neither
max-one checks nor a factored local pass qualifies every binary64 graph solve.
Overflow and positive-to-zero underflow examples are fixed in the JSON.

Length/force unit factors c,f transform A by c^2, I/J by c^4 and E by f/c^2;
translations by c, rotations unchanged. Compare forces as f, moments and energy
as f*c, strains unchanged and curvatures as 1/c. Entries of each tangent block
must use the corresponding force/displacement units, not one global factor.
Rigidity sweeps multiply E by the specified powers of two with geometry fixed.

Implementation is additive first: a new private physical core, independent
source-equation oracle tests, then a private matrix adapter. Existing frozen
owner/packets must not silently dispatch to it. A successor graph identity,
schema and complete runtime bindings are mandatory before graph propagation;
old packets must fail before family construction. No hot migration of accepted
history. Tests must prove detached outputs, failure atomicity and unchanged
public/other-family sources. No legacy corotational wrapper or numerical frame
differentiation is introduced. Reuse the accepted matrix chart by explicit
import only if unchanged equations and identity binding are checked.

The exact audit is standard-library rational algebra, not a mechanics run.
Before numerical execution, commit the complete implementation and runner,
bind the existing capsule and complete clean input graph, and independently
review. Retain existing Windows process-tree bounds and exclusive external
outputs. No full formal histories until Q4 recovery and all other open
MO01-MO18 gates are genuinely closed. Local correctness is not full parity.

Seven exact tests remain a separate inventory from numerical core, adapter,
graph and formal tests. Rehearsal evidence from the old operator is preserved
but cannot qualify the successor. Neither this approval nor a local pass
authorizes aliases, defaults, main integration, version or publication changes.
