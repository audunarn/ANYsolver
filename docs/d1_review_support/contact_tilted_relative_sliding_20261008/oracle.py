"""Exact binary original-Q1 footprint in a registered tilted projection chart.

The original bilinear projected image is its convex quadrilateral when the four
corner Jacobians are positive. No triangle substitution or production overlap
kernel is used. Area is the registered binary-chart measure, not pressure support.
"""
from fractions import Fraction as F
import importlib.util
from pathlib import Path
def _load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
_repo=Path(__file__).parents[3]
_clip=_load('_tilted_exact_clip',_repo/'tests/test_general_contact_automatic_q4_pair.py')
_clip_exact,_turn=_clip._clip_exact,_clip._turn
_gap=_load('_tilted_finite_gap',Path(__file__).parents[1]/'contact_finite_rotation_shell_work_20261008/oracle.py')
posed_bounds,SOURCE,TARGET=_gap.posed_bounds,_gap.SOURCE,_gap.TARGET

def projected_footprint(points,axis_x,axis_y):
    axes=[tuple(F(float(v)) for v in a) for a in (axis_x,axis_y)]
    p=[tuple(sum(F(float(v))*a for v,a in zip(row,axis)) for axis in axes) for row in points]
    def area(poly):
        return abs(sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly))))/2 if len(poly)>=3 else F(0)
    entries=[]
    for si,sids in enumerate(SOURCE):
        s=[p[i-1] for i in sids];assert all(_turn(s[i],s[(i+1)%4],s[(i+2)%4])>0 for i in range(4))
        for ti,tids in enumerate(TARGET):
            t=[p[i-1] for i in tids];assert all(_turn(t[i],t[(i+1)%4],t[(i+2)%4])>0 for i in range(4))
            clipped=_clip_exact(s,t);a=area(clipped)
            entries.append(dict(source_face=si,target_face=ti,area_fraction=str(a),area_m2=float(a),vertex_count=len(clipped)))
    total=sum(F(p['area_fraction']) for p in entries)
    seam=[]
    def cross2(a,b):return a[0]*b[1]-a[1]*b[0]
    for si,(left,right) in enumerate(((10,11),(11,12))):
        q=[p[i-1] for i in SOURCE[si]]
        a=tuple((q[0][k]+q[1][k])/2 for k in range(2))
        b=tuple((q[3][k]+q[2][k])/2 for k in range(2))
        e=p[left-1];f=p[right-1]
        d=tuple(b[k]-a[k] for k in range(2));edge=tuple(f[k]-e[k] for k in range(2));r=tuple(e[k]-a[k] for k in range(2))
        determinant=cross2(d,edge);assert determinant!=0
        v=cross2(r,edge)/determinant;t=cross2(r,d)/determinant
        assert 0<v<1 and 0<t<1
        seam.append(dict(source_face=si,source_material_u='1/2',source_material_v_fraction=str(v),source_material_v=float(v),target_edge=[left,right],target_edge_parameter_fraction=str(t)))
    return dict(kind='exact_binary_registered_chart_original_Q1_convex_footprint',total_area_fraction=str(total),total_area_m2=float(total),pairs=entries,positive_area_pairs=[[p['source_face'],p['target_face']] for p in entries if F(p['area_fraction'])>0],axes=[list(map(float,a)) for a in axes],seam_material_coordinates=seam)
