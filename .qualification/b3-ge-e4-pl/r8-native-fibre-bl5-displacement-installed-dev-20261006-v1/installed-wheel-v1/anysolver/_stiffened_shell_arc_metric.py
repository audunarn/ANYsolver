"""Local physical chord metric, experimental and not programme-qualified.

Weights are explicit reference quadrature weights, frozen by the caller. No
nodal-count normalization or mass is inferred. This is a seminorm on the mixed
system: retained variables and multipliers still belong in equilibrium.
"""
from dataclasses import dataclass
import numpy as np
from ._ge_beam3_p5.algebra import skew


class ChordDomainError(ValueError):
    """A candidate leaves the local chord chart; malformed data is separate."""


def _owned(value):
    array = np.asarray(value, dtype=float)
    return np.frombuffer(array.tobytes(), dtype=float).reshape(array.shape)


@dataclass(frozen=True)
class PhysicalChordMetric:
    weights: np.ndarray
    length: float

    def __post_init__(self):
        weights = np.asarray(self.weights, dtype=float)
        if (weights.ndim != 1 or not weights.size or not np.isfinite(weights).all()
                or np.any(weights <= 0.) or not np.isfinite(self.length)
                or self.length <= 0.):
            raise ValueError("positive finite reference weights and length required")
        squared=float(self.length)*float(self.length)
        if not np.isfinite(squared) or squared<=0.:
            raise ValueError("representable squared metric length required")
        object.__setattr__(self, "weights", _owned(weights))
        object.__setattr__(self, "length", float(self.length))

    def evaluate(self, displacement, frames, reference_frames):
        """Value and translation/spatial-left-rotation gradients.

        Physical translation differences are supplied directly, avoiding the
        subtraction of two large absolute positions. Rotation chord is local:
        relative angles >= pi/2 are rejected rather than traversing its fold.
        """
        n = len(self.weights)
        u = np.asarray(displacement, dtype=float)
        current = np.asarray(frames, dtype=float)
        reference = np.asarray(reference_frames, dtype=float)
        if (u.shape != (n, 3) or current.shape != (n, 3, 3)
                or reference.shape != current.shape or not np.isfinite(u).all()):
            raise ValueError("complete finite physical nodal poses required")
        for rotations in (current, reference):
            if (not np.isfinite(rotations).all()
                    or np.max(np.abs(rotations.transpose(0, 2, 1) @ rotations - np.eye(3))) > 1e-10
                    or np.max(np.abs(np.linalg.det(rotations) - 1.)) > 1e-10):
                raise ValueError("proper physical rotation matrices required")
        relative = current @ reference.transpose(0, 2, 1)
        if np.any(np.trace(relative, axis1=1, axis2=2) <= 1.):
            raise ChordDomainError("local continuation rotation exceeds pi/2")
        difference = current - reference
        value = np.sum(self.weights * (
            np.sum((u / self.length)**2, axis=1)
            + .5*np.sum(difference*difference, axis=(1, 2))))
        translation = 2*self.weights[:, None]*u/self.length**2
        # d(3-tr(R R0.T)) / d spatial-left theta.
        spin = np.column_stack((relative[:, 2, 1]-relative[:, 1, 2],
                                relative[:, 0, 2]-relative[:, 2, 0],
                                relative[:, 1, 0]-relative[:, 0, 1]))
        return float(value), translation, self.weights[:, None]*spin

    def plane(self, displacement, frames, reference_frames, translations, spins):
        """Frozen physical tangent-plane value and actual spatial gradients.

        Caller supplies a unit tangent in this metric. Unlike squared distance,
        this signed projection has a nonzero row at the accepted predecessor.
        """
        self.evaluate(displacement,frames,reference_frames)  # same local domain
        translations=np.asarray(translations,dtype=float)
        spins=np.asarray(spins,dtype=float)
        if (translations.shape!=(len(self.weights),3) or spins.shape!=translations.shape
                or not np.isfinite(translations).all() or not np.isfinite(spins).all()):
            raise ValueError("finite physical tangent directions required")
        tangent=np.array([skew(v)@r for v,r in zip(spins,reference_frames)])
        value=np.sum(self.weights*(np.sum(displacement*translations,axis=1)/self.length**2
            +.5*np.sum((frames-reference_frames)*tangent,axis=(1,2))))
        product=frames@tangent.transpose(0,2,1)
        gradient=-.5*np.column_stack((product[:,2,1]-product[:,1,2],
            product[:,0,2]-product[:,2,0],product[:,1,0]-product[:,0,1]))
        return float(value),self.weights[:,None]*translations/self.length**2,self.weights[:,None]*gradient
