"""Frozen numerical-core inventory; execute only with reviewed bounded runner."""
from fractions import Fraction as F
import json
from pathlib import Path
import numpy as np
import pytest
from anysolver._ge_beam3_g3c_b2_physical import evaluate, physical_rigidities, RepresentabilityError

CONTRACT=json.loads((Path(__file__).resolve().parents[1]/'docs/reference_cases/ge_beam3_g3c_b2_physical_contract_v1.json').read_text())

def cases():
    for row in CONTRACT['fixtures']:
        x={k:float(F(v)) for k,v in row.items() if k!='id'}
        S=physical_rigidities(*(x[k] for k in ('E','nu','A','Iy','Iz','J','ky','kz')))
        yield row['id'],x,S

def equal(a,b,relative=False):
    a,b=np.asarray(a),np.asarray(b)
    scale=max(np.linalg.norm(a),np.linalg.norm(b))
    if not relative:scale=max(1.,scale)
    assert np.isfinite(a).all() and np.isfinite(b).all()
    assert np.linalg.norm(a-b)<=1e-11*scale

def oracle(L,S,d):
    """Independent exact 6x6 flexibility elimination, no target internals."""
    l=F(L);s=list(map(F,S));v=list(map(F,d));z=F(0)
    H=[[z]*6 for _ in range(6)]
    H[0][0]=l/s[0];H[1][1]=l/s[3]
    for start,ei,shear in ((2,s[4],s[2]),(4,s[5],s[1])):
        for i in range(2):
            for j in range(2):H[start+i][start+j]=l/ei*(F(1,3) if i==j else -F(1,6))+1/(shear*l)
    B=[[z]*12 for _ in range(6)];B[1][3]=-1;B[1][9]=1
    for i,r in ((2,4),(3,10)):B[i][2]=-1/l;B[i][8]=1/l;B[i][r]=1
    for i,r in ((4,5),(5,11)):B[i][1]=1/l;B[i][7]=-1/l;B[i][r]=1
    rhs=[sum(a*b for a,b in zip(row,v)) for row in B]
    augmented=[r[:]+[b] for r,b in zip(H,rhs)]
    for i in range(6):
        pivot=augmented[i][i];augmented[i]=[a/pivot for a in augmented[i]]
        for j in range(6):
            if i!=j:
                t=augmented[j][i];augmented[j]=[a-t*b for a,b in zip(augmented[j],augmented[i])]
    q=[row[-1] for row in augmented]
    du,dv,dw=[(v[i+6]-v[i])/l for i in range(3)]
    e=du+(dv*dv+dw*dw)/2;N=s[0]*e
    de=[z]*12;de[:3]=[-1/l,-dv/l,-dw/l];de[6:9]=[1/l,dv/l,dw/l]
    force=[sum(B[i][j]*q[i] for i in range(6))+l*N*de[j] for j in range(12)]
    energy=sum(a*b for a,b in zip(rhs,q))/2+s[0]*l*e*e/2
    return float(energy),np.array(list(map(float,force)))

def test_physical_blocks_all_fixtures():
    for _,x,S in cases():
        d=.013*np.sin(np.arange(12)+.4);out=evaluate(x['L'],S,d);energy,force=oracle(x['L'],S,d)
        equal(out.energy,energy,True);equal(out.force,force,True);equal(out.tangent,out.tangent.T)

def test_all_six_component_fields():
    _,x,S=list(cases())[3];seen=np.zeros(6,dtype=bool)
    for dof in (6,7,8,9,10,11):
        d=np.zeros(12);d[dof]=.01;out=evaluate(x['L'],S,d)
        seen|=np.any(out.resultants!=0,axis=0)
        equal(out.strains*S,out.resultants,True)
        energy,force=oracle(x['L'],S,d);equal(out.energy,energy,True);equal(out.force,force,True)
    assert seen.all()

def test_clamp_relative_energy_work():
    for name,x,S in cases():
        if name not in ('CLAMP','SHEAR_SOFT'):continue
        for index in (7,8):
            d=np.zeros(12);d[index]=.01;d[6]=-.5*d[index]**2/x['L']
            out=evaluate(x['L'],S,d)
            integrated=.5*np.einsum('s,si,si->',out.weights,out.strains,out.resultants)
            recovered=np.einsum('s,sij,si->j',out.weights,out.strain_differential,out.resultants)
            equal(out.energy,integrated,True);equal(out.force,recovered,True)
            # Rational oracle retains actual rounded d, including any tiny axial residue.
            energy,force=oracle(x['L'],S,d);equal(out.energy,energy,True);equal(out.force,force,True)

def test_finite_force_tangent_all_steps():
    d=.013*np.sin(np.arange(12)+.4);v=np.cos(np.arange(12)+.7);v/=np.linalg.norm(v)
    for _,x,S in cases():
        out=evaluate(x['L'],S,d)
        for h in (1e-4,1e-5,1e-6):
            p=evaluate(x['L'],S,d+h*v);m=evaluate(x['L'],S,d-h*v)
            assert np.linalg.norm((p.force-m.force)/(2*h)-out.tangent@v)<=1e-7*max(1.,np.linalg.norm(out.tangent@v))
            assert abs((p.energy-m.energy)/(2*h)-out.force@v)<=1e-7*max(1.,abs(out.force@v))

def test_legacy_unclamped_agreement():
    for name,x,S in cases():
        if name in ('CLAMP','SHEAR_SOFT'):continue
        L=x['L']
        for index,ei,shear in ((7,S[5],S[1]),(8,S[4],S[2])):
            d=np.zeros(12);d[index]=.01;d[6]=-.5*d[index]**2/L
            old=6*ei*d[index]**2/(L**3*(1+12*ei/max(shear*L**2,1e-12)))
            equal(evaluate(L,S,d).energy,old,True)

def test_units_and_rigidity_range():
    for name,x,S in cases():
        if name!='CLAMP':continue
        d=.013*np.sin(np.arange(12)+.4);base=evaluate(x['L'],S,d)
        for power in (-40,-10,0,10,40):
            factor=2.**power;out=evaluate(x['L'],S*factor,d)
            equal(out.force,base.force*factor,True);equal(out.energy,base.energy*factor,True)
        for c in (1/1024,1.,1024.):
            for f in (1/256,1.,256.):
                scales=np.tile([c,c,c,1,1,1],2);row=np.tile([f,f,f,f*c,f*c,f*c],2)
                out=evaluate(x['L']*c,S*np.array([f,f,f,f*c*c,f*c*c,f*c*c]),d*scales)
                equal(out.energy,base.energy*f*c,True);equal(out.force,base.force*row,True)
                equal(out.tangent,base.tangent*row[:,None]/scales[None,:],True)

def test_immutable_detached_outputs():
    _,x,S=next(cases());d=np.zeros(12);out=evaluate(x['L'],S,d);d[:]=2
    for array in (out.force,out.tangent,out.strains,out.resultants,out.strain_differential,out.stations,out.weights):
        assert not array.flags.writeable
        with pytest.raises(ValueError):array.setflags(write=True)
    assert out.energy==0 and not out.production_qualified

def test_input_and_representability_rejection():
    _,x,S=next(cases());d=np.zeros(12)
    for L in (True,0.,-1.,float('nan'),float('inf')):
        with pytest.raises(ValueError):evaluate(L,S,d)
    for E,A in ((1e308,1e308),(1e-300,1e-300)):
        with pytest.raises(RepresentabilityError):physical_rigidities(E,0,A,1,1,1,1,1)
    for bad in (np.ones(5),np.ones(6,dtype=int),np.zeros(6),np.full(6,np.nan)):
        with pytest.raises(ValueError):evaluate(1.,bad,d)
