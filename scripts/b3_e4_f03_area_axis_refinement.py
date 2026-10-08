"""One-axis-at-a-time F03 finite-pad diagnostic, without physical qualification.

The common supervisor/evidence code is shared with the prior four-case
feasibility screen. This distinct runner is part of the registered source
identity and freezes 18 cases: baseline plus low/high values on each of
four axes for both independently assembled shell topologies.
"""

from pathlib import Path

import b3_e4_f03_area_feasibility as pilot


_BASE=(8,16,16,8)
_VARIANTS={
    'baseline':_BASE,
    'shell_x_low':(4,16,16,8),
    'shell_x_high':(16,16,16,8),
    'shell_y_low':(8,8,16,8),
    'shell_y_high':(8,32,16,8),
    'beam_low':(8,16,8,8),
    'beam_high':(8,16,32,8),
    'mortar_low':(8,16,16,4),
    'mortar_high':(8,16,16,16),
}
pilot.CASES={f'{topology}_{name}':(shell,*mesh)
             for topology,shell in (('q4','Q4'),('cst_cb','CST-CB'))
             for name,mesh in _VARIANTS.items()}
pilot.RUNNER=Path(__file__).resolve()
pilot.SOURCES=(pilot.RUNNER,*pilot.SOURCES)
pilot.KIND='experimental-classical-finite-pad-axis-refinement-v1'
pilot.SCOPE=(
    'one-axis Q4/CST-CB physical-response diagnostic; algebraic checks only; '
    'no saturation, independent reference, native coupling, G0B or G1 claim')
pilot.PARITY_REFERENCE={
    'q4_baseline':'a8e4496734b3225bd727b033bc623857543a90bebec4731b1181ec713fa22a9c',
    'cst_cb_baseline':'9e492bd09e2abf1c7d604e1be2abb613a1e2f58ca2d0e18c209a6087498bba3a',
}
pilot.CAPTURE_STATE=True


if __name__=='__main__':
    raise SystemExit(pilot.main())
