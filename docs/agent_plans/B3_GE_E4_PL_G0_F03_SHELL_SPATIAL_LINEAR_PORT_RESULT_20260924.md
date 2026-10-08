# G0 F03 shell spatial reference-port diagnostic — 24 September 2026

Status: **bounded virgin linear diagnostic passed; G0B remains open.** No
formal scientific case, multiplier selection, installed-artifact comparison,
or G1 admission follows from this result.

The isolated integration branch adds a flat-reference six-channel shell
station trace on the existing four off-grid material samples. Three centroid
translation rows use Q4/S3 host interpolation. Two physical angular rows
average the independent shell director rotations `rx` and `ry`; the normal
angular row uses the centered in-plane proper-fit variation. The map has no
`rz` columns. A pure normal moment therefore pulls back to physical
in-plane nodal forces with zero resultant and the prescribed moment about
the material station. The director rows are independent of midsurface
slopes, preserving an admissible transverse-shear field.

A separate small diagnostic assembler gathers the actual Q4 and S3-V2D
`compute_stiffness_components(...)["physical"]` blocks with all six nodal
coordinates. It excludes PL/hourglass completion and does not presume that
the physical matrix is positive definite in drilling coordinates.

Executed with `C:\Python\Python314\python.exe` from this checkout:

- New shell spatial reference-port module: **10 passed**.
- New shell and native spatial port modules with the existing moment and
  nonaffine-trace diagnostics: **74 passed**.

The checks cover both Q4 and S3-V2D, off-grid stations, six rigid trace
fields, all six physical stiffness rigid null modes, exact in-plane
projection parity with the earlier F03 shell diagnostic, physical-block
symmetry, absent physical drilling columns, nonzero shear energy for a
director-independent slope, and isolated normal-torque balance.

An independent read-only mechanics review found no defect in this bounded
linear map. It requested the isolated normal-torque and full-matrix rigid
tests, which were added and passed. Its final closure result is recorded
with this diagnostic.

This code reconstructs a fresh flat virgin panel. It is not a finite
SO(3) shell-side pose, a nonlinear E4-PL trial evaluator, a shell/beam
relative-pose logarithm, a constraint Hessian, a line integral, or a
coupled KKT stability result. Those mechanics remain the next G0 work.
