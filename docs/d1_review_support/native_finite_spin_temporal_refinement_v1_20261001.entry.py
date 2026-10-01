from pathlib import Path
from hashlib import sha256
import json,os,runpy,sys
p=Path(sys.argv[1]);b=p.read_bytes()
assert sha256(b).hexdigest()==sys.argv[2]
spec=json.loads(b)
os.environ.update(spec["environment"])
sys.path[:0]=spec["pythonpath"]
runpy.run_path(spec["runner"],run_name="__main__")
