"""Exact binary-pose separation/chart proof; no production geometry kernels."""
from fractions import Fraction as F

SOURCE=((1,2,5,4),(2,3,6,5))
TARGET=((7,8,11,10),(8,9,12,11),(10,11,14,13),(11,12,15,14))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def normals(q):return tuple(cross(sub(q[(k+1)%4],q[k]),sub(q[(k-1)%4],q[k])) for k in range(4))


def strict_separation(points,source_faces=SOURCE,target_faces=TARGET):
    p=[tuple(F(float(x)) for x in row) for row in points]
    source_ids={n for face in source_faces for n in face};target_ids={n for face in target_faces for n in face}
    delta=min(p[n-1][2] for n in source_ids)-max(p[n-1][2] for n in target_ids)
    result=dict(kind='exact_Q1_global_z_and_varying_source_normal_chart_separation',global_z_clearance_m=float(delta),global_z_clearance_fraction=str(delta),all_pairs=len(source_faces)*len(target_faces),strict_positive=delta>0)
    if delta<=0:return result
    lowers=[];chart_margins=[]
    for face in source_faces:
        ns=normals([p[n-1] for n in face]);n0=ns[0];assert n0[2]>0 and min(n[2] for n in ns)>0
        align=min(dot(n,n0) for n in ns);assert align>0
        upper=max(sum(abs(x) for x in n) for n in ns);assert upper>0
        lower=delta*align/(n0[2]*upper);assert lower>0
        for target in target_faces:
            target_align=min(dot(n,n0) for n in normals([p[n-1] for n in target]));assert target_align>0
            lowers.append(lower);chart_margins.append((str(align),str(target_align)))
    minimum=min(lowers)
    result.update(source_normal_gap_lower_m=float(minimum),source_normal_gap_lower_fraction=str(minimum),exact_raw_normal_chart_margins=chart_margins,norm_upper='max corner L1, exact rational; no sqrt')
    return result
