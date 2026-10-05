from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
source = (ROOT / 'probe-v1.py').read_text()
source = source.replace('ROOT = Path(__file__).resolve().parent', '''def convert(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError('unsupported diagnostic type '+type(value).__name__)

ROOT = Path(__file__).resolve().parent''')
source = source.replace('binding-v1.json','binding-v2.json')
source = source.replace('terminal-v1.json','terminal-v2.json')
source = source.replace('native-v1.json','native-v2.json')
source = source.replace('allow_nan=False','allow_nan=False,default=convert')
ast.parse(source)
(ROOT / 'probe-v2.py').open('x').write(source)
source = (ROOT / 'run-v1.py').read_text().replace('probe-v1.py','probe-v2.py').replace("'native-v1'","'native-v2'")
ast.parse(source)
(ROOT / 'run-v2.py').open('x').write(source)
(ROOT / 'writer-repair-v2.md').open('x').write('''# Failed diagnostic writer repair

v1 reached JSON writing but failed on an ndarray recovery payload; no numerical
output survived. Source/runtime/stderr and empty native-v1.json are preserved.
v2 changes serialization only, to the exact ndarray.tolist conversion used by
the historical native fixture runner. Same single Fy inventory/model/pinned
installed site/physical criteria/per-run budget. This is a failed Level-A
diagnostic repair, not replay of a formal or historical one-use authority.
The first preparation shell command had a quoting parser error; it launched
no Python process and changed no file. Saved preparation script avoids quoting.
''')
print('Prepared AST-checked v2 writer; original failed source retained.')
