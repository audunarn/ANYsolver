from pathlib import Path
import hashlib
import json
import argparse
from threadpoolctl import threadpool_info
from scripts.b3_e4_bl5_scalar_lifting_dev import lifting_case

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
assert not args.output.exists()
pools = threadpool_info()
assert pools and all(p['num_threads'] == 1 for p in pools)
previous = Path('previous.json')
row = lifting_case(8, 2, 16, 1)
assert row['span'] == 2 and row['supports'] == 8
result = dict(status='COMPLETED_DEVELOPMENT_ONLY', corrected_saved_work_map_anchor=row,
    previous_sha256=hashlib.sha256(previous.read_bytes()).hexdigest(),
    scope='anchor correction only; unchanged 21 c2 cases reused from bound previous result',
    finding='V2 anchor used c2/span4 rather than saved c1/span2; do not score saved native fixture with c2 floor',
    threads=pools)
with args.output.open('x', encoding='utf-8') as output:
    json.dump(result, output, indent=2)
print(json.dumps(dict(status=result['status'], anchor_floor=row['prospective_product_floor'])))
