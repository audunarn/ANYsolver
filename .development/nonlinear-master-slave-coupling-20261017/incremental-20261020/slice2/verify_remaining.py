"""Supply an explicit preparation plugin to the existing portable runner."""
import os
from pathlib import Path
import runpy
import sys

here = Path(__file__).resolve().parent
os.environ['PYTHONPATH'] = str(here) + os.pathsep + os.environ.get('PYTHONPATH', '')
os.environ['PYTEST_PLUGINS'] = 'slice2_saved_reference'
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
