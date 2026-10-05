"""Precise scalar angular coordinates for the existing material normal work.

The gap is an affine axial field plus a circular sinusoid. Decimal arithmetic
keeps its value and angular partition consistent when the axial slope is tiny.
Jet2 still supplies all work derivatives; this is no new differentiation engine.
Angles are confined to the surface rule's [0, 2*pi] range. All loops are bounded.
"""
from decimal import Decimal, localcontext
from math import acos, atan2, pi


PRECISION = 50


def _sincos(angle):
    """Taylor evaluation on the admitted bounded angle range, at 50 digits.

    At |angle| <= 2*pi, the omitted term after 80 pairs is below 1e-150.
    Decimal roundoff dominates that remainder; finite precision is still
    checked by the root and interval admission, rather than claiming exactness.
    """
    x = Decimal(angle)
    sine = sine_term = x
    cosine = cosine_term = Decimal(1)
    square = -x*x
    for k in range(1, 81):
        sine_term *= square/Decimal(2*k*(2*k+1))
        cosine_term *= square/Decimal((2*k-1)*2*k)
        sine += sine_term
        cosine += cosine_term
    return sine, cosine


class PreciseNormalAngles:
    def __init__(self, offset, slope, width, cosine, sine):
        self.offset, self.cosine, self.sine = map(Decimal, (offset, cosine, sine))
        with localcontext() as ctx:
            ctx.prec = PRECISION
            self.axial_change = Decimal(width)*Decimal(slope)

    def value(self, angle):
        with localcontext() as ctx:
            ctx.prec = PRECISION
            sine, cosine = _sincos(angle)
            return self.offset+self.cosine*cosine+self.sine*sine

    def endpoint_values(self, angle):
        with localcontext() as ctx:
            ctx.prec = PRECISION
            first = self.value(angle)
            return float(first), float(first+self.axial_change)

    def breakpoints(self, lower, upper):
        with localcontext() as ctx:
            ctx.prec = PRECISION
            lo, hi = Decimal(lower), Decimal(upper)
            points = {lo, hi}
            amplitude = (self.cosine*self.cosine+self.sine*self.sine).sqrt()
            if not amplitude:
                return sorted(points)
            phase = atan2(float(self.sine), float(self.cosine))
            for k in range(-2, 5):
                angle = Decimal(phase+k*pi)
                if lo < angle < hi:
                    points.add(angle)
            roots = {}
            offsets = ((self.offset, self.offset+self.axial_change) if self.axial_change
                       else (self.offset,))
            for offset in offsets:
                ratio = -offset/amplitude
                if not -1 <= ratio <= 1:
                    continue
                root = acos(float(ratio))
                for sign in (-1., 1.):
                    for k in range(-2, 4):
                        angle = Decimal(phase+sign*root+2*k*pi)
                        if not lo < angle < hi:
                            continue
                        if self.axial_change and self.offset+self.axial_change == +self.offset:
                            raise ValueError('material plane angular axial separation unresolved')
                        for _ in range(12):
                            sine, cosine = _sincos(angle)
                            derivative = -self.cosine*sine+self.sine*cosine
                            if not derivative:
                                raise ValueError('material plane angular root is unresolved; grazing excluded')
                            change = (offset+self.cosine*cosine+self.sine*sine)/derivative
                            angle -= change
                            if abs(change) <= Decimal('1e-40'):
                                break
                        else:
                            raise ValueError('material plane angular root precision exhausted')
                        if not lo < angle < hi:
                            raise ValueError('material plane angular root ownership unresolved')
                        # Distinct endpoint equations may describe a very thin
                        # partial-contact arc. Never silently merge that arc.
                        if angle in roots and roots[angle] != offset:
                            raise ValueError('material plane angular root separation unresolved')
                        roots[angle] = offset
                        points.add(angle)
            return sorted(points)
