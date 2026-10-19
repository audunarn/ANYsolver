"""Explicit-only disposable diagnostic launcher; not part of the CI inventory."""
import os
from pathlib import Path
import subprocess
import sys


def test_archived_record_charge_probe():
    evidence = Path(os.environ['CONTACT_CHARGE_PROBE_ROOT'])
    output = Path(os.environ['CONTACT_CHARGE_PROBE_OUTPUT'])
    repo = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, str(evidence / 'charge_probe.py'),
                    '--repo', str(repo), '--out', str(output)], cwd=repo, check=True)
    assert (output / 'complete.json').is_file(), 'probe did not complete'
