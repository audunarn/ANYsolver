"""Coupled EP load sweep below collapse.

Checks:
  A. pre-yield: EP == elastic (alpha == 0, uz identical)
  B. small rotation: corotational ~= von_karman (same material)
  C. post-yield: EP deflection >= elastic deflection (softer)
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ep_isolation import shell_model, run  # noqa: E402

for fz in (-2000.0, -6000.0, -10000.0, -14000.0):
    for kin in ("von_karman", "corotational"):
        el = run(lambda: shell_model(1e4, True, fz), kin, steps=6)
        ep = run(lambda: shell_model(1.0, True, fz), kin, steps=6)
        print(f"Fz/node={fz:+8.0f} {kin:12s} EL: {el} | EP: {ep}", flush=True)
