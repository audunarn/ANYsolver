"""Independent exact binary original-Q1 posed gap and chart bounds.

Input is the authoritative saved physical nodal pose, independently reconstructed
before use. No production geometry, projection or surface triangulation is used.
"""
from fractions import Fraction as F
SOURCE=((1,2,5,4),(2,3,6,5))
TARGET=((7,8,11,10),(8,9,12,11),(10,11,14,13),(11,12,15,14))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def normals(q):return tuple(cross(sub(q[(i+1)%4],q[i]),sub(q[(i-1)%4],q[i])) for i in range(4))


def posed_bounds(points,axis):
    p=[tuple(F(float(v)) for v in row) for row in points]
    a=tuple(F(float(v)) for v in axis)
    sourceids={i for f in SOURCE for i in f};targetids={i for f in TARGET for i in f}
    delta=min(dot(p[i-1],a) for i in sourceids)-max(dot(p[i-1],a) for i in targetids)
    negative=[];positive=[];charts=[]
    for sids in SOURCE:
        source=[p[i-1] for i in sids];ns=normals(source);n0=ns[0]
        axis_alignment=min(dot(n,a) for n in ns);assert axis_alignment>0
        # A positive exact coordinate component bounds the Euclidean norm.
        distances=[min(n[k] for n in ns) if min(n[k] for n in ns)>0
                   else -max(n[k] for n in ns) if max(n[k] for n in ns)<0 else F(0)
                   for k in range(3)]
        denominator=max(distances);assert denominator>0
        alignment=min(dot(n,n0) for n in ns);assert alignment>0
        upper=max(sum(abs(x) for x in n) for n in ns)
        for tids in TARGET:
            target=[p[i-1] for i in tids]
            target_alignment=min(dot(n,n0) for n in normals(target));assert target_alignment>0
            numerator=min(dot(sub(x,y),n) for x in source for y in target for n in ns)
            negative.append(min(F(0),numerator)/denominator)
            # The chart projection ray is parallel to n0. The global Q1 axis
            # envelope therefore bounds its ray length, while n0.N positivity
            # converts that ray to the actual varying-source-normal signed gap.
            if delta>0:positive.append(delta*alignment/(dot(n0,a)*upper))
            charts.append(dict(source_alignment=str(alignment),target_alignment=str(target_alignment),axis_alignment=str(axis_alignment)))
    lower=min(negative);assert lower>=-F(float(5e-5))
    result=dict(kind='exact_binary_original_Q1_all_pair_negative_bound_and_axis_chart_separation',all_pairs=len(negative),lower_m=float(lower),lower_fraction=str(lower),axis=tuple(float(x) for x in a),axis_clearance_fraction=str(delta),strict_positive=delta>0,chart_margins=charts)
    if positive:result.update(strict_positive_gap_lower_m=float(min(positive)),strict_positive_gap_lower_fraction=str(min(positive)))
    return result
