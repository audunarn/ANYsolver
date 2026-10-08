# Overlap-local swept Q4/S3 bound — review brief

**Status:** Development derivation for the explicit `overlap_local_dev`
certificate. It is not independently accepted and is not a general
continuous-collision claim. Source at this brief: `fdc35c8f`. The kernel is
[`q4_overlap_local_bound.py`](../../src/anysolver/general_contact/q4_overlap_local_bound.py).

## Admitted kinematics and construction

The D1 von Karman contact map gives an affine path in physical nodal
positions between two trial poses. The Q4 surface is bilinear in its two
parameters; each S3 target is the convex hull of three moving vertices.
For each Q4/S3 pair, the kernel partitions the Q4 parameter square into a
fixed depth-three set of subrectangles. It uses one frame from the Q4's
start projection normal and one fixed axis from the target's start normal.

For a subrectangle and any time on the linear nodal path, each source point
is a bilinear combination of its four subrectangle corners and each point
on the S3 triangle is a nonnegative barycentric combination of its moving
vertices. For the fixed axis, the separation is therefore bounded below by
the minimum of every source-corner/target-vertex separation at both path
endpoints. Moving target normals do not enter this extremum argument.

The projected source and target boxes in the fixed frame enclose their
endpoint vertices. The Q4 parent-normal quadratic Bernstein controls bound
the lateral drift of the matching source-to-target projection. A
subrectangle is pruned only when the boxes remain disjoint after that drift
and a floating-point margin. Otherwise its fixed-axis separation is retained.
The fallback for an unresolved orientation cone is the existing whole-pair
conservative swept bound, rather than an omitted pair.

Where the parent projection normal and the physical varying Q4 normal have
the required positive cones, let `q` be the fixed-axis separation of a
matched pair. The physical normal gap is

    g = q * (n_physical · n_projection) / (axis · n_projection).

The numerator ratio is nonnegative and at most one for unit normals. The
computed cone lower bound `c` is no greater than
`axis · n_projection`. For negative `q`, `min(0,q_min/c)` is consequently a
lower bound for the physical gap; the kernel subtracts a scale-dependent
roundoff margin. The contact manager also checks whole-face orientation and
its unchanged dimensional gap budget along the same trial path.

## Evidence and outstanding review points

The six original focused local tests cover partial overlap, disjoint faces, moving
planar faces, a midpath crossing with open endpoints, sampled warped moving
faces, and restart identity. A later focused test adds path reversal and
common rigid transformation controls. Another reconstructs the saved
eight-S3 manager and confirms old-path rejection, new-path admission,
D1 coverage and an independent endpoint gap under the declared limit. A
saved second-step proposal rejected by the
older projected-matching bound passed the explicit local bound at full
length: endpoint certificate −37.08 µm and an independently reconstructed
endpoint gap −14.26 µm against the unchanged −50 µm limit. The corresponding
two-step coupled route completed and matched a same-mesh independent linear
KKT reference in integrated force within 5.16e−5 relative.

An independent mechanics review should check the lateral-drift inequality,
the orientation-cone conversion above, the whole-pair fallback and the
roundoff margin against the actual varying-frame Q4 contract. It should also
check path reversal, near-grazing and nonuniform director motion within the
admitted small-rotation map. Numerical samples are controls, not a proof of
conservatism. Promotion additionally requires one-sided branch checks and
accepted-path/restart evidence; the existing local and coupled runs do not
establish these claims.

Raw controls: [saved rejected proposal](d1_target8s3_swept_capture_20260929.json),
[full replay](d1_target8s3_swept_full_replay_20260929.json),
[coupled result](d1_coupled_target8s3_bump_overlap_20260929.json),
[oracle comparison](d1_target8s3_overlap_comparison_20260929.json),
[path reversal test](d1_overlap_path_symmetry_20260929.log), and
[saved-path regression](d1_overlap_saved_eight_s3_path_20260929.log).
