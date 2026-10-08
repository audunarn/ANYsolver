"""Shared pytest configuration.

PyCharm may launch pytest with ``tests`` as the process working directory,
while several integration tests intentionally execute repository scripts by
relative path.  Normalize the working directory once for the full session so
those tests behave identically from PyCharm, PowerShell and CI.
"""

from __future__ import annotations

import os
from pathlib import Path


_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
os.chdir(_REPOSITORY_ROOT)


import pytest


@pytest.fixture(scope="module")
def f03_q8_sided_faces():
    """Manufactured face geometry for bounded algebra, not external evidence.

    Four by eight serendipity cells on each face, with distinct plate/bar
    ownership even at their coincident interface. No saved deck, solver output,
    physical supports or historical qualification files are required.
    """
    import numpy as np

    coords = {}
    domains = []
    for heights in ((-.0175, .0175), (.0175, .1175)):
        domain = set()
        for z in heights:
            for i, x in enumerate(np.linspace(.9, 1., 9)):
                for j, y in enumerate(np.linspace(-.05, .05, 17)):
                    if i % 2 and j % 2:  # Q8 omits cell-centre nodes.
                        continue
                    node = len(coords) + 1
                    coords[node] = np.array((x, y, z))
                    domain.add(node)
        domains.append(domain)
    assert len(coords) == 484 and not domains[0] & domains[1]
    return coords, *domains
