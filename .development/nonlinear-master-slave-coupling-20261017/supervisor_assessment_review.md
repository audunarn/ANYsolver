# Independent review of analytical/mesh assessment implementation

Read-only static review, 2026-10-18. Reviewed diagnostics/arc_reference.py,
assessment_support.py, mesh_study.py, analytical_derivation.md, the adopted
supervisor_findings decisions, and only the supporting builder/constraint and
reaction symbols needed to check entry paths. No imports, numerical solves,
pytest, diagnostic edits or product edits were performed. Mistral retains
exclusive numerical execution during its active assignment.

## Findings requiring correction or explicit qualification

### A1 — P2: named root My is not the total constrained root-section reaction

arc_reference.py:163–164 reads only
`result.steps[-1].support_reactions['root']`. The root boundary at line121
contains just the center shell node's ux,uz,ry. Outer root nodes' ux,uz,ry are
affine dependents of that node through the cylinder row equations at lines85–93.
They therefore carry physical section-force/moment terms that are absent from
the named support sum.

The inspected production `_support_reaction_resultants` at
nonlinear_static.py:1656–1721 simply sums DOFs explicitly listed in each boundary.
The rotating-MPC reaction transfer relocates beam reactions to shell masters,
but it does not propagate the outer shell row's generic affine reactions to the
center support. The added from-forces helper also only selects named support
DOFs; it does not change this conclusion.

Consequently root_My_balance_relative is not a physical moment-balance metric
for this model. An ideal concentric cylindrical field already demonstrates the
issue analytically: the center node carries half the shell end moment under the
consistent [1/4,1/2,1/4] distribution. The named root sum contains Mb+Ms/2,
while the actual section resultant is Mb+Ms. At e=0 the apparent relative deficit
is (1.75/2)/3.15=27.7778%, despite exact equilibrium. This is a deterministic
reaction-accounting counterexample, not an FE result.

Bounded correction: reuse the independently assembled full imbalance and
rotating beam-slave-to-master transfer, then sum the three root shell nodes'
section forces and moments. Root rotations are zero, so their ry covectors
equal spatial My; include appropriate deformed force arms for any more general
spatial resultant. This has no extra constitutive evaluation cost. Keep the raw
named support result separately if useful and label it as such. Do not repair
this benchmark diagnostic by broadening product reaction APIs or replacing row
ties with conflicting extra supports. The current accuracy/equilibrium gates do
not use this incorrect moment metric, so it does not by itself create a false
accuracy pass; it creates misleading reported evidence.

### A2 — P2: actual terminal moment omits achieved lambda on incomplete cases

arc_reference.py:161–162 uses the full unit-factor beam force and centroid
moments when forming actual_terminal_moment_Nm. All these forces/moments are
proportional loads. For a returned state with load factor lambda!=1 the actual
external moment is

    lambda * [cross(current_separation, reference_beam_force)
              + reference_shell_centroid_moment
              + reference_beam_centroid_moment].

The current record instead reports the hypothetical unit-factor moment at that
geometry and compares it with achieved-load reactions. Multiply every term by
result.load_factor, or rename the existing value explicitly as the unit-load
moment and additionally record the actual moment. Completed lambda1 cases are
unaffected. `assessment_support.equilibrium` correctly uses achieved lambda;
this finding is confined to the separate moment diagnostic.

### A3 — P2: mesh summary silently overwrites duplicate evidence for one case

mesh_study.py:57–58 builds a dictionary comprehension keyed by case. Providing
two retained JSON records for one case silently chooses the last path, whereas
arc_reference.summarize correctly raises on duplicates. An old failed/partial
case followed by a passing retry can therefore disappear from the summary with
no indication that selection occurred. Exact input/candidate identity also
matters when retrying a repaired source.

Use the same explicit duplicate refusal as the arc summarizer, or require an
explicit selected-case manifest that records all superseded attempts and their
identities. Do not make argument order an implicit acceptance-selection rule.
This can be checked with tiny synthetic JSON records without an FE solve.

### A4 — P2: arc summary does not establish adopted extension eligibility

arc_reference.py:199–215 sorts whatever levels were supplied and compares only
the final two. Base8/16/32 presence is checked, but a supplied set
8/16/32/256 can still pass without the prospectively required64/128 evidence.
Nor does the summary report/check the adopted condition that analytical errors
must decrease before authorizing each extension. Thus its top-level passed flag
alone does not establish the in-order/decreasing-error refinement contract.

Either enforce a prefix of [8,16,32,64,128,256] and record extension eligibility
from the previous level's frozen displacement/rotation errors, or bind the
summary to an explicit independently inspected execution/selection manifest
that establishes those conditions. This does not require changing any physical
input, tolerance or existing run authority. If Astra enforces these conditions
outside this script, label that external check explicitly rather than treating
the current summary flag as complete proof of it.

## Checks that agree with the adopted reference

- The scalar oracle is independent of production assembly/reduction. It uses
  As=Wt, Ab=bh, Is=Wt^3/12, Ib=bh^3/12, EA-weighted neutral axis, composite
  rigidity with the parallel-axis term, engineering strain and reference-length
  curvature. At e=0/.002 the rigidities are3.15/17.15 N m^2 as required.
- Beam section Iy uses the .002m depth in z; Iz uses the .01m width in y.
  Material is linear elastic with nu=0; the small-strain guard admits the
  prescribed maximum .27925% strain and does not invoke S355 plasticity.
- Positive ry bends toward negative z. Shell/beam radii 1/k-zbar and
  1/k+e-zbar, centroid tip formulas, tensile Nb/compressive Ns, final-tangent
  dead-force signs and separate centroid My all match the independent derivation.
  No total composite moment is counted twice. For this single-axis field
  additive ry covectors equal spatial My.
- Every x-row has exact common ux,uz,ry through upstream affine shell ties;
  uy,rx,rz are fixed and only center root ux,uz,ry are prescribed. There is no
  support/MPC duplicate dependent definition. These ties consume shell DOFs,
  not rotating beam-slave translations, and therefore are compatible with the
  new fail-closed downstream guard. No cross-width freedom remains that would
  invalidate the adopted cylindrical-strip idealization.
- The beam interpolation nodes/weights use the intended same longitudinal
  geometry, with matching nb=nx and nonmatching nb=1.5nx. The oracle does not
  compensate for their chord errors. e=0 explicitly requests work_conjugate,
  avoiding the inactive-descriptor auto-mode change in force law.
- Assessment requests force control, twelve steps, forty Newton iterations,
  tolerance1e-8. Reached status requires completed and lambda1. Analytical
  displacement-vector and ry errors, and final vector/ry refinement changes,
  use the prospectively adopted normalizations. Both shell and beam tips are
  checked; component errors are also retained. No prescribed rotation makes
  the accuracy test tautological.
- equilibrium() reconstructs at result.load_factor, copies accepted state and
  displacement before assembly, compares both original and supplied copied
  state after assembly, and normalizes residual by max(norm(J.T F_actual),1).
  It therefore corrects the earlier unit-load DC residual issue for these
  assessment cases. Constraint status is the production postcheck; this is not
  a claim of a separately implemented nonlinear constraint oracle.
- Requested mesh identities R1–R4, M1–M4, P1–P4 and loads12/140kN match the
  assignment. M/P last uz and ry refinements and M4/P4 gaps are tested. The
  linear solves are inside the per-case execution, not hidden in a summarizer.
  Nonmonotonicity reporting currently covers uz only; record ry sequences too
  if the requested report is intended to cover both measured convergence fields.
- The supporting convergence_study import has its numerical entry points under
  `if __name__ == '__main__'`; importing its builder does not itself launch a
  study. CLI case construction/output paths show no independent execution bug
  in this static review.

## Limits of this assessment

No runtime API/admission, convergence, residual value, refinement feasibility,
performance or budget claim is established here. In particular the known
nonmatching chord bias remains a real discretization risk, not a reason to fit
the reference or relax the gates. These findings concern the actual assessment
code and its reported evidence; numerical results remain to be produced by the
authorized owner under the unchanged shared allowance.

## Recheck after Astra instrumentation corrections

A1 and A2 are resolved by the updated source at this static recheck:

- equilibrium(..., root_nodes=...) reuses the same independent full imbalance,
  transfers rotating beam slave terms when active, then aggregates deformed-arm
  forces and moments over the three shell root nodes plus the beam root. For
  e=0, where no rotating map exists, including the beam root directly is correct.
  For e>0 its transferred force/moment entries are zero, so its inclusion does
  not double count. The root zero-rotation assertion makes the direct rotational
  covector/spatial-moment equality valid.
- The arc case now reports the raw named center-support result separately and
  compares the physical root moment against actual external moment.
- actual_M is scaled by result.load_factor after both force-couple and intrinsic
  moment terms are formed. Partial-result moment evidence now uses achieved load.

No added raw named-reaction gate is needed. Remaining A3/A4 summary-selection
findings remain as above pending an implementation correction or an explicitly
checked external manifest. No numerical checks were performed for this recheck.

## Recheck of summary repairs and DC augmented classification

The current mesh summarizer explicitly rejects duplicate case keys instead
of silently overwriting them. A3 is resolved statically.

The current arc summarizer requires the exact ordered prefix of
[8,16,32,64,128,256]. For every additional level it checks the preceding two
levels were complete, the maximum of frozen displacement-vector and ry relative
errors decreased, and at least one previous last-change metric still exceeded
.25%. Eligibility is checked from evidence available before the extension,
rather than letting the extension justify its own launch afterward. A4 is
resolved under this explicit maximum-principal-error interpretation of “errors
decrease.” Individual case errors remain available; no accuracy/refinement
threshold changes.

Physical reaction reconstruction remains correct for the declared zero-rotation
root: all three shell root nodes and beam root are included; e=0 beam terms are
summed directly; e>0 terms are transferred with their lever moment and zeroed
before summation; deformed force arms are included; actual external moments are
scaled by achieved lambda. Raw named center-support values remain separately
labelled. No further concrete assessment-code defect was found in this recheck.
This is static closure, not numerical acceptance.

### D1 — P1: ordinary DC augmented matrix must be classified GENERAL

At nonlinear_static.py:4104–4120 the ordinary DC helper forms

    A = [[K_red, -F_prop_red],
         [row_jac,       0]].

It declares GENERAL only if general_tangent is true, otherwise
SYMMETRIC_INDEFINITE. general_tangent describes the structural/equilibrium
tangent's follower/legacy-consistent/contact conditions. It does not establish
symmetry of A. Even when K_red is symmetric, A is symmetric only if row_jac
equals -F_prop_red, which the DC contract does not require or generally satisfy.

The declaration has concrete backend consequences. linalg.py:294–325 sends
SYMMETRIC_INDEFINITE to PARDISO mtype -2 first and prepares only the upper
triangle. The omitted control row is replaced by the transposed load column.
Fallback to general mode occurs only on factorization failure (538–568), not on
a residual check of the original A. The solve wrapper checks finite output but
not the original-system residual (970–991). It can therefore successfully solve
a different symmetric matrix and return a wrong Newton increment. SciPy general
LU can conceal the declaration error; no runtime backend or causal diagnosis is
inferred here.

Exact scalar counterexample without numerical execution: K=1, F_prop=1,
row_jac=1, rhs=(0,1). The intended [[1,-1],[1,0]] has solution (dq,dlambda)=(1,1).
A symmetric backend consuming its upper triangle solves [[1,-1],[-1,0]] instead,
obtaining (-1,-1), which violates the actual control row by2. Structural
symmetry is therefore insufficient.

Bounded repair: use MatrixClass.GENERAL unconditionally for this assembled
ordinary DC augmented system. No formulation, tolerance, load, target or public
compatibility change is needed. Keep the block elimination fast path separate:
it factorizes K_red and solves the scalar control equation explicitly, so this
finding does not require changing that structural symmetric declaration.

Focused owner verification: capture the ordinary dead-load/work-conjugate DC
factorization call and assert GENERAL even when K_red is symmetric. A tiny fake
symmetric-only backend or the exact matrix above can discriminate the behavior
without installed PARDISO. Check the original augmented residual and target,
not merely factorization status. Numerical authority remains unchanged.

No imports, solves or tests were performed in this follow-up; Mistral remains
the product repair and numerical-execution owner.
