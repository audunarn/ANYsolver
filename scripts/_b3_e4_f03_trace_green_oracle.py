"""Independent high-precision Green-kernel quadrature for the scalar trace norm.

This bounded verification oracle uses only Decimal arithmetic and the
Neumann Green kernel. It does not import the Riesz transfer or FE helper.
Quadrature splits every density branch and the Green-kernel diagonal.
The final conversion to binary64 is explicit; no interval certificate is
claimed. Only a (Nm+3)-square scalar interface matrix is formed.
"""

from __future__ import annotations

from decimal import Decimal,localcontext
import math

import numpy as np


def _gauss(order: int,digits: int) -> list[tuple[Decimal,Decimal]]:
    """Gauss-Legendre nodes/weights on [0,1], refined in Decimal arithmetic."""
    result=[]
    one=Decimal(1)
    tolerance=Decimal(10)**(-(digits-10))
    for index in range(1,order//2+1):
        z=Decimal(str(math.cos(math.pi*(index-.25)/(order+.5))))
        for _ in range(50):
            old=one; value=z
            for k in range(2,order+1):
                old,value=value,((2*k-1)*z*value-(k-1)*old)/k
            derivative=order*(z*value-old)/(z*z-one)
            step=value/derivative
            z-=step
            if abs(step)<tolerance:
                break
        else:
            raise ArithmeticError('Decimal Gauss root did not converge')
        old=one; value=z
        for k in range(2,order+1):
            old,value=value,((2*k-1)*z*value-(k-1)*old)/k
        derivative=order*(z*value-old)/(z*z-one)
        weight=one/((one-z*z)*derivative*derivative)
        result.extend((((one-z)/2,weight),((one+z)/2,weight)))
    return sorted(result)


def _cosh(x: Decimal) -> Decimal:
    positive=x.exp()
    return (positive+1/positive)/2


def green_gram(n_mortar: int,order: int = 12,digits: int = 70) -> np.ndarray:
    """Normalized enriched Gram: all P1 hats, then root and tip atoms.

    h/2 normalizes each boundary density hat; h normalizes each interior
    density hat; endpoint actions have measure 1. Endpoint rows are forces,
    with the same independent channel convention as the line functionals.
    """
    if (type(n_mortar) is not int or not 2<=n_mortar<=16 or
            type(order) is not int or order not in (8,12,16) or
            type(digits) is not int or not 50<=digits<=100):
        raise ValueError('outside bounded Decimal Green-oracle domain')
    with localcontext() as context:
        context.prec=digits
        zero=Decimal(0); one=Decimal(1); h=one/n_mortar
        points=_gauss(order,digits)
        expone=one.exp(); sinh=(expone-1/expone)/2
        size=n_mortar+3
        out=[[zero for _ in range(size)] for _ in range(size)]
        left_integrals=[]; right_integrals=[]
        for cell in range(n_mortar):
            a=cell*h
            left=[zero,zero]; right=[zero,zero]
            for xi,weight in points:
                s=a+h*xi
                for i,shape in enumerate((one-xi,xi)):
                    left[i]+=h*weight*shape*_cosh(s)
                    right[i]+=h*weight*shape*_cosh(one-s)
            left_integrals.append(left); right_integrals.append(right)
            # Diagonal square is split into s<t and its reflected triangle.
            for u,wu in points:
                t=a+h*u
                nt=(one-u,u)
                for v,wv in points:
                    s=a+h*u*v
                    ns=(one-u*v,u*v)
                    kernel=_cosh(s)*_cosh(one-t)/sinh
                    measure=h*h*u*wu*wv
                    for i in range(2):
                        for j in range(2):
                            out[cell+i][cell+j]+=measure*kernel*(ns[i]*nt[j]+nt[i]*ns[j])
        for a in range(n_mortar):
            for b in range(a+1,n_mortar):
                for i in range(2):
                    for j in range(2):
                        value=left_integrals[a][i]*right_integrals[b][j]/sinh
                        out[a+i][b+j]+=value
                        out[b+j][a+i]+=value
            for i in range(2):
                root=right_integrals[a][i]/sinh
                tip=left_integrals[a][i]/sinh
                out[a+i][-2]+=root; out[-2][a+i]+=root
                out[a+i][-1]+=tip; out[-1][a+i]+=tip
        out[-2][-2]=out[-1][-1]=_cosh(one)/sinh
        out[-2][-1]=out[-1][-2]=one/sinh
        measures=[h]*(n_mortar+1)+[one,one]
        measures[0]=measures[n_mortar]=h/2
        result=np.array([[float(out[i][j]/(measures[i]*measures[j]))
                          for j in range(size)] for i in range(size)])
    if not np.all(np.isfinite(result)):
        raise ArithmeticError('nonfinite Green norm')
    return result
