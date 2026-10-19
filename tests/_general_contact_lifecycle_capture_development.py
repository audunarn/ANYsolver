"""Explicit-only disposable lifecycle launcher; never add to CI inventory/commit."""
import os
from pathlib import Path
import subprocess
import sys


def test_saved_lifecycle_record_capture():
    base = Path(os.environ['CONTACT_LIFECYCLE_ROOT'])
    output = Path(os.environ['CONTACT_LIFECYCLE_RECEIPT'])
    repo = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, str(base/'entry.py'), '--repo', str(repo),
                    '--receipt', str(output), '--profile', os.environ['CONTACT_LIFECYCLE_PROFILE']],
                   cwd=repo, check=True)
    assert (output/'capture'/'completion.json').is_file()
