"""Development zero-set certificate; not yet wired to material integration.

The caller supplies whole-material-rectangle enclosures of gap and its time
derivative on each slab. Sampling is not an enclosure. Every possible zero
must be transverse with the same orientation. Thus a continuously
differentiable point gap has at most one zero on the complete segment;
turning points strictly away from zero do not obstruct this implication.
"""
from dataclasses import dataclass
from math import isfinite

from .native_surface_support import SupportIntervalBudget


@dataclass(frozen=True)
class GapSlabEnclosure:
    gap_lower: float
    gap_upper: float
    derivative_lower: float
    derivative_upper: float

    def __post_init__(self):
        if (not all(isfinite(v) for v in (self.gap_lower,self.gap_upper,
                                         self.derivative_lower,self.derivative_upper))
                or self.gap_lower>self.gap_upper
                or self.derivative_lower>self.derivative_upper):
            raise ValueError('finite ordered whole-slab enclosures required')


def certify_single_crossing(enclose, *, budget):
    """Prove at most one crossing per material point, or return False.

    Bounds must include arithmetic error and the full spatial rectangle.
    The derivative is with respect to the original segment parameter, not
    a rescaled local time. Strict inequalities exclude unresolved tangencies.
    Every inspected slab consumes the caller's shared support budget.
    """
    if type(budget) is not SupportIntervalBudget:
        raise TypeError('exact shared support interval budget required')
    pending=[(0.,1.)];orientation=0
    while pending:
        if not budget.consume():
            return False
        left,right=pending.pop()
        bounds=enclose(left,right)
        if type(bounds) is not GapSlabEnclosure:
            raise TypeError('exact whole-slab enclosure required')
        if bounds.gap_lower>0. or bounds.gap_upper<0.:
            continue
        direction=(1 if bounds.derivative_lower>0. else
                   -1 if bounds.derivative_upper<0. else 0)
        if direction:
            if orientation and direction!=orientation:
                return False
            orientation=direction
            continue
        middle=(left+right)/2
        if not left<middle<right:
            return False
        pending.extend(((middle,right),(left,middle)))
    return True
