"""Separate closed-equation load/chart reconstruction; no producer imports."""
from math import cos, sin, sqrt
import numpy as np


def cross_matrix(v):
    x, y, z = v
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def chart(v):
    v = np.array(v, dtype=float)
    s = float(v@v)
    angle = sqrt(s)
    if angle < .01:
        a = .5-s/24+s*s/720-s*s*s/40320
        b = 1/6-s/120+s*s/5040-s*s*s/362880
        da = -1/24+s/360-s*s/13440
        db = -1/120+s/2520-s*s/120960
    else:
        a = (1-cos(angle))/s
        b = (angle-sin(angle))/(angle*s)
        da = (angle*sin(angle)-2*(1-cos(angle)))/(2*s*s)
        db = (angle*(1-cos(angle))-3*(angle-sin(angle)))/(2*angle*s*s)
    skew = cross_matrix(v)
    matrix = np.eye(3)+a*skew+b*skew@skew
    derivative = np.empty((3, 3, 3))
    for k, unit in enumerate(np.eye(3)):
        dk = cross_matrix(unit)
        derivative[:, :, k] = 2*v[k]*da*skew+a*dk+2*v[k]*db*skew@skew+b*(dk@skew+skew@dk)
    return matrix, derivative


def load(coordinates, density, order):
    """Integrate the Q2 reference metric directly from three coordinates."""
    points, weights = np.polynomial.legendre.leggauss(order)
    x = np.array(coordinates, dtype=float)
    a = (x[2]-x[0])/2
    b = x[0]-2*x[1]+x[2]
    result = np.zeros(42)
    for cell in (0, 1):
        for point, weight in zip(points, weights):
            xi = cell-1+(float(point)+1)/2
            tangent = a+xi*b
            measure = float(weight)*sqrt(float(tangent@tangent))/2
            result[18+3*cell:21+3*cell] += measure*np.array(density)
    return result


def pullback(force, spatial_jacobian, increments):
    mapping = np.eye(18)
    connection = np.zeros((18, 18))
    for i, increment in enumerate(increments):
        dofs = slice(6*i+3, 6*i+6)
        a, da = chart(increment)
        mapping[dofs, dofs] = a
        for k in range(3):
            connection[dofs, 6*i+3+k] = da[:, :, k].T@force[dofs]
    return mapping.T@force, mapping.T@spatial_jacobian@mapping+connection
