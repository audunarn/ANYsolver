# Supporting source scrutiny — matched S3 overlap

Read-only owned OpenAI reviewer `s3_overlap_gap_contract_review`; same model family,
not independent engineering acceptance. No reviewer edits, numerical runs or Git actions.

The reviewer found no soundness counterexample in conservative closed clipping,
whole-path endpoint openness cuts, original-polarity checks or driver commit ordering.
Both `minimum_gap` and its decision gate are replaced together while production
work remains unchanged. Endpoint, strong path and weak phase checks precede commit.

The upper gap component is a penetration witness only for exact constant-endpoint
clipping. Outer swept polygon vertices may never belong to actual overlap. Current
code uses it for endpoint rejection only. This restriction remains binding.

Final reference scrutiny found no further projected-work, physical reference-area or
mass-ordering discrepancy. Its first finding concerned an intermediate default-KN
trajectory selector; before the K launch the candidate explicitly passed KN2e10 to
both owner definition and independent reference, and recorded that setting. Earlier
KN1e9 failures remain historical. The independent reference-area omission for N>1
was corrected separately; flat overlap area is checked at N1/N2/N8.

Limits retained: the independent preflight checks time-step endpoint gaps; production
must still prove its complete Hermite paths. The reference replays production's
accepted time grid and therefore does not independently validate event selection or
localization times. Structural stiffness is production input. Numerical agreement
does not establish temporal/spatial accuracy, unrestricted impact, or C0–C9 acceptance.
