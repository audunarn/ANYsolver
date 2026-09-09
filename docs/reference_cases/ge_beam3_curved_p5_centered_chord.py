"""Opt-in algebraically equivalent chord-strain evaluation; author research.

U^T d - d0 = (U^T-I)d0 + U^T(d-d0). All operations remain in Jet2,
so first/second derivatives come from the same discrete potential. No
rounding-error bound, assembly convergence or qualification is claimed.
"""

from anysolver._ge_beam3_mixed_ad import Jet2, matvec, transpose
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import NonlinearMixedBeamProbe
from docs.reference_cases.ge_beam3_curved_p5_force_accurate_assembly import ForceAccurateAssemblyHistoryProbe


SCHEMA = 'GE_BEAM3_P5_ASSEMBLY_CENTERED_CHORD_FORCE_ACCURACY_V1'


class CenteredChordMixedProbe(NonlinearMixedBeamProbe):
    def _chord_strain(self, made_u, chord, left, right):
        size = chord[0].gradient.size
        reference = [Jet2.constant(self.reference.coordinates[right, i]-self.reference.coordinates[left, i], size)
                     for i in range(3)]
        u_t = transpose(made_u)
        difference = [[u_t[i][j]-(1 if i == j else 0) for j in range(3)] for i in range(3)]
        rotated_reference_change = matvec(difference, reference)
        rotated_chord_change = matvec(u_t, [chord[i]-reference[i] for i in range(3)])
        return [rotated_reference_change[i]+rotated_chord_change[i] for i in range(3)]


class CenteredChordAssemblyHistoryProbe(ForceAccurateAssemblyHistoryProbe):
    _mixed_type = CenteredChordMixedProbe
    _accuracy_schema = SCHEMA
