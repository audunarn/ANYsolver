from pathlib import Path
import ast, datetime, hashlib, json, sys
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
preserved={}
for name in ('raw-artifact-sha256.json','raw-artifact-sha256-v2.json'):
    path=ROOT/name;data=json.loads(path.read_text());mismatches=[]
    for artifact,record in data['artifacts'].items():
        if sha(ROOT/artifact)!=record['sha256']:mismatches.append(artifact)
    assert not mismatches,mismatches
    preserved[name]=dict(sha256=sha(path),artifacts_verified=len(data['artifacts']),mismatches=mismatches)
names=('owner-diagnosis-v3.py','owner-diagnosis-v3.json','owner-diagnosis-v3-detail.py','owner-diagnosis-v3-detail.json',
       'owner-diagnosis-v3-branch.py','owner-diagnosis-v3-branch.json','owner-diagnosis-v3-correct.py',
       'owner-diagnosis-v3-corrected.json','owner-diagnosis-v3-rounding.py','owner-diagnosis-v3-rounding.json',
       'owner-diagnosis-v3-procedure-failure.json','owner-diagnosis-v3.md','owner-diagnosis-v3-finalize.py')
for name in names:
    if name.endswith('.py'):ast.parse((ROOT/name).read_text())
sources=('src/anysolver/_stiffened_shell_ge_experimental.py','src/anysolver/_stiffened_shell_ge_finite_experimental.py',
         'src/anysolver/_ge_beam3_generalized_static_boundary.py','src/anysolver/_ge_beam3_retained_fibre.py',
         'src/anysolver/_ge_beam3_retained_generalized.py','src/anysolver/_ge_beam3_p5/compensated.py',
         'src/anysolver/_ge_beam3_p5/compensated_coordinates.py','src/anysolver/_ge_beam3_fibre_cell.py',
         'src/anysolver/_ge_beam3_fibre_section.py','examples/stiffened_shell_native_fibre_bl5.py')
assert not any(n=='numpy' or n.startswith('numpy.') or n=='scipy' or n.startswith('scipy.') for n in sys.modules)
report=dict(state='READ-only saved-data diagnosis complete; implementation/material gates unchanged',
    finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),preserved_consumed_evidence=preserved,
    new_files={n:dict(sha256=sha(ROOT/n),bytes=(ROOT/n).stat().st_size) for n in names},
    inspected_source_sha256={n:sha(REPO/n) for n in sources},
    primary_finding='Last .3125 line rejection crosses a fixed-origin native fibre activity boundary; five-channel saved K/residual fit predicts h*=.00017062445044 below minimumdyadic1/4096. Branch slopejump accounts for nonlinear residual increase.',
    derivative_finding='Whole-free-KKT FD errors reproduced exactly; >99.9999979%squared error in four axial compatibility rows on both generalized and fibre members, with near-cancelling geometric/material directional terms and subULP cell-diagonal sensitivities. FD states/term provenance absent; not a tangentPASS.',
    causal_sizes=dict(current_work_norm=1.8097776464862212,original_linear_defect_work=4.4499433461842295e-7,
        last_candidate_nonlinear_defect_work=.02414971862148017,last_candidate_row108_defect_work=.024119738722753522),
    eliminated_as_demonstrated_cause=['retained force/moment scale packing in this diagnostic','multiplier-tail norm contamination as dominant error','sparse linear residual magnitude as source of current .0306merit','a fibre-only derivative defect inferred from whole-direction FDerror','insufficientdyadicreach as complete programme cure (quadraticcandidate alreadyfailed24Newton)'],
    unresolved=['explicit return-map branch labels and signed margins at transition were notsaved','actual FD plus/minus states and separate kinematic/material values missing','global .3125 convergence beyond final rejection not established','full simultaneous shell/fibre and mixedgeneralized yielded gates unchanged'],
    proposed_discriminator='ONE fixed-origin geometry-frozen coupled-cell material-only savedNewtonresultant direction: p0,p0±1e-4dp and savedlastcandidatep; pairedDecimal gradient/compliance, explicit station0fibre1 branch/margin. No global solve/newfixture/tolerancechange; proposalonly/noauthority consumed.',
    execution=dict(numerical_imports=False,solver_evaluations=0,material_evaluations=0,linear_solves=0,
                   global_solves=0,product_edits=0,numerical_lease='not granted or acquired',owned_numerical_processes=0),
    procedure_failure='Preserved NameError in stdlib helper namespace, repaired before detailoutput; reviewedoriginal rolelabelbug preserved and corrected in newfile')
target=ROOT/'owner-diagnosis-v3-handoff.json';assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(state=report['state'],preserved_counts={k:v['artifacts_verified'] for k,v in preserved.items()},new_files=len(names),numerical_evaluations=0)))
