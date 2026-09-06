"""Standalone planar Reissner first-branch cantilever quadrature.

No ANYsolver, discrete beam, continuation driver or section-law imports.
Source equations: Batista arXiv:1508.04424v3, (1),(2),(5)-(10),(94),(98).
The regularized first-integral quadrature is derived here, not copied code.
Binary64 convergence checks are not interval or multiprecision certification.
"""

from dataclasses import dataclass
import math

import numpy as np


SOURCE_SHA256 = '5B596FA9B26D6AFDAD8A7C7501CE795DA47E7F1B7FD710643FA0D56E763E5E63'


class PostcriticalReferenceError(ValueError):
    """No admissible bounded first-branch reference result."""


def _parameters(length, axial, shear, bending):
    values = (length,axial,shear,bending)
    if any(not isinstance(v,(int,float,np.integer,np.floating)) or isinstance(v,(bool,np.bool_))
           or not math.isfinite(v) or v<=0 for v in values):
        raise PostcriticalReferenceError('positive finite length and stiffnesses required')
    if shear>axial:
        raise PostcriticalReferenceError('this reference family requires GA <= EA')
    return tuple(float(v) for v in values)


def critical_load(length, axial, shear, bending):
    length,axial,shear,bending = _parameters(length,axial,shear,bending)
    delta = 1/shear-1/axial
    euler = bending*(math.pi/(2*length))**2
    value = 2*euler/(1+math.sqrt(1+4*delta*euler))
    if not math.isfinite(value) or not 0<value<axial:
        raise PostcriticalReferenceError('critical state violates positive axial stretch')
    return value


@dataclass(frozen=True)
class PostcriticalReference:
    load: float
    critical_load: float
    tip_angle: float
    arclength: np.ndarray
    coordinates: np.ndarray
    angles: np.ndarray
    moments: np.ndarray
    strains: np.ndarray
    resultants: np.ndarray
    strain_energy: float
    length_residual: float
    moment_balance_residual: float
    quadrature_order: int


def solve(length, axial, shear, bending, tip_angle, *, order=64, stations=17, max_bisections=64):
    """Positive first branch, clamped at s=0, dead force (-P,0), free tip moment.

    s is reference arclength. Finite axial/shear strains are retained. The
    benchmark family is GA<=EA and 0<tip_angle<=pi/2; other branches fail closed.
    """
    length,axial,shear,bending = _parameters(length,axial,shear,bending)
    if (not isinstance(tip_angle,(int,float,np.integer,np.floating))
            or isinstance(tip_angle,(bool,np.bool_)) or not math.isfinite(tip_angle)
            or not 0<tip_angle<=math.pi/2):
        raise PostcriticalReferenceError('first-branch tip angle in (0,pi/2] required')
    if (type(order) is not int or order not in (32,64,128)
            or type(stations) is not int or not 2<=stations<=65
            or type(max_bisections) is not int or not 0<=max_bisections<=64):
        raise PostcriticalReferenceError('bounded quadrature, station and bisection counts required')
    critical = critical_load(length,axial,shear,bending)
    delta = 1/shear-1/axial
    k = math.sin(tip_angle/2)
    ca = math.cos(tip_angle)
    points,weights = np.polynomial.legendre.leggauss(order)

    def integrals(load, bound, full=False):
        phi = .5*bound*(points+1)
        sin_half = k*np.sin(phi)
        cosine = 1-2*sin_half**2
        sine = 2*sin_half*np.sqrt(1-sin_half**2)
        # sin(theta/2)=k*sin(phi) removes the tip square-root singularity.
        density = math.sqrt(bending/load)/np.sqrt(
            (1-sin_half**2)*(1+.5*load*delta*(cosine+ca)))
        w = .5*bound*weights*density
        distance = float(w.sum())
        if not full:
            return distance
        dx = cosine-load*cosine**2/axial-load*sine**2/shear
        dy = sine*(1+load*delta*cosine)
        difference = 2*k*k*np.cos(phi)**2
        moment_squared = bending*load*difference*(2+load*delta*(cosine+ca))
        energy = .5*(load**2*cosine**2/axial+load**2*sine**2/shear+moment_squared/bending)
        return np.array([distance,w @ dx,w @ dy,w @ energy])

    low,high = critical,math.nextafter(axial,0.)
    if integrals(low,math.pi/2)<length*(1-1e-12) or integrals(high,math.pi/2)>length:
        raise PostcriticalReferenceError('no admissible first-branch load bracket')
    for _ in range(max_bisections):
        middle = .5*(low+high)
        if integrals(middle,math.pi/2)>length:
            low = middle
        else:
            high = middle
    load = .5*(low+high)
    total = integrals(load,math.pi/2,True)
    error = abs(total[0]-length)/length
    if not math.isfinite(error) or error>1e-12 or not 0<load<axial:
        raise PostcriticalReferenceError('bounded load solve did not resolve length')
    s = np.linspace(0.,length,stations)
    coordinates = np.zeros((stations,2))
    angles = np.zeros(stations)
    moments = np.zeros(stations)
    strains = np.zeros((stations,3))
    resultants = np.zeros((stations,3))
    for i,target in enumerate(s):
        left,right = 0.,math.pi/2
        if i==0:
            phi = 0.
        elif i==stations-1:
            phi = math.pi/2
        else:
            for _ in range(max_bisections):
                middle = .5*(left+right)
                if integrals(load,middle)<target:
                    left = middle
                else:
                    right = middle
            phi = .5*(left+right)
        partial = integrals(load,phi,True)
        if abs(partial[0]-target)>1e-12*length:
            raise PostcriticalReferenceError('bounded station solve did not resolve arclength')
        angles[i] = tip_angle if i==stations-1 else 2*math.asin(k*math.sin(phi))
        c,t = math.cos(angles[i]),math.sin(angles[i])
        squared = bending*load*(2*k*k*math.cos(phi)**2)*(2+load*delta*(c+ca))
        moments[i] = 0. if i==stations-1 else math.sqrt(squared)
        coordinates[i] = partial[1:3]
        resultants[i] = [-load*c,load*t,moments[i]]
        strains[i] = resultants[i]/np.array([axial,shear,bending])
    balance = float(np.max(np.abs(moments-load*(coordinates[-1,1]-coordinates[:,1]))))
    if balance>1e-11*max(1.,load*length):
        raise PostcriticalReferenceError('reference first-integral/moment-balance disagreement')
    for array in (s,coordinates,angles,moments,strains,resultants):
        if not np.isfinite(array).all():
            raise PostcriticalReferenceError('nonfinite reference result')
        array.setflags(write=False)
    return PostcriticalReference(load,critical,float(tip_angle),s,coordinates,angles,moments,
        strains,resultants,float(total[3]),error,balance,order)
