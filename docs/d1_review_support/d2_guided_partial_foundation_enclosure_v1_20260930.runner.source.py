"""Saved-pose continuum error enclosures; no structural/contact evaluations.

The fixed fixture's Decimal reference is evaluated at EVERY midpoint. Global
Lipschitz bounds turn these values into integral bounds, not a sampled-L2 claim.
See D2_GUIDED_PARTIAL_FOUNDATION_ENCLOSURE_DERIVATION_20260930.md.
"""
import argparse
from decimal import Decimal as D, localcontext, ROUND_HALF_EVEN
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Reference:
    def __init__(self,summary):
        self.K=D.from_float(summary["D_n_per_m"])
        self.q=D.from_float(summary["q_pa"])
        self.g=D.from_float(summary["initial_gap_m"])
        self.k=D.from_float(summary["kappa_pa_per_m"])
        self.L=D.from_float(summary["length_m"])
        self.C=D.from_float(summary["supported_length_m"])
        self.T=self.L-self.C
        if not (D(1602)<self.K<D(1603) and self.q==D('.5') and self.k==D(1000000)
                and self.L==1 and summary["width_m"]==1. and abs(self.g-D('.0001'))<D('1e-18')
                and abs(self.C-D('.9'))<D('1e-16')):
            raise ValueError("enclosure derivation is specific to the frozen fixture")
        self.beta=(self.k/self.K).sqrt()
        lo,hi=D('.7'),D('.8')
        guard=D('1e-60')
        if not (self.required_gap(lo)+guard<self.g<self.required_gap(hi)-guard):
            raise ValueError("positive partial-contact root not bracketed")
        for _ in range(250):
            mid=(lo+hi)/2
            f=self.required_gap(mid)-self.g
            if f+guard<0:lo=mid
            elif f-guard>0:hi=mid
            else:break
        self.lo,self.hi=lo,hi
        if hi-lo>D('1e-20'):
            raise ValueError("front bracket does not resolve the point allowance")
        self.a=(lo+hi)/2
        self.cosh_a=self.cosh(self.beta*(self.C-self.a))
        self.b=-self.g/self.a-self.q*self.a/(2*self.K)
        self.cut=self.active(self.C)

    @staticmethod
    def cosh(x):return (x.exp()+(-x).exp())/2

    @staticmethod
    def sinh(x):return (x.exp()-(-x).exp())/2

    def required_gap(self,a):
        lam=self.beta*(self.C-a)
        c=self.cosh(lam)
        return self.q/self.K*(a*a/2+a*self.sinh(lam)/c/self.beta+a*self.T/c)

    def active(self,s):
        return (-self.g-self.q/self.k
            +self.q/self.k*self.cosh(self.beta*(self.C-s))/self.cosh_a
            -self.q*self.T/(self.K*self.beta)*self.sinh(self.beta*(s-self.a))/self.cosh_a)

    def value(self,s):
        if s<self.a:return self.q*s*s/(2*self.K)+self.b*s
        if s<=self.C:return self.active(s)
        t=s-self.C
        return self.cut-self.q*self.T*t/self.K+self.q*t*t/(2*self.K)

    def force(self):
        lam=self.beta*(self.C-self.a)
        return self.q*(self.C-self.a-self.sinh(lam)/self.cosh_a/self.beta
            +self.T*(1-1/self.cosh_a))


def assess(case,cells):
    nx=case["nx"]
    if nx not in (79,159) or not case["assessment"]["development_checks_met"]:
        raise ValueError("completed passing development source required")
    u=np.asarray(case["displacements"])
    if len(u)!=6*(2*(nx+1)+4):raise ValueError("fixture coordinate count differs")
    q=u[2:6*(nx+1):6]
    top=u[6*(nx+1)+2:12*(nx+1):6]
    if not np.array_equal(q,top) or np.max(abs(q))>=.001:
        raise ValueError("fixed-field interpolation scope differs")
    reference=Reference(case["reference"])
    if not (0<reference.force()<reference.q*reference.L):
        raise ValueError("reference derivative-bound force assumption fails")
    x=np.linspace(0.,1.,cells+1)
    h=np.diff(x);mid=(x[:-1]+x[1:])/2
    exact=np.fromiter((float(reference.value(D.from_float(float(s)))) for s in mid),float,count=cells)
    if np.max(abs(exact))>=.001:
        raise ValueError("reference conversion allowance no longer applies")
    fe=np.interp(mid,np.arange(nx+1)/nx,q)
    # Budgets include binary conversion, field-coordinate/interpolation errors,
    # slope evaluation and cell-radius rounding; fixed-domain derivation linked.
    value_budget=1e-18
    interpolation_budget=1e-14
    slope=float(np.max(abs(np.diff(q)*nx)))+1e-12
    if slope>=1.:raise ValueError("interpolation operation bound does not apply")
    reference_slope=float(2*reference.q*reference.L/reference.K)+1e-12
    radius=h/2+1e-15
    error=abs(fe-exact)
    e_radius=(slope+reference_slope)*radius+value_budget+interpolation_budget
    r_radius=reference_slope*radius+value_budget
    nlo=float(np.sum(h*np.maximum(error-e_radius,0.)**2))
    nhi=float(np.sum(h*(error+e_radius)**2))
    dlo=float(np.sum(h*np.maximum(abs(exact)-r_radius,0.)**2))
    dhi=float(np.sum(h*(abs(exact)+r_radius)**2))
    gamma=(10*cells+100)*np.finfo(float).eps
    gamma=gamma/(1-gamma)
    if dlo<=0.:raise ValueError("reference L2 denominator unresolved")
    outer=32*np.finfo(float).eps
    nlo_bound=float(np.nextafter(nlo/(1+gamma),0.))
    nhi_bound=float(np.nextafter(nhi/(1-gamma),np.inf))
    dlo_bound=float(np.nextafter(dlo/(1+gamma),0.))
    dhi_bound=float(np.nextafter(dhi/(1-gamma),np.inf))
    l2lo=float(np.nextafter(np.sqrt(nlo_bound/dhi_bound)*(1-outer),0.))
    l2hi=float(np.nextafter(np.sqrt(nhi_bound/dlo_bound)*(1+outer),np.inf))
    tip=abs(float(reference.value(reference.L)))-value_budget
    linfhi=float(np.nextafter((np.max(error+e_radius)+interpolation_budget)/tip*(1+gamma+outer),np.inf))
    force=float(reference.force())
    force_budget=1e-15
    actual_force=float(case["assessment"]["certificate"]["integration_force"][2])
    force_hi=float(np.nextafter((abs(actual_force-force)+force_budget)/(force-force_budget)*(1+outer),np.inf))
    return dict(nx=nx,reference_front_bracket_m=[str(reference.lo),str(reference.hi)],
        root_guard_m="1e-60",reference_value_rounding_budget_m=value_budget,
        interpolation_coordinate_budget_m=interpolation_budget,
        reference_contact_force_n=force,reference_force_budget_n=force_budget,
        maximum_fe_slope=slope,reference_slope_bound=reference_slope,
        l2_relative_interval=[l2lo,l2hi],linfinity_relative_upper=linfhi,
        numerator_integral_interval_m3=[nlo_bound,nhi_bound],
        denominator_integral_interval_m3=[dlo_bound,dhi_bound],
        force_relative_upper=force_hi,positive_sum_gamma=gamma,
        checks=dict(analytic_force=force_hi<=.001,analytic_l2=l2hi<=.001,
                    analytic_global_displacement=linfhi<=.001))


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument("--saved",nargs=2,type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    freeze=args.output.with_suffix(".inputs.json")
    snapshot=args.output.with_suffix(".runner.source.py")
    if any(p.exists() for p in (args.output,freeze,snapshot)):raise FileExistsError(args.output)
    cases=[json.loads(p.read_text(encoding="utf-8")) for p in args.saved]
    if [c["nx"] for c in cases]!=[79,159]:raise ValueError("fixed refinement pair required")
    if cases[0]["inputs"]!=cases[1]["inputs"] or cases[0]["package"]!=cases[1]["package"]:
        raise ValueError("mechanics or package identity differs across refinement")
    mismatches=[p for p,v in cases[0]["package"].items() if sha(Path("src/anysolver")/p)!=v]
    if mismatches:raise ValueError(f"candidate source changed: {mismatches}")
    record=dict(accepted=False,released=False,cells=1000000,analytic_relative_target=.001,
        inputs=[dict(path=str(p),sha256=sha(p)) for p in args.saved],source_sha256=sha(__file__),
        derivation_sha256=sha(Path(__file__).with_name("D2_GUIDED_PARTIAL_FOUNDATION_ENCLOSURE_DERIVATION_20260930.md")),
        decimal_precision=80,decimal_rounding="ROUND_HALF_EVEN",python=sys.version,
        resource_caps=dict(seconds=180,process_tree_bytes=1073741824),
        limits="fixed guided partial-support benchmark only; no installed admission, uniform stability or radial regrade")
    snapshot.write_bytes(Path(__file__).read_bytes())
    freeze.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    start=time.perf_counter()
    with localcontext() as context:
        context.prec=80
        context.rounding=ROUND_HALF_EVEN
        record["rows"]=[assess(c,record["cells"]) for c in cases]
    first,last=record["rows"]
    record["meaningful_refinement"]=dict(
        enclosed_displacement_improves=last["l2_relative_interval"][1]<first["l2_relative_interval"][0],
        physical_bins_improve=cases[1]["assessment"]["metrics"]["physical_bin_l1_relative"]<
            cases[0]["assessment"]["metrics"]["physical_bin_l1_relative"])
    record["development_checks_met"]=all(last["checks"].values()) and all(record["meaningful_refinement"].values())
    record["elapsed_seconds"]=time.perf_counter()-start
    args.output.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:record[k] for k in ("development_checks_met","elapsed_seconds","rows","meaningful_refinement")}),flush=True)
    raise SystemExit(0 if record["development_checks_met"] else 1)


if __name__=="__main__":main()
