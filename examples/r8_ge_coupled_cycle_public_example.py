"""Run the connected installed public cycle after exact root adoption/transfer.

Preparation alone grants no execution. The supervisor enforces fresh bounded
authority; the example never rebuilds a package or resets material histories.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.r8_ge_coupled_cycle_dev import launch

if __name__=='__main__':
    raise SystemExit(launch('installed-cycle'))
