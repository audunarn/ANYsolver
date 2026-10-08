"""Independent Decimal Q1 weighted-gap values for a captured Q4/S3 pair."""

from __future__ import annotations

from decimal import Decimal, localcontext
import json
from pathlib import Path

from scripts.general_contact_d1_wedge_decimal_oracle import d, work


ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "reports/general_contact_d1_distributed_pair28_capture_20260927.json"
OUTPUT = ROOT / "reports/general_contact_d1_distributed_pair28_decimal_20260927.json"
if OUTPUT.exists():
    raise FileExistsError(OUTPUT)

capture = json.loads(CAPTURE.read_text(encoding="utf-8"))
with localcontext() as context:
    context.prec = 80
    reference = [tuple(map(d, row)) for row in capture["source_reference"]]
    source = [tuple(map(d, row)) for row in capture["local_source"]]
    target = [tuple(map(d, row)) for row in capture["local_target"]]
    rows = []
    for order in (4, 8, 12):
        values = []
        for index in range(4):
            pressure = tuple(Decimal(int(j == index)) for j in range(4))
            value, area, signature = work(reference, source, target,
                                          pressure, order)
            values.append(str(value))
        rows.append({"quadrature_order": order,
                     "weighted_gap_m3": values,
                     "projected_area_m2": str(area),
                     "clip_signature": signature})

record = {
    "capture": str(CAPTURE.relative_to(ROOT)),
    "precision_digits": 80,
    "input_conversion": "exact binary64 to Decimal",
    "local_values_m3": capture["local_values_m3"],
    "derivative_values_m3": capture["derivative_values_m3"],
    "rows": rows,
}
OUTPUT.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"orders": [row["quadrature_order"] for row in rows],
                  "oracle_12_m3": rows[-1]["weighted_gap_m3"]}, indent=2))
