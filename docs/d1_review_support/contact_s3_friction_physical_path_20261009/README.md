# Physical-side S3 material friction path

Development candidate: a translating source and an elastic target deforming in plane. Target normal motion and rotations are constrained. This is not target bending, varying-normal friction, partial coverage or engineering acceptance.

The existing normal owner supplies the fixed reference material atlas. Its material node positions and work rows are checked against friction's adapters. Independently declared source/target director and winding reversals preserve physical sides; material IDs, first-touch sign and physical force couples are tested for all four combinations.

The new combination (`physical_sides_dev`, `control_projection_dev`, exact `S3SlidingFrictionSettings`, refined S3 projected penalty) admits only a certified fixed axis-aligned target plane. Exact rational interval coefficients enclose sparse corner and stored dense material-point maps, interpolation rounding and underflow floors. Strict positive quadratic Bernstein controls prove full source-triangle coverage over the entire candidate segment. The actual rounded target normal is bounded and remains along the fixed axis. Unresolved, oblique, normally translating and varying-normal paths refuse conservatively. Legacy adapter construction and restart bytes remain unchanged.

## Example

Run the installed package with the source example:

```powershell
python examples/general_contact_s3_friction_physical_path.py --output result.json
```

Seven increments: press, stick, .39 m slide across target facets, reverse stick, reverse slip, open and stress-free recontact. Both source translations are declared ties; target right-edge ux is solved. Normal stiffness1000 Pa/m, mu=.3, tangential stiffness1000 Pa/m, registered gap50um, solver tolerance1e-12. Scientific equilibrium/wrench1e-6 use separate .02 N/.02 Nm scales; directional tangent1e-5. Dissipation sign and endpoint return/storage accounting use1e-12 J. Endpoint contractions are not integrated path work.

Initial y=(.2,.6) had an exact seam-tie zero-area normal pair and was refused by the existing derivative domain. The separately adopted V2 y=(.19,.59) avoids that tie. The old failure remains evidence; no seam-tie capability is claimed.

## Evidence and scope

Raw evidence: `C:/ANYworkspaceWork/contact_s3_friction_physical_path_20261009`. Each guarded job preserves command, source inputs, immutable wheel identity, private imports/runtime, process-tree wall/RSS, stdout/stderr, JUnit and attempt-local machine output. The one private635-payload wheel is3c8e13f8a5c1994b3eaed15a4fb2d07b11c7d77a5fe963ef9a3776c6b5c86095.

Full V2 accepted poses1..7 pass independent binary-plane gap, recovered constrained equilibrium, complete normal-plus-friction wrench and actual target work. Four-polarity unit proof is distinct from the public default-polarity lifecycle. Active/open fresh restarts and actual public interruption/refusal checks are recorded in the final outcome; see OUTCOME.md for their completed status.

No pressure/spatial stability, general swept friction, finite rotation, generic material-trial rollback or release claim follows. Wider oblique/varying-normal target friction is the next geometric dependency.
