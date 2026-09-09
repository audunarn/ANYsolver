"""Straight elastic prestress diagnostic using the unchanged mixed potential.

The exact homogeneous compressed configuration is supplied analytically; no
failed postcritical seed or local Newton solve is retried. Global loss of
stiffness and local stationary-block failure have distinct diagnostics.
"""

from dataclasses import dataclass

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_continuum_probe import parabolic_references
from docs.reference_cases.ge_beam3_curved_p5_section_probe import DirectedHardeningSectionProbe
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import NonlinearMixedBeamProbe
from docs.reference_cases.ge_beam3_curved_p5_postcritical_reference import critical_load


class PrestressError(RuntimeError):
    """Unresolved local/equilibrium/critical-load diagnostic, not a NO-GO claim."""


@dataclass(frozen=True)
class PrestressRecord:
    elements: int
    load: float
    equilibrium_error: float
    local_residual: float
    minimum_moment_block: float
    minimum_rotation_block: float
    tangent: np.ndarray
    free: np.ndarray


def evaluate(count, load, *, axial=1000., shear=400., bending=1., order=8):
    """L=2, material y bending=EI, other bending/torsion=2*EI.

    Positive load means compression. Negative load is tension. Only the existing
    straight parabolic-family builder and diagonal elastic section are used.
    """
    if type(count) is not int or count not in (1,2,4,8):
        raise ValueError('registered one/two/four/eight-element extent required')
    if (not all(np.isfinite(v) and v>0 for v in (axial,shear,bending))
            or not np.isfinite(load) or load>=axial):
        raise ValueError('finite positive stiffness and positive compressed stretch required')
    refs = parabolic_references(0.,count)
    elastic = np.diag([axial,shear,shear,2*bending,bending,2*bending])
    law = DirectedHardeningSectionProbe(elastic,[1.,0.,0.,0.,0.,0.],max(1.,abs(load))*1e6,1.)
    nodes = 2*count+1
    stiffness = np.zeros((6*nodes,6*nodes))
    force = np.zeros(6*nodes)
    local_error = 0.
    moment_min,rotation_min = np.inf,np.inf
    for index,ref in enumerate(refs):
        x = ref.coordinates.copy()
        x[:,0] = -1+(1-load/axial)*(x[:,0]+1)
        response = NonlinearMixedBeamProbe(ref,law,order=order).evaluate(
            x,ref.nodal_triads,np.tile(np.eye(3),(2,1,1)),np.zeros((2,2,3)))
        h = response.hessian
        error = float(np.max(np.abs(response.residual[18:])))
        local_error = max(local_error,error)
        if error>1e-11:
            raise PrestressError('analytical compression is not locally stationary')
        try:
            moment_min = min(moment_min,float(np.linalg.eigvalsh(-h[24:,24:])[0]))
            np.linalg.cholesky(-h[24:,24:])
            schur = h[18:24,18:24]-h[18:24,24:] @ np.linalg.solve(h[24:,24:],h[24:,18:24])
            rotation_min = min(rotation_min,float(np.linalg.eigvalsh(schur)[0]))
            np.linalg.cholesky(schur)
            condensed = h[:18,:18]-h[:18,18:] @ np.linalg.solve(h[18:,18:],h[18:,:18])
        except np.linalg.LinAlgError as exc:
            raise PrestressError('local stationary block lost definiteness or invertibility') from exc
        dofs = (6*np.arange(2*index,2*index+3)[:,None]+np.arange(6)).ravel()
        stiffness[np.ix_(dofs,dofs)]+=condensed
        force[dofs]+=response.residual[:18]
    expected = np.zeros_like(force);expected[0]=load;expected[-6]=-load
    equilibrium = float(np.linalg.norm(force-expected)/max(1.,abs(load)))
    if equilibrium>1e-11 or not np.isfinite(stiffness).all():
        raise PrestressError('analytical global compression equilibrium mismatch')
    if np.linalg.norm(stiffness-stiffness.T)>1e-11*max(1.,np.linalg.norm(stiffness)):
        raise PrestressError('prestressed tangent symmetry mismatch')
    free = np.arange(6,6*nodes)
    stiffness.setflags(write=False);free.setflags(write=False)
    return PrestressRecord(count,float(load),equilibrium,local_error,moment_min,rotation_min,stiffness,free)


def critical(count, *, axial=1000., shear=400., bending=1., iterations=32):
    """Bounded bisection of the first free-stiffness sign change, not PSD proof."""
    if type(iterations) is not int or not 0<=iterations<=40:
        raise ValueError('at most forty critical-load bisections required')
    continuum = critical_load(2.,axial,shear,bending)
    initial = evaluate(count,0.,axial=axial,shear=shear,bending=bending)
    free = initial.free
    base = initial.tangent[np.ix_(free,free)]
    if np.min(np.diag(base))<=0:
        raise PrestressError('initial stiffness scaling unavailable')
    scale = 1/np.sqrt(np.diag(base))
    def eigen(load):
        record = evaluate(count,load,axial=axial,shear=shear,bending=bending)
        k = record.tangent[np.ix_(free,free)]*scale[:,None]*scale[None,:]
        return float(np.linalg.eigvalsh(k)[0])
    lower,upper = 0.,2*continuum
    if eigen(lower)<=0 or eigen(upper)>=0:
        raise PrestressError('no positive-to-negative global stiffness bracket')
    for _ in range(iterations):
        mid = .5*(lower+upper)
        if eigen(mid)>0:
            lower = mid
        else:
            upper = mid
    if upper-lower>1e-8*continuum:
        raise PrestressError('critical-load interval unresolved within budget')
    return {'elements':count,'lower':lower,'upper':upper,'continuum':continuum,
            'relative_error':(.5*(lower+upper)-continuum)/continuum,
            'iterations':iterations,'production_qualified':False}
