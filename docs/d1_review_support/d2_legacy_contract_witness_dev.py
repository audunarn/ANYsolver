"""Development metadata witness; no accepted solve or consumed authority rerun."""
import json
from pathlib import Path
import numpy as np
import anysolver.general_contact.s3_patch_static as owner
from test_general_contact_q4_s3_refined_patch import _two_q4_two_s3
from test_general_contact_q4_s3_jet2_static_owner import _settings
from dataclasses import replace
import sys
model, definition, settings = _two_q4_two_s3()
settings = replace(_settings(settings), q4_source_gap_certificate="overlap_local_dev")
manager = owner.GeneralS3PatchManager(model, definition, settings)
record = {"contract": manager.restart_contract(),
          "open_result": manager.evaluate(np.zeros(manager.n_dof), tangent=False)[2].to_dict()}
Path(sys.argv[1]).write_text(json.dumps(record, sort_keys=True, separators=(",", ":"), default=lambda x: x.item() if isinstance(x, np.generic) else x), encoding="utf-8")
print(owner.__file__)
