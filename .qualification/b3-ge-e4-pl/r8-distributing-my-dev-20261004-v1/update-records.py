from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
active=REPO/'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md'
shutil.copyfile(active,ROOT/'active-before-my.md')
text=active.read_text(encoding='utf-8')
start=text.index('Next discriminator: ONE separately bound unitMy')
end=text.index('\n## Exact state',start)
text=text[:start]+'''Latest My discriminator completes: direct compliance difference0.019364%,
native/solid reciprocal errors6.785e-17/2.602e-15 (solid bound1.232e-13).
No missing pitch-work channel indicated. This supports My only, not nativeMx
adequacy or full6channel/finite fidelity. Source/provenance and serializer issues
repaired; original failed native/empty output remains rejected and preserved.

Next scientific discriminator: ONE separately bounded native80x32 Mx/My on
unchanged physical pad/support/law/b7artifact, onefactor/full6poses/work and
absolute cross coupling. New builder must reproduce allowed40x16 exactly;
historical donor still rejects80x32. Runtime/memory unmeasured:600s/2GiB limits.
Significant movement threatening original1% comparison leaves adequacy open;
small movement supports measured mesh-pair stability only. No asymptotic claim,
automatic next mesh/solid campaign, threshold change or line-law substitute.
''' +text[end:]
text=text.replace('pre-slice HEAD02cc1ed4','pre-slice HEAD3f6ae11a')
text=text.replace('Latest raw .qualification/b3-ge-e4-pl/r8-distributing-thickness-dev-20261004-v1','Thickness raw .qualification/b3-ge-e4-pl/r8-distributing-thickness-dev-20261004-v1')
text=text.replace('All numerical jobs and supporting reviewers terminal; no process needs recovery.', '''Latest My raw .qualification/b3-ge-e4-pl/r8-distributing-my-dev-20261004-v1
pins final v3 jobs/comparison,23 initial controls/1final changed control,419
actual installed source hashes and preserved failure/repair history. Numerical
jobs terminal; bounded next-implementation Read review may still be running.''')
active.write_text(text,encoding='utf-8',newline='')
for name in ('B3_GE_E4_PL_REVISION_8_PLAN.md','B3_GE_E4_PL_REVISION_8_GOAL.md'):
 p=REPO/'docs/agent_plans'/name;shutil.copyfile(p,ROOT/('before-'+name))
 text=p.read_text(encoding='utf-8')
 if name.endswith('PLAN.md'):
  marker='  tolerance, finer campaign, formalF03 consumption or aggregate pass follows.'
  assert marker in text
  text=text.replace(marker,marker+'''
  Completed My direction: direct compliance0.019364% difference and reciprocal
  work controls pass. Next ONE new native80x32 Mx/My adequacy check, same law/
  pad/support/b7 artifact,1factor, old donor guards intact and exact40x16 builder
  parity. Significant movement leaves adequacy open; small movement supports
  measured pair stability, not an asymptotic bound or aggregate acceptance.''')
 else:
  marker='alone establish Mx convergence. All mandatory rows and authorities remain.'
  assert marker in text
  text=text.replace(marker,marker+'''
My comparison is now complete with0.019364% direct compliance difference and
reciprocal work controls. Next ONE separately bounded native80x32 Mx/My check
with unchanged physical law/support/artifact and preserved old guards targets
mesh adequacy; no asymptotic claim or automatic next refinement follows.''')
 p.write_text(text,encoding='utf-8',newline='')
p=REPO/'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'
with p.open('a',encoding='utf-8',newline='') as f:f.write('''
F04 independent My direction, 4 October — IMPLEMENTED_NOT_QUALIFIED.
Unchanged40x16 native/b7 and solidnz4: direct work difference0.019364%,
reciprocal discrepancies6.785e-17/2.602e-15 within stated numerical/decimal
bounds. Full poses and stub/root/transfer controls retained. Original23PASS/
final changed-control1PASS and failed serialization/recheck evidence preserved.
Next one separately bounded native80x32 Mx/My check targets remaining adequacy;
old donor guards remain. No convergence/full6channel/finite/aggregate pass.
FormalF03 UNCONSUMED. [Evidence](development/r8-distributing-reference-linear-20261004/results.md).
''')
snapshot=ROOT/'final-bytes';snapshot.mkdir()
for rel in ('scripts/r8_e02_distributing_my.py','scripts/r8_e02_distributing_feasibility.py','tests/test_r8_e02_distributing_my.py'):
 p=snapshot/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/rel,p)
files=[p for p in ROOT.rglob('*') if p.is_file() and not any(part.startswith('pytest-') or part=='__pycache__' for part in p.relative_to(ROOT).parts)]
inventory={str(p.relative_to(ROOT)).replace('\\','/'):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files}
(ROOT/'inventory.json').open('x',encoding='utf-8').write(json.dumps(inventory,indent=2)+'\n')
print(json.dumps({'retained_files':len(files),'bytes':sum(x['bytes'] for x in inventory.values())}))
