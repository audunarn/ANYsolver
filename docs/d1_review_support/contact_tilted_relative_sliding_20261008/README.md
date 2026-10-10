# Tilted relative Q4 sliding development

Opt-in `finite_frame_seed="per_surface_reference_frames_dev"` uses the two named complete ContactSurface selections as structural body partitions. Each must be a disjoint connected component covering every model element, node and DOF, with a complete six-coordinate unit-control anchor. The seed transports each body's committed free midsurfaces and physical directors by its own prescribed frame, retaining free deformation, then projects the declared controls. Every seed uses the existing actual whole-q-path certificate and owner-local deformation caps before material evaluation.

The new support fixture has source anchors1/4 and target anchor7 all six coordinates prescribed, target9/13/15 normal controls and target9 static uy support. It performs twelve5-degree common Y rotations to60degrees, normal press,20mm source-only globalY slide while the target anchor remains held, opening and recontact. Both bodies retain free bending coordinates. Initial physical clearance0.2um, materials/skins/fineQ1 law unchanged. This support tuple is new, not a reinterpretation of the previous common-frame example.

Scientific gates retain Fref=1e-4N, Mref=1e-4Nm, L1equilibrium and wrench<=1e-6, force complementarity<=1e-8, nonnegative z and50um dimensional gap. Opening additionally requires independent strictly positive physical separation and released forces. Independent posed binary original-Q1 skin bounds, projected footprint areas and target-seam material coordinates use no production overlap projection. Their area is the registered projected chart measure, not physical tilted surface area. Physical rim/corner admission remains open.

V1tolerance1e-10 completed all16solver increments but failed the independent L1equilibrium gate at sliding step14. Its recorded L2residual3.04266466780843e-11N matches the independently recomputed value; L1=1.3636101504831994e-10N exceeds the1e-10N gate. All15otherposes passed this equilibrium discriminator. Lead adopted exactly one numerical accuracy candidate1e-12, unchanged max18/physics/gates. Because tolerance is restart-bound, V2starts fresh and preserves every V1checkpoint/result.

The independent seed discriminator uses60degrees and proves source-only20mm transport with unchanged target skin and preserved owner-local coordinates. The inherited full spin/chart q-z directional-work discriminator exercises30degrees with shifted overlap; it is not a60degree accepted-pose tangent qualification. Skin/work/sweep mechanics are unchanged in this slice.

## Public usage

Run `python examples/general_contact_tilted_relative_sliding.py --through-step 4`, save its reported checkpoint, then pass `--restart checkpoint.json` with registered endpoints8,12,13,14,15,16. The final CLI check may use the terminal checkpoint and therefore perform zero new increments; the separate installed fresh-process chain supplies the actual solve evidence.

Default common-frame settings omit the new field from historical automatic/restart contracts. Current request identities bind the package and full settings and are not claimed unchanged across packages. Partial angular constraints, general mixed structural models, large local strain, friction, dynamics and arc length remain outside this finite profile. This is development evidence, not engineering acceptance or release; generic nonlinear hidden-state rollback is not qualified.

Raw evidence: `C:/ANYworkspaceWork/contact_tilted_relative_sliding_20261008`; exact final results/accounting are recorded in OUTCOME.md after closure.

Final public numerical controls: tolerance5e-12,max18. V2at1e-12 rejected firstpress at a measured roundoff/globalization floor; V3uses the independently checked89-coordinate stopping bound and passes the complete chain. Detailed results and retained failures are in OUTCOME.md. No tolerance-bound old checkpoint is migrated.
