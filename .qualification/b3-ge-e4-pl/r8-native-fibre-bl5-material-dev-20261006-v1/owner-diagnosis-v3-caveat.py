from pathlib import Path
import hashlib, json
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
md=ROOT/'owner-diagnosis-v3.md';handoff=ROOT/'owner-diagnosis-v3-handoff.json'
for source,name in ((md,'owner-diagnosis-v3-reviewed-before-caveat.md'),(handoff,'owner-diagnosis-v3-handoff-before-caveat.json')):
    snapshot=ROOT/name;assert not snapshot.exists();snapshot.write_bytes(source.read_bytes())
text=md.read_text()
old='''If both pass, the saved last rejection is
consistent with an ordinary yield-boundary obstruction and the complete FD failure
is mainly a kinematic/representation diagnostic issue; the next implementation
decision must address the global branch transition under separately adopted
authority, rather than treating sparse scaling or a material tangent bug as proved.'''
new='''If both pass, the check isolates the existing material compliance and fixed-origin
consistency; it does NOT prove the complete FD error is kinematic noise. Assembly
or chart derivative bias and representation effects remain unresolved. The saved
last rejection is consistent with an ordinary yield-boundary obstruction, but
that separate consistency evidence is not a whole-system tangent pass or a cure
for global convergence. Any next implementation decision needs separately adopted
authority; sparse scaling or a material tangent bug is not established here.'''
assert old in text;text=text.replace(old,new);md.write_text(text)
record=json.loads(handoff.read_text())
record['material_discriminator_pass_caveat']='A pass isolates material compliance/fixed-origin consistency only. It does not prove completeFD error is kinematicnoise; assembly/chart derivativebias and representation remain unresolved.'
record['reviewed_before_caveat_preserved']=dict(markdown_sha256=sha(ROOT/'owner-diagnosis-v3-reviewed-before-caveat.md'),handoff_sha256=sha(ROOT/'owner-diagnosis-v3-handoff-before-caveat.json'))
for name in ('owner-diagnosis-v3.md','owner-diagnosis-v3-reviewed-before-caveat.md','owner-diagnosis-v3-handoff-before-caveat.json','owner-diagnosis-v3-caveat.py'):
    p=ROOT/name;record['new_files'][name]=dict(sha256=sha(p),bytes=p.stat().st_size)
for name in ('raw-artifact-sha256.json','raw-artifact-sha256-v2.json'):
    manifest=json.loads((ROOT/name).read_text())
    for path,row in manifest['artifacts'].items():assert sha(ROOT/path)==row['sha256'],path
handoff.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(caveat_explicit=True,original_versions_preserved=True,consumed_manifest_counts=[760,779],handoff_sha256=sha(handoff))))
