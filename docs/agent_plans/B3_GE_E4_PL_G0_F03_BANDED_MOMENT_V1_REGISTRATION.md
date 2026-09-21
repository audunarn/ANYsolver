# F03 shell-port moment application: banded/diagonal parity registration

22 September 2026. **Exploratory G0B implementation check, not F03
acceptance.** The independently reviewed planar shell-port lifting
bound specifies rooted P1 translation moments and P0 retained yaw
moments. The existing v1 executable verified the mathematical
moments with a bounded dense solve. This v1 component compares an
explicit banded/diagonal application against that sealed dense oracle.
Freeze source and registration at a clean integration commit and
obtain independent mechanics/code review before a one-time run.

For each existing Q4/S3-V2D mesh `(Nb,Ns)=(4,4),(8,8),(16,16),
(8,1),(8,64)`, build the same supported two shell ports, actual
native translation and retained yaw columns, overlay R, and K4 or
local-dual row F as the frozen predecessor. The augmented system
contains three `Nb` moment blocks and two physical root equations.
Solve the 2×2 root port first; subtract its *actual induced yaw and
translation moments*. Apply the K4 tridiagonal rooted P1 mass solve
or local-dual diagonal solve separately to x/y, then the diagonal
native P0 yaw cell-average solve. Do not zero the physical shell-port
yaw, impose a tip restraint, or change any test row.

Check the assembled block against the independent dense `D`:
off-block entries ≤`1e−12` relative, translation bandwidth ≤1 for
K4 and 0 for local dual, yaw bandwidth 0, positive pivots, and root
translation identity. For every physical and retained input column
in the bounded ten cases, require the **maximum per-column** banded
coefficient and trace error to agree with the dense oracle
≤`1e−10`, normalized by
`max(reference column norm,1e−6×maximum reference column norm)`.
This floor makes a true zero column auditable without division by
roundoff. Require moment,
root and idempotence residuals ≤`1e−9`. Report matrix dimensions,
input count, **explicit band/diagonal arrays and RHS bytes**, and
solve work. `solve_banded` uses internal LU/pivot workspace not
included in these explicit-array counts; sampled RSS covers process
memory. This is a dense
*verification* oracle only; a production apply must stream vectors
without materializing a full projection matrix.

Separately run pure algebraic uniform rooted P1 and P0 moment systems
for `Nb=64,256,1024,4096,16384`, both K4 and local dual, with
deterministic smooth-plus-alternating RHS. Construct only diagonal
and adjacent arrays, verify residual ≤`1e−11` relative and report
explicit arrays/RHS sizes and elapsed work. No native element
or physical-response claim follows from these synthetic sizes.

One serial supervisor, one BLAS/Numba thread, sampled child RSS
≤8 GiB, 900 s/case, 7,200 s total. Pin previous shell-port raw
manifest/records and exact inherited source bytes, package/import
identities, all 15 case definitions, stdout/stderr, resource and
failure records under a new exclusive root. Preserve failed cases;
do not reinterpret one as a passing rerun. Require independent
post-run audit. A passing result proves an O(Nb)-storage/work
*application of this planar moment system*, not a fixed-stencil
inverse, signed KKT stability, six-channel mechanics, or a loaded
physical reference. F03/G0B and G1 gates remain unchanged.
