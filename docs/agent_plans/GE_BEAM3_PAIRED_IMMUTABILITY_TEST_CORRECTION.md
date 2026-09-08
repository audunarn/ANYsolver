# Correct the immutable-storage mutation harness

Base d5141c3777e887d3bac7134d354efe50b7aab8eb, tree
41daee19c90924813bdc1d85cf06a935fbdb0871. Preserve the failed rehearsal,
not an accepted qualification: local32tests had31passes and one harness
failure; old dense17 and prestress3 all passed and their raw scientific
records are byte-identical to the bound40e5d22 archive.

The result uses genuinely immutable backing storage. Attempting to turn on
WRITEABLE already raises ValueError, before the test's expected guard call.
Correct only that test: first require this rejection, then use an equal-valued
writable copy to test the explicit result ownership guard. Both checks must
pass. No private kernel, arithmetic, material, mechanics or tolerance change.

Three-path correction: test, this plan and initial canonical status. Bind the
9720-byte external archive manifest
CB3F39FEEEE0E5CC8BD8BA559391CD65B6CA3DCFD4795DE5B2BBCE9E415AC832,
audit81110042B7AA17C9847876AF73CC17B955B22FD443D3E770222D162410172763.
Original test failure and all raw runs remain immutable. No slenderness
lane or repeat cycle was launched after the failure.

Freeze then run corrected writable witness once, full32-node local once,
then each of the three4-specimen/all12-root slenderness nodes once. Compare
the31 previous passing local records byte-for-byte. Previously passing
old-route regressions remain bound through unchanged implementation hashes;
do not label them rerun at the correction commit. No automatic retries.
Inherited one-thread/24GiB/600second/120second-inactivity/three-worker and
1800second-wave controls unchanged. Only successful complete rehearsal
permits the later continuum regression and fresh deterministic repeats.
Full programme active. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
