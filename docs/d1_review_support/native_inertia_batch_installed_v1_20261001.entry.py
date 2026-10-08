from pathlib import Path
from hashlib import sha256
import json,os,runpy,sys
p=Path(sys.argv[1]);data=p.read_bytes()
assert sha256(data).hexdigest()==sys.argv[2]
r=json.loads(data)
os.environ.update(r['environment'])
runpy.run_path(r['installed_entry'],run_name='__main__')
