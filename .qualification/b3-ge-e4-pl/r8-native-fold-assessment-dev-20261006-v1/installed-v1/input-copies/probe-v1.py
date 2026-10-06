from pathlib import Path
import json
from examples import stiffened_shell_native_fold_assessment as assessor

def run(folder):
    folder = Path(folder)
    (folder/'screen-started.json').write_text(json.dumps(dict(scope='one saved g13/g14/g15 assessment',endpoints=3,borders=3,assemblies=15))+'\n')
    saved = Path(__file__).resolve().parents[2]/'r8-native-proportional-capacity-dev-20261006-v1/installed-v1'
    result = assessor.assess_saved_prefixes(saved)
    (folder/'assessment-result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return 0
