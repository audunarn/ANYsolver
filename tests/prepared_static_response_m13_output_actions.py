"""Output-aware conditional uncertainty actions; diagnostic graph only."""
from dataclasses import dataclass
import numpy as np
from prepared_static_response_m10_bounds import *
from prepared_static_response_m12_resident import ResidentSolveBound,ResidentRefusal,triangular_center_error

@dataclass
class Node:
    row:list
    noise:dict
    interval:tuple

class OutputActions(ResidentSolveBound):
    def prepare(self,rhs,cancellation=None):
        require_authority()
        if cancellation is not None:cancellation()
        require_authority()
        b=np.asarray(rhs)
        if b.dtype!=np.float64 or b.shape!=self.scaling.shape or not np.all(np.isfinite(b)):
            raise ResidentRefusal('rhs')
        try:bi=[rounded((rational(s)*rational(x),)*2) for s,x in zip(self.scaling,b)]
        except (OverflowError,AssertionError):raise ResidentRefusal('scaling_overflow')
        bc=[(bi[i][0]+bi[i][1])/2 for i in self.roworder]
        db=[(bi[i][1]-bi[i][0])/2 for i in self.roworder]
        yc,ey=triangular_center_error(self.L,bc,db,True)
        zc,ez=triangular_center_error(self.U,yc,ey,False)
        n=len(b);count=2*n+2;g=count*UNIT/(ONE-count*UNIT)
        def residual(T,c,e,inputs,ei):
            return [g*(sum((abs(t)*(abs(x)+r) for t,x,r in zip(row,c,e)),ZERO)+abs(inputs[i])+ei[i])+count*TINY*(ONE+abs(row[i]))/(ONE-count*UNIT) for i,row in enumerate(T)]
        RL=residual(self.L,yc,ey,bc,db);RU=residual(self.U,zc,ez,yc,ey)
        graph=Graph(self,zc,db,RL,RU)
        nodes=[]
        for i,s in enumerate(self.scaling):
            j=self.pc[i];row=[ZERO]*n;row[j]=rational(s)
            base=(rational(s)*(zc[j]-ez[j]),rational(s)*(zc[j]+ez[j]))
            interval=scale((zc[j]-ez[j],zc[j]+ez[j]),s)
            radius=UNIT*max(abs(base[0]),abs(base[1]))+TINY
            nodes.append(graph.new_node(row,{},interval,radius,'final_scaling'))
        if cancellation is not None:cancellation()
        require_authority()
        return graph,nodes

def transpose_action(T,w,lower):
    n=len(w);x=[ZERO]*n
    for i in (reversed(range(n)) if lower else range(n)):
        prior=range(i+1,n) if lower else range(i)
        x[i]=(w[i]-sum((T[j][i]*x[j] for j in prior),ZERO))/T[i][i]
    return x

class Graph:
    def __init__(self,owner,center,db,RL,RU):
        self.owner=owner;self.center=center;self.db=db;self.RL=RL;self.RU=RU
        self.errors=[]

    def new_node(self,row,noise,interval,radius,tag):
        require_authority()
        if interval[0]>interval[1] or max(abs(interval[0]),abs(interval[1]))>rational(np.finfo(float).max):
            raise ResidentRefusal('graph_interval_overflow')
        noise=dict(noise)
        if radius:
            index=len(self.errors);self.errors.append((radius,tag));noise[index]=ONE
        return Node(row,noise,interval)

    def linear(self,weights,nodes,interval,radius,tag):
        weights=[rational(w) if not isinstance(w,Q) else w for w in weights]
        row=[sum((w*node.row[j] for w,node in zip(weights,nodes) if w),ZERO) for j in range(len(self.center))]
        noise={}
        for w,node in zip(weights,nodes):
            if not w:continue
            for key,value in node.noise.items():noise[key]=noise.get(key,ZERO)+w*value
        noise={key:value for key,value in noise.items() if value}
        return self.new_node(row,noise,interval,radius,tag)

    def dot(self,weights,nodes,tag):
        if len(weights)!=len(nodes) or not len(weights) or 2*len(weights)*UNIT>=ONE:
            raise ResidentRefusal('graph_dot_count')
        if not np.all(np.isfinite(weights)):
            raise ResidentRefusal('graph_nonfinite_weight')
        interval=dot(weights,[n.interval for n in nodes]);count=2*len(weights)
        magnitude=sum((abs(rational(w))*max(abs(n.interval[0]),abs(n.interval[1])) for w,n in zip(weights,nodes)),ZERO)
        radius=count*UNIT/(ONE-count*UNIT)*magnitude+count*TINY/(ONE-count*UNIT)
        return self.linear(weights,nodes,interval,radius,tag)

    def matvec(self,A,nodes,tag):return [self.dot(row,nodes,tag) for row in A]

    def add(self,a,b,tag):
        interval=add(a.interval,b.interval)
        magnitude=max(abs(a.interval[0]+b.interval[0]),abs(a.interval[1]+b.interval[1]))
        return self.linear([ONE,ONE],[a,b],interval,UNIT*magnitude+TINY,tag)

    def scale(self,a,factor,tag):
        f=rational(factor);interval=scale(a.interval,factor)
        magnitude=abs(f)*max(abs(a.interval[0]),abs(a.interval[1]))
        return self.linear([f],[a],interval,UNIT*magnitude+TINY,tag)

    def divide(self,a,factor,tag):
        f=rational(factor)
        if f==0:raise ResidentRefusal('zero_divisor')
        interval=divide(a.interval,factor)
        magnitude=max(abs(a.interval[0]),abs(a.interval[1]))/abs(f)
        return self.linear([ONE/f],[a],interval,UNIT*magnitude+TINY,tag)

    def negate(self,a):
        return self.linear([-ONE],[a],(-a.interval[1],-a.interval[0]),ZERO,'exact_sign')

    def enclose(self,node):
        require_authority()
        a=transpose_action(self.owner.U,node.row,False)
        c=transpose_action(self.owner.L,a,True)
        contributions={'rhs_scaling':sum((abs(w)*r for w,r in zip(c,self.db)),ZERO),
            'native_forward':sum((abs(w)*r for w,r in zip(c,self.RL)),ZERO),
            'native_backward':sum((abs(w)*r for w,r in zip(a,self.RU)),ZERO)}
        for key,value in node.noise.items():
            radius,tag=self.errors[key]
            contributions[tag]=contributions.get(tag,ZERO)+abs(value)*radius
        radius=sum(contributions.values(),ZERO)
        center=sum((w*x for w,x in zip(node.row,self.center)),ZERO)
        require_authority()
        return (center-radius,center+radius),contributions

def require_authority():
    for name,expected in _BINDINGS.items():
        if globals().get(name) is not expected or expected.__code__ is not _CODES[name]:
            raise ResidentRefusal('diagnostic_source_authority')

_BINDINGS={name:globals()[name] for name in ('triangular_center_error','transpose_action','dot','add','scale','divide','rounded')}
_CODES={name:value.__code__ for name,value in _BINDINGS.items()}
