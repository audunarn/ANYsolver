# G0 F03 native spatial station-port diagnostic — 24 September 2026

Status: **bounded kinematic diagnostic passed; G0B remains open.** This is
not a formal scientific case, line multiplier selection, installed-artifact
qualification, or permission to enter G1.

The isolated integration branch adds a private six-channel station port over
the actual B3-GE retained generalized half-cell state. It evaluates the
position and material frame, maps a native trial increment to spatial
translation/rotation, pulls a physical wrench into retained coordinates, and
computes the station position/frame second variation in one spatial-left
chart. An explicit side selects the left or right half-cell at their common
node. The output position retains compensated high/low components. An exact
binary64 affine calculation in this bounded diagnostic avoids loss of a
sub-ULP station offset near a large origin.

The port validates each trial state against its frozen native context. It
does not require an issued accepted state, so it can be used on rejected
trial configurations. This diagnostic intentionally does not define the
shell-side six-channel pose, a relative-pose logarithmic constraint or its
curvature, a line integral, a multiplier space, or a coupled KKT system.

Executed with `C:\Python\Python314\python.exe` from this checkout:

- New station-port module: **10 passed**.
- New module together with existing moment, nonaffine-trace, and port-factory
  diagnostics: **72 passed**.

The tests include straight native planar-limit parity; curved and
pre-rotated reference frames; first and second derivatives through the
actual `Context.advance` operation; eccentric force/moment virtual work;
deformed one-sided frames; owned outputs; interior large-origin and sub-ULP
position pairs; and malformed trial-state rejection.

An independent read-only mechanics review found and then verified closure
of the large-origin interior interpolation issue. Its final review found no
new actionable issue and agreed with the restricted kinematic claim.

Next mechanics work is a six-channel shell-side trace with a physical
rotational contract, followed by relative-pose and line-constraint
derivatives, full coupled KKT and stability checks under the frozen F03
acceptance matrix. No one-use scientific registration or release action was
performed.
