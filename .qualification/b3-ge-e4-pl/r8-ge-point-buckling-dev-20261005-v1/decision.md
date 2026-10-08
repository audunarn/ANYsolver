Decision: deliver conservative accepted-state mixedGE/Q4 point buckling, a missing
G4B behavior; this is development, not complete programme acceptance.
Adopted potential: objectiveQ4 energy + sum(pT k - V*) + muT c - deadtranslationwork.
Retain full42/member (24kinematic/18resultants), pointmultipliers and sparsepatterns.
Beam Km=[[0,BT],[B,-S]], Ggeo=[[G,0],[0,0]], both high/low Hessian parts.
Q4 Km=DT km D; G=DT kg D+sum(f Hess d); qualifiedlinear correction is material,
while correctedforce also contributes mapcurvature. Use localcomponent seam,
not spatial-return split. Pointmixed-chart tangent needs +.5skew(rbeamrotation)
on zero-leftExp beam block; charted shell derivative already supplied.
Pencil A-lambdaB, B=-embeddedG; lambda1 reconstructs acceptedconservativeH.
Lambda frozenprestress/curvature scale, not recomputed loadpath/limitload.
Admission: objectiveelasticQ4, elasticinteriorgeneralizedGE, sixposepoints,
conservative nodaltranslation, simplefixedtranslations/fullfixedrotationtriples.
Historicalcorotational equivalence/otherprofiles/loads/materials/attachments remain
explicit pending programme obligations; do not qualify them through this slice.
Discriminator: bounded independent fullmixed denseassembly, actualupdatecovector
FD at nonzero mu, reconstruction/skew/supportrestriction, immutablehistory,
finitepencil eigen/constraint residuals, tension/compression/negativeadmission.
Failure: repair concrete derivative/split/ownership error, do not average tangent,
regularize with inventedmass, assumeSPD or return guessedpairs. No automatic
refinement/campaign expansion. Accurate finitepairs alone not lowestinstability.
Independent supporting OpenAIRead found contract implementable with above chart
correction; not required different-model-family acceptance.
Resources onejob600s/2GiB tree/affinity1/pools1/JIToff. Root owns numericallaunch.
No formalF03/G3c/protectedcanary/closedcampaign/main/push/publication authority.
Source parent20a09c21; owner /root/restricted_nonlinear_reference assigned connected
operator/capture/publicroute/tests/docs. Astra review/integration/final acceptance.
