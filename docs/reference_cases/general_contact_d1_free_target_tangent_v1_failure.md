# Free-target mixed tangent v1: failed registered moment gate

The [registration](general_contact_d1_free_target_tangent_v1.json)
(SHA256 `dbd19a856c2f2dd038556f37696c61c3f537b7fcc879ff825083afa50d89ecc0`)
was committed before one mixed source/target run. The saved pose is
kinematically admissible under the new left-edge target clamp but is not
established as an equilibrium of that altered model.

The [raw report](../../reports/general_contact_d1_free_target_tangent_v1_formal_20260927.json)
(SHA256 `10c9f9ae8b887223927fe9646e7be21d47ee07a2592d77fc13cfc46a0b2965bc`)
completed in 48.040 s. The [frozen-criteria verdict](../../reports/general_contact_d1_free_target_tangent_v1_verdict_20260927.json)
(SHA256 `8c335e79965258e084c944dd6a4d89d1d8ede70c5f1351635024f1782995c6d0`)
is **FAIL**. All branch, identity, pose, pressure, resource, coupled-force,
coupled-moment and mapped-contact-force predicates pass. The mapped-contact
moment relative errors are 0.0113516 and 0.00567581 at h=1e−6 and
5e−7 m, above the frozen 1e−5 limit. Its moment action is only
0.000318640 Nm/m, so the corresponding absolute derivative difference is
about 3.62e−6 and 1.81e−6 Nm/m. The halving ratio is consistent with the
first-order truncation of the negative one-sided difference, but this
interpretation is not a passed derivative gate.

The next bounded diagnostic compares a second-order one-sided difference
on the same negative active-set branch at the original step sizes. That
new calculation cannot change this failed verdict. The full contact
programme and general C1 remain open.
