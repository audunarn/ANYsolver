from pathlib import Path
from hashlib import sha256
import json, os, runpy, sys
p=Path(sys.argv[1]); data=p.read_bytes()
assert sha256(data).hexdigest()==sys.argv[2]
spec=json.loads(data)
os.environ.update(spec["environment"])
sys.path[:0]=spec["pythonpath"]
runpy.run_path(spec["runner"],run_name="__main__")
