"""One targeted shell-resolution change; preserve original screen and results."""
from pathlib import Path
raw=Path(__file__).resolve().parent
source=(raw/'screen-v1.py').read_text()
old="""shell=ss.ShellPanel((1,2,3,4,5,6),tuple((x,y,0.) for y in (-.05,.05) for x in (-1.,0.,1.)),
    ((1,2,5,4),(2,3,6,5)),2e-5,E,nu,density)
model=ss.LinearDefinition(ss.B3_GE_E4_PL_STIFFENED_SHELL_V1,shell,beams,
    tuple(ss.PointConnection(i,100+2*i-1) for i in (1,2,3)),
    tuple(ss.FixedCoordinate('shell',i,k) for i in (1,3,4,6) for k in range(6)),
    q4_pullback_policy=ss.Q4_ALGORITHMIC_PULLBACK_V1)
weights=np.zeros(11)"""
new="""shell=ss.ShellPanel(tuple(range(1,11)),tuple((x,y,0.) for y in (-.05,.05) for x in (-1.,-.5,0.,.5,1.)),
    ((1,2,7,6),(2,3,8,7),(3,4,9,8),(4,5,10,9)),2e-5,E,nu,density)
model=ss.LinearDefinition(ss.B3_GE_E4_PL_STIFFENED_SHELL_V1,shell,beams,
    tuple(ss.PointConnection(i,j) for i,j in ((1,101),(3,103),(5,105))),
    tuple(ss.FixedCoordinate('shell',i,k) for i in (1,5,6,10) for k in range(6)),
    q4_pullback_policy=ss.Q4_ALGORITHMIC_PULLBACK_V1)
weights=np.zeros(15)"""
assert old in source
source=source.replace(old,new).replace('.1*shell.thickness_m/4','.05*shell.thickness_m/4')
source=source.replace('weights[6+2*i:9+2*i]','weights[10+2*i:13+2*i]')
for name in ('result-v1.json','last-prefix.checkpoint','turning-predecessor.checkpoint','turning-successor.checkpoint'):
    newname=name.replace('-v1','-v2') if '-v1' in name else name.replace('.checkpoint','-v2.checkpoint')
    source=source.replace(name,newname)
assert not (raw/'screen-v2.py').exists()
(raw/'screen-v2.py').write_bytes(source.encode('ascii'))
runner=(raw/'run-v1.py').read_text().replace('screen-v1.py','screen-v2.py').replace("'screen-v1'","'screen-v2'")
(raw/'run-v2.py').write_bytes(runner.encode('ascii'))
print('Prepared four-Q4 shell discriminator; beam, laws, physical supports/ties/load/metric rule unchanged.')
