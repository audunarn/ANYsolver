# Saved density work analysis supporting Read review V1

No consequential algebraic or channel-indexing defect found. Read-only source/record/hash review; no import, numerical job, solve or test performed. The previous V2 physical review remains unchanged.

Let p/q be fine-parent/coarse-child configurations, lp/lq their multipliers, f the identical load, and rp=Kp+Cf.T lp-f, rq=Kq+Cc.T lq-f. The exact algebraic identity is

    (q-p).T f = lp.T Cf q + q.T Kp - p.T Kq - lq.T Cc p - q.T rp + p.T rq.

Analysis lines47-54 implement every term with these signs. No symmetry of saved K, exact equilibrium or zero fixed reactions is silently assumed. Both saved configurations have the unchanged homogeneous fixed restrictions, so full residual work includes reactions consistently. The 5x8 reshape at49 agrees with fine channel-major rows: five channels, four supports, constant/slope pairs. The reported translation_y term is the local flat-reference y channel, which equals the global lateral channel in this bound identity-frame fixture.

Observed signed work difference2.2935217289381777e-6J reconstructs as2.2935217289381713e-6J, scaled mismatch3.212503738916803e-16. Parent lateral multiplier work on the child's fine gaps is2.2888923935242343e-6J, much larger than each other signed channel term. Cross-skew1.836367429647323e-18J, residual work-1.8684095078315145e-18J and child-on-parent coarse gap work2.0651888786822463e-20J are explicitly retained.

The restricted conclusion is supported: the lateral parent multiplier work dominates this signed difference between these two saved solutions. Prefer this precise wording to an assertion that individual fine multiplier modes have been uniquely classified as removed. Mathematically, coarse-range multiplier additions E.T a do no work on an exactly coarse-compatible q; thus attribution concerns fine action modulo that coarse range. It does not give a channel stiffness, energy partition, causal decomposition of independent uncoupled mechanics, or permission to tune one channel. No positivity, law selection, accuracy, beam-discretization exclusion or uniform qualification follows.

The profile outputs at58-64 are linearized local gap samples at the existing128 quadrature stations and measure-weighted RMS summaries. Their names 'continuous_station_gap' do not certify globally continuous trace fields or a registered norm. Translation components have length units; director components are dimensionless, so their raw maxima/RMS must not be compared as a common physical norm.

All four prepared/control hash pins match current files and the reviewed V2 pairs. Source SHA736358db41e150f3e3d96d137e9f806334244ea2296e321022f6930b521a094f; analysis JSON SHA29bc0de1c241d40fe001f90bd3e7248e7fd8f05f759e4c1c341fe83ac77d9ed2. Terminal execution exit0,0.4377051s,53,055,488 sampled bytes/max1, affinity[0], effective pool1; solve_count0 and source contains no factorization/solve. This is saved-array attribution, not a new physical campaign or scientific acceptance.