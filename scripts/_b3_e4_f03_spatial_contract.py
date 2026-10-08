"""Frozen represented constants and geometry for the classical residual study.

This namespace is independent of native element operators. Expressions below
match the original diagnostic's binary64 preparation; exact arithmetic starts
after those expressions, rather than silently changing the material model.
"""
from fractions import Fraction
import math

import numpy as np


E=210e9
NU=.3
THICKNESS=.07
AREA=.01
SHEAR_AREA=.008
INERTIA=8.333333333333333e-6
G=E/(2*(1+NU))
EA=E*AREA
GAS=G*SHEAR_AREA
EI=E*INERTIA
PLANE=E/(1-NU**2)*np.array(((1.,NU,0.),(NU,1.,0.),(0.,0.,(1-NU)/2)))
PLANE.setflags(write=False)
DX=.2
DY=.23
HALFWIDTH=.05
J=DX**2+DY**2+2*HALFWIDTH**2/3
F0=1e6
L0=1.
U0=F0/(E*THICKNESS)
E0=F0*U0
OMEGA=2*math.pi/L0
ORDERS=(48,64)
IDENTITY_LIMIT=1e-10


def _q(value):
    return Fraction.from_float(float(value))


Q_E=_q(E)
Q_NU=_q(NU)
Q_THICKNESS=_q(THICKNESS)
Q_EA=_q(EA)
Q_GAS=_q(GAS)
Q_EI=_q(EI)
Q_PLANE=tuple(tuple(_q(value) for value in row) for row in PLANE)
Q_DX=_q(DX)
Q_DY=_q(DY)
Q_A=_q(HALFWIDTH)
Q_J=_q(J)
Q_F0=_q(F0)
Q_L0=_q(L0)
Q_U0=_q(U0)
Q_E0=_q(E0)
Q_OMEGA=_q(OMEGA)
Q_AREA=(4*Q_A)**2
Q_J_GEOM=Q_DX**2+Q_DY**2+2*Q_A**2/3
Q_GAMMA=Q_J_GEOM/Q_J

X_CUTS=(Fraction(-1,2),-Q_DX-Q_A,-Q_DX+Q_A,Q_DX-Q_A,Q_DX+Q_A,
        Q_L0-Q_DX-Q_A,Q_L0-Q_DX+Q_A,Q_L0+Q_DX-Q_A,Q_L0+Q_DX+Q_A,
        Fraction(3,2))
Y_CUTS=(Fraction(-1,2),-Q_DY-Q_A,-Q_DY+Q_A,Q_DY-Q_A,Q_DY+Q_A,
        Fraction(1,2))
CELLS=tuple((X_CUTS[i],X_CUTS[i+1],Y_CUTS[j],Y_CUTS[j+1])
            for j in range(5) for i in range(9))
PADS=tuple((sign_x*Q_DX-Q_A,sign_x*Q_DX+Q_A,
            sign_y*Q_DY-Q_A,sign_y*Q_DY+Q_A)
           for sign_x,sign_y in ((-1,-1),(1,-1),(1,1),(-1,1)))
FREE_EDGES=tuple((side,i,X_CUTS[i],X_CUTS[i+1],Fraction(side,2))
                for side in (-1,1) for i in range(9))


def _pair(value):
    return [str(value.numerator),str(value.denominator)]


def definition_record():
    """Bit and rational identities, units and immutable ordering conventions."""
    names=('E','NU','THICKNESS','AREA','SHEAR_AREA','INERTIA','G','EA',
           'GAS','EI','DX','DY','HALFWIDTH','J','F0','L0','U0','E0','OMEGA')
    return {
        'schema':'classical_spatial_residual_constants_v1',
        'constants':{name:{'binary64_hex':float(globals()[name]).hex(),
                           'exact':_pair(_q(globals()[name]))} for name in names},
        'plane_binary64_hex':[[float(v).hex() for v in row] for row in PLANE],
        'plane_exact':[[_pair(v) for v in row] for row in Q_PLANE],
        'area':_pair(Q_AREA),'J_geom':_pair(Q_J_GEOM),'gamma':_pair(Q_GAMMA),
        'x_cuts':[_pair(v) for v in X_CUTS],
        'y_cuts':[_pair(v) for v in Y_CUTS],
        'cell_order':'9*j+i; j=0..4 bottom to top, i=0..8 left to right',
        'load_channels':['line','root_atom','tip_atom'],
        'stress_channels':['T_xx','T_yy','T_xy'],
        'strain_channels':['u_x,x','u_y,y','u_x,y+u_y,x'],
        'free_edge_order':'bottom segments 0..8, then top segments 0..8',
        'cosine_convention':'omega=binary64(2*math.pi/L0); numpy cos(omega*s); '
            'primitive numpy sin(omega*s)/omega; no endpoint sine correction',
        'load_density':'F0/L0 + F0/(4*L0)*cos(omega*s)',
        'material_preparation':'binary64 source expressions first; lift PLANE, '
            'THICKNESS, EA, GAS, EI separately before exact polynomial algebra',
        'orders':list(ORDERS),'identity_limit':IDENTITY_LIMIT,
        'units':{'coordinates':'m','pose_theta':'rad','density':['N/m','N/m','N'],
                 'atoms':['N','N','Nm'],'stress':'N/m','area_force':'N/m^2'},
        'scope':'classical saved-state numerical residual diagnostic only; '
                'no native qualification or physical error estimator',
    }
