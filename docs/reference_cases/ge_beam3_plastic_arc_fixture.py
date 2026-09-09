"""Immutable data for the first active-plastic arc smoke; no mechanics imports."""
from copy import deepcopy
from math import sqrt

ID = 'GE_BEAM3_ACTIVE_PLASTIC_ARC_SMOKE_V1'

def tensor(diagonal, changes):
    a = [[float(i == j) for j in range(6)] for i in range(6)]
    for i, j, value in changes:
        a[i][j] = value
    return [[sum(a[k][i]*diagonal[k]*a[k][j] for k in range(6)) for j in range(6)] for i in range(6)]

def fixture(macros=1):
    if type(macros) is not int or macros not in (1, 2):
        raise ValueError('one curved macro or two connected curved macros')
    points = []; frames = []
    for i in range(2*macros+1):
        x = float(i/macros); slope = .4*(1.-x); norm = sqrt(1.+slope*slope)
        t = [1./norm, slope/norm, 0.]
        points.append([x, .2*(1.-(x-1.)**2), 0.])
        frames.append([[t[0], 0., t[1]], [t[1], 0., -t[0]], [0., 1., 0.]])
    return deepcopy(dict(schema=ID, macros=macros, points=points, frames=frames,
        connectivity=[list(range(2*i+1, 2*i+4)) for i in range(macros)], fixed_node=1,
        elastic=tensor([4., 6., 8., 2., 3., 5.], [(0,3,.2),(1,4,-.3),(2,5,.25),(0,1,.1)]),
        metric=tensor([1., .25, .5, 2., .75, 1.5], [(0,5,.2),(1,3,-.15),(2,4,.1)]),
        yield_force=.025, hardening=.6, order=4,
        steps=[.05, .05, .05], length_scale=2., parameter_scale=1., initial_sign=1.,
        max_iterations=24, max_backtracks=8, force=[2*macros+1, 1., .2, .1]))
