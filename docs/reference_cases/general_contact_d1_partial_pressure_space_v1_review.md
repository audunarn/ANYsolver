# Fixed-pose Q4/S3 partial-pressure-space review

The [registration](general_contact_d1_partial_pressure_space_v1.json)
(SHA256 `7217dad25d6b592ff8fd7e446b7b5a6830b57ade2200aac4239fcc9c5909f906`)
was committed before the one formal run. It binds the probe and pressure-space
source blobs at `4becd969`, three retained development predictor hashes and
the independent local-plane force reference. The source commit is an ancestor
of the execution branch; the listed blobs match.

The [raw report](../../reports/general_contact_d1_partial_pressure_space_v1_formal_20260927.json)
(SHA256 `41572b8c5a73fef6766cd12fafc4df54b2b80546c347b7917f91a3bdc319df1e`)
contains the one 16/32/64-division, four-row run, elapsed 99.869 s under
the 180 s limit. The [verdict](../../reports/general_contact_d1_partial_pressure_space_v1_verdict_20260927.json)
(SHA256 `a2ef56f6e453c5b8efeb58f87ee61cb67f903ecb2c61b5c13c9ee926e0b7d84f`)
passed all frozen predicates.

Independent read-only review recomputed the positive-part affine penetration
integral over x=[0.24,0.77] m and y=[0.21,0.73] m. Its local-plane reference
is 0.17225 N. The observed forces at 16/32/64 divisions were
0.1697613976/0.1717734850/0.1721806932 N, with strictly decreasing
absolute errors 0.00248860/0.000476515/0.0000693068 N. The finest relative
error is 0.040236%. The scaled Gram rank equals the supported pressure-mode
count at each resolution: 44/44, 76/76 and 144/144. Active modes increase
24/40/72. Source and target forces and moments balance to about 1e−17 in
their respective units. The finest integration indicator is 7.698e−15 N,
1.11e−10 of the finest reference error, below the registered 0.1 fraction.

The reviewer **accepted only fixed-pose planar Q4/S3 partial-contact
pressure-space rank and integrated-force resolution** for this case.
Development predictor equality is deterministic replay; the independent
force check is the local-plane integral, whose finite-slope projection
assumption makes it an approximation. Refinement changes x divisions while
four rows remain fixed. Full rank applies to supported modes, not every
source node. The raw JSON does not independently attest the source process
or one-use count; the run was owner-supervised. Coupled equilibrium, tangent,
other geometries and general C1 remain open.
