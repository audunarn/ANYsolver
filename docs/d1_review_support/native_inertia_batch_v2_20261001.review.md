# Batched finite-inertia V2 independent review

**Scoped local PASS. No consequential blocker to lead wiring for a separately verified integrated route.** The new kernel remains `9ee021df59f5974092e94a002ed6da8b8143e0a9ed891982992a60e50d194682`; existing owners/dispatch/native timesteps were unchanged by this case. [V1 source review and literal NONPASS](native_inertia_batch_v1_20261001.review.md) remain intact.

## Corrected named zero comparison

[Test](native_inertia_batch_v2_20261001.test.source.py):107–142 requires the literal isotropic translational section block, skew centroid crossblock and transposed lower block, uniform nodal translation, zero angular velocity and all zero acceleration before issuing outputs or the exemption. Fixed positive scales are L=2 m, m=5.78128833265066 kg, V=0.6213694553162393 m/s, Omega_ref=V/L, with denominator m L² Omega_ref=7.18463196457054 kg m²/s. Dq assigns L to nine translational coordinates and 1 to rotational coordinates. Thus Dq.T dv Dq has consistent work derivative units, avoiding separate force/couple unit mixing. Scalar norm, batch norm and their difference must each satisfy the original 1e-13 bound for this analytic-zero case only; all resolved relative gates remain unchanged.

Independent stdlib recomputation from the saved arrays gives dimensionless scalar 2.497334517166942e-17, batch 2.4970217657046832e-17 and difference 6.529171490485728e-19. The exact section assumptions and mass/scale construction also reconcile. Three previously passing V1 cases are reused byte-equivalent in the saved payload with identical prepared inputs and fixture states, not reevaluated or regraded. V1 itself remains NONPASS.

## Previously unissued checks and identities

Literal independent station virtual work contracts spatial/body balance before generalized assembly, without candidate derivative arrays: -255.956115921563 versus -255.95611592156294, relative 2.220826748215992e-16. Candidate residual finite differences are compared with the unchanged scalar analytic derivatives, at intervals 1e-5 and 2e-6. Velocity relative errors are 7.2826300135175714e-9 / 2.67962717475998e-8; configuration errors 6.049466701912904e-11 / 7.603095257471652e-10, below unchanged 1e-5. The raw saves these error metrics rather than each perturbed response array; source and successful selected test establish their execution. Read-only outputs, exact 42-coordinate algebraic zeros, momentum/energy mass identities and four rejection controls (negative measure, nonpositive section, improper frame, nonfinite velocity) complete. XML reports one test, zero errors/failures/skips.

Frozen test SHA `272374dcbbc1095de95469b8d0445d69b8c6560e1cd920c19988fb1430e30d00`; [input](native_inertia_batch_v2_20261001.inputs.json) `ee5d4873b1f8a2b9332d3cd9f7302ea3629e1f6fe4a17dce6590fc3039b6d633`; [raw](native_inertia_batch_v2_20261001.raw.json) `73c9294674103aa801272b769257c66615cae05b15535e2eb800b73cb804065a`; resource `dc63db00b7ce46ac95231f62f97a080c0c0195843e2f1ec401972889a2e19f63`; summary `8ceb2d575e172577856f5091f07d4d9e7bf1758c81874b63a4895a9c549d33b6`. All 452 actual source hashes and postverification flags match; effective environment and criteria equal the input. Exit 0, completed 4.8242886 s / 197.033984 MB within 180 s / 1 GiB, zero physical timesteps.

## Timing and handoff limits

The declared scalar/batch/batch/scalar kernel calls are 0.3069096000 / 0.0465151000 / 0.0438311000 / 0.3132358000 s. Recomputed means are 0.3100727000 versus 0.0451731000 s, ratio 6.86410054. This measures one prepared 48-station kernel pose; preparation, complete owner operations, package guards and native route costs are outside the comparison. It establishes no whole-trajectory savings, affordability, temporal/spatial accuracy, C7 qualification or release. Integrated owner/work/state/cost parity remains the next affected boundary.

Review used source and saved stdlib arithmetic/hashes only. No candidate imports, kernel evaluations, tests or numerical rerun were performed.
