# ANYsolver 0.4.6: bounded ecosystem compatibility release

ANYsolver 0.4.6 widens the supported mesher line to `ANYmesher>=0.4,<0.6`
and raises the file-I/O floor to `ANYfileio>=0.3.2,<0.4`. The bounded gate
uses production ANYmaterial 0.2.0, ANYgeometry 0.4.3, ANYmesher 0.5.0, and
ANYfileio 0.3.2 artifacts.

The release changes dependency metadata and compatibility evidence only.
Solver mechanics, B3-GE explicit opt-in behavior, the legacy B3 default, and
qualified Q4/S3 mechanics and defaults are unchanged.

The gate validates the immutable B3-GE G7 evidence, exact installed package
identities, source and wheel runtime equality, dependency resolution, neutral
meshing and file-I/O public contracts, licensing, selector boundaries, and
the trimmed source archive. It does not rerun scientific qualification.

Terminal on success:

`PROVISIONAL_GO_ANYSOLVER_0_4_6_BOUNDED_COMPATIBILITY_RELEASE`

This terminal authorizes a separate publication decision for the exact 0.4.6
artifacts; it does not publish them automatically.
