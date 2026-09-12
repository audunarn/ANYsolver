# Shared SO(3) elementary evaluation diagnosis, not a source correction

The 8132e745333e572b07e2dd56b9df9c1ca1527270 component diagnostic completed
one nonclassifying node in 18.444574200024363 seconds, peak 238624768 bytes,
exit zero and zero remaining children. Temp directory:
anysolver-g3c-owner-development-xvv9p4q1; lease SHA-256
c0ce8eaf3b672f2d11f7e46737f1e5313345ece7108609c80e29c820e1c96428.
It preserves/reproduces the failed d90aa3e full gate, not supersedes it.

At h=1e-6 the normalized directional errors are full 2.767173042642239e-7,
native 2 2.9864946731594166e-7, B2 1.7317289852897585e-7, and combined
supports/joints 5.369425301511977e-6. Native Schur reconstruction differences
are exactly zero; centre internal errors are 1.3161592062157365e-17 and
3.5194111673146195e-17. No threshold, fixture or source formula has changed.

Freeze one additional nonclassifying elementary diagnostic node. Compare actual
shared Log/Exp scalar coefficients and their first two derivatives against
90-digit Decimal series on a fixed small-angle grid. For F(c)=acos(c)/sqrt(1-c*c),
use delta=1-c and a_0=1, a_n=n*a_(n-1)/(2*n+1), with derivative signs from
d/dc=-d/ddelta. Use independent factorial series for sin(sqrt(x))/sqrt(x)
and (1-cos(sqrt(x)))/x. Require 40/60-term binary64 reference agreement.
Report all discrepancies without changing production dispatch. Also report the
exact local identity Log(Exp(v))=v and its analytic first/second derivatives.
These diagnostics are not a new mechanics proof or an accepted replacement.

Command: C:/Python/Python314/python.exe -I -S -B
scripts/run_ge_beam3_g3c_owner_bridge.py --elementary-diagnostic.
Same source/environment lease and limits: one thread, 600 seconds, 24 GiB/tree,
120-second inactivity, fresh exclusive directory, no retry. Exactly one node,
separate from previous diagnostic, smoke and full-development inventories.

The accepted contract freezes the shared source. Do not edit that source or
silently rebind its hash. Any confirmed elementary-evaluation repair requires
a reviewed successor authority, preserving earlier evidence, all scientific
thresholds and mechanics definitions. Formal G3c remains blocked; restart,
remaining graph coverage, recovery and later parity obligations remain open.
