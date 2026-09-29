# Independent read-only code and mechanics review

Reviewer: /root/s3_algorithmic_review, separate from the implementation owner.
Reviewed solver product: 0da6cd12b755ab78b9634e2a4b5b880058f2e457.
Reviewed ANYfem product: b0185b4cab261cfe35327c5ae9d959af88984789.
The consumer test subsequently added public solve/checkpoint/restore execution;
consumer product was unchanged. Reviewer ran no numerical jobs.

No actionable correctness findings in the selected Q4 map and owner integration:
full fixed-predecessor pullback and chart curvature; consistent reference/finite
selection; owned definition; nondefault-only model identity; checkpoint binding;
strict ANYfem v3 selection with compatible historical v1/v2 layouts.

The reviewer identified the remaining F05 acceptance gap: local Q4/S3 smooth
plastic derivatives do not establish the selected mixed owner derivative with
actively updating S3 plasticity. The existing historical mixed derivative and
all-S3 elastic-shell derivative do not supply that evidence. One-sided yield
limits also remain missing. Check the selected assembled active-plastic tangent
from frozen predecessors, branch masks, shell/beam/constraint blocks and nonzero
multiplier curvature, then the local one-sided yield branches. Bind reused and
new checks in the existing concise Level B acceptance contract and independently
adjudicate; no pass is declared here. The consumed historical Q4-v1 diagnostic
must not be replayed. There is no separate unconsumed F05 acceptance authority
recorded; formal F03 authority is unrelated and remains unconsumed.

Downstream G3 material breadth/dissipation and F06 large noncommuting histories
and partial support laws remain open. This review does not accept F05/F06/G0B.
