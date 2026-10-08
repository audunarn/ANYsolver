# C1 development profile: initial disjoint patch approach

The restricted planar multi-face Q4/S3 static path admits explicitly paired
shell patches that have no projected overlap at the reference pose. The
surface orientation and physical sides are still fixed at registration.
`validate_general_contact` accepts the disjoint pose only for the restricted
multi-face profile; the older guided-pair profile retains its reference
overlap requirement.

The first-approach example moves a Q4 patch 0.5 m laterally while lowering it
by 0.5 µm toward two S3 V2D faces. It starts with zero overlap and ends with
0.27 m² of overlap, four active pressure nodes and a positive integrated
reaction. The independent gap certificate remains within its declared 6 µm
development tolerance. Run:

```text
python examples/general_contact_mixed_path.py --first-approach
```

This is one planar, frictionless, prescribed path. It does not establish
general automatic collision detection, arbitrary curved trajectories,
rotating shell sides, coincident-edge derivatives, self-contact or an
unqualified crossing guarantee. The paired shell path and its swept trial
limiter remain subject to the C1 numerical acceptance gates.
