"""Exploratory CPS/U1 four-sample collocation deck, not F03 acceptance.

Finite beam-node equations approximate the reference trace; they are not the
continuous exact-multiplier line law. This first route tests execution and
basic displacement recovery only, preserving all raw outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

import numpy as np

from probe_b3_ge_e4_pl_g0_f03_ccx_u1_smoke import EXPECTED_EXE_SHA256


OFFSETS = ((-.2,-.23),(.2,-.23),(.2,.23),(-.2,.23))
YAW_DENOMINATOR = 4*(.2**2+.23**2)


def _host(x, y, n_shell, topology):
    nx = 2*n_shell
    dx = 1/n_shell
    i = max(0, min(nx-1, int(np.ceil((x+.5)/dx))-1))
    j = max(0, min(1, int(np.ceil((y+.5)/.5))-1))
    xi = (x-(-.5+i*dx))/dx
    eta = (y-(-.5+j*.5))/.5
    if not (-1e-12 <= xi <= 1+1e-12 and -1e-12 <= eta <= 1+1e-12):
        raise ValueError('four-sample host outside panel')
    a = 1+j*(nx+1)+i
    b, d = a+1, a+nx+1
    c = d+1
    if topology == 'Q4':
        return ((a,b,c,d), ((1-xi)*(1-eta),xi*(1-eta),xi*eta,(1-xi)*eta))
    if eta <= xi:
        return ((a,b,c),(1-xi,xi-eta,eta))
    return ((a,c,d),(1-eta,xi,eta-xi))


def _trace(s, n_shell, topology):
    rows = ({}, {}, {})
    for ox, y in OFFSETS:
        ids, weights = _host(s+ox, y, n_shell, topology)
        for node, weight in zip(ids, weights):
            for row, dof, coefficient in ((0,1,weight/4), (1,2,weight/4),
                                          (2,1,-y*weight/YAW_DENOMINATOR),
                                          (2,2,ox*weight/YAW_DENOMINATOR)):
                key = (node,dof)
                rows[row][key] = rows[row].get(key,0.)+coefficient
    # Independent rigid translation/rotation patch identities, including
    # physical lever-arm y motion at each beam station s.
    positions = lambda node: (-.5+((node-1)%(2*n_shell+1))/n_shell,
                              -.5+((node-1)//(2*n_shell+1))*.5)
    evaluate = lambda row, ux, uy: sum(coefficient*(ux(*positions(node)) if dof == 1
                                                  else uy(*positions(node)))
                                      for (node,dof),coefficient in row.items())
    if max(abs(evaluate(rows[0],lambda x,y:1.,lambda x,y:0.)-1),
           abs(evaluate(rows[1],lambda x,y:0.,lambda x,y:1.)-1),
           abs(evaluate(rows[0],lambda x,y:-y,lambda x,y:x)),
           abs(evaluate(rows[1],lambda x,y:-y,lambda x,y:x)-s),
           abs(evaluate(rows[2],lambda x,y:-y,lambda x,y:x)-1)) > 2e-13:
        raise AssertionError('four-sample physical rigid-motion patch failed')
    return rows


def deck(topology, n_shell, n_beam, load_kind):
    nx = 2*n_shell
    shell_count = 3*(nx+1)
    nodes = [(1+j*(nx+1)+i, -.5+i/n_shell, -.5+j*.5, 0.)
             for j in range(3) for i in range(nx+1)]
    nodes += [(shell_count+1+i, i/n_beam, 0., 0.) for i in range(n_beam+1)]
    shell_elements = []
    for j in range(2):
        for i in range(nx):
            a = 1+j*(nx+1)+i
            b,d = a+1,a+nx+1
            c = d+1
            shell_elements += [(a,b,c,d)] if topology == 'Q4' else [(a,b,c),(a,c,d)]
    beam_elements = [(shell_count+1+i,shell_count+2+i) for i in range(n_beam)]
    lines = ['** Experimental four-sample collocation: NOT a qualified F03 reference',
             '*NODE,NSET=Nall']
    lines += [','.join((str(node),*(f'{v:.17g}' for v in (x,y,z)))) for node,x,y,z in nodes]
    lines += [f'*ELEMENT,TYPE={"CPS4" if topology == "Q4" else "CPS3"},ELSET=Eplate']
    lines += [','.join((str(i),*(str(node) for node in element)))
              for i,element in enumerate(shell_elements,1)]
    lines += ['*ELEMENT,TYPE=U1,ELSET=Ebeam']
    lines += [','.join((str(i),*(str(node) for node in element)))
              for i,element in enumerate(beam_elements,len(shell_elements)+1)]
    lines += ['*USER ELEMENT,TYPE=U1,NODES=2,INTEGRATION POINTS=2,MAXDOF=6',
              '*NSET,NSET=Sends']
    lines += [','.join(str(1+j*(nx+1)+i) for j in range(3) for i in (0,nx))]
    lines += ['*NSET,NSET=Bfree',
              ','.join(str(shell_count+1+i) for i in range(1,n_beam+1)),
              '*BOUNDARY', 'Sends,1,2', f'{shell_count+1},1,6', 'Bfree,3,5',
              '*MATERIAL,NAME=Steel', '*ELASTIC', '210.e9,.3',
              '*SOLID SECTION,ELSET=Eplate,MATERIAL=Steel', '.07',
              '*BEAM SECTION,ELSET=Ebeam,MATERIAL=Steel,SECTION=GENERAL',
              '.01,8.333333333333333e-6,0.,8.333333333333333e-6,.8', '0.,1.,0.']
    constraint_count = 0
    for i in range(1,n_beam+1):
        beam_node = shell_count+1+i
        for row, beam_dof in zip(_trace(i/n_beam,n_shell,topology),(1,2,6)):
            terms = [(beam_node,beam_dof,1.)]
            terms += [(node,dof,-coefficient) for (node,dof),coefficient in sorted(row.items())
                      if abs(coefficient) > 1e-15]
            lines += ['*EQUATION',str(len(terms))]
            for start in range(0,len(terms),4):
                lines.append(','.join(f'{node},{dof},{coefficient:.17g}'
                                      for node,dof,coefficient in terms[start:start+4]))
            constraint_count += 1
    roots,weights=np.polynomial.legendre.leggauss(8)
    load=np.zeros(n_beam+1)
    for i in range(n_beam):
        a,b=i/n_beam,(i+1)/n_beam
        for xi,wi in zip(roots,weights):
            s=(a+b)/2+(b-a)*xi/2
            density=(1e6*(1+.25*np.cos(2*np.pi*s)) if load_kind == 'smooth'
                     else 1e6*np.sin(2*np.pi*s))
            load[i] += (b-a)*wi/2*density*(b-s)/(b-a)
            load[i+1] += (b-a)*wi/2*density*(s-a)/(b-a)
    lines += ['*STEP','*STATIC','*CLOAD']
    lines += [f'{shell_count+1+i},2,{value:.17g}' for i,value in enumerate(load)
              if abs(value)>1e-8]
    lines += ['*NODE PRINT,NSET=Nall','U','*END STEP']
    metadata=dict(topology=topology,n_shell=n_shell,n_beam=n_beam,
                  shell_nodes=shell_count,shell_elements=len(shell_elements),
                  beam_nodes=n_beam+1,beam_elements=n_beam,
                  constraints=constraint_count,load_kind=load_kind,
                  root_station_tied=False,
                  constraint_stations=[i/n_beam for i in range(1,n_beam+1)],
                  nodal_load_sum_n=float(sum(load)),
                  beam_node_ids=[shell_count+1+i for i in range(n_beam+1)])
    return '\n'.join(lines)+'\n',metadata


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable',required=True,type=Path)
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--topology',choices=('Q4','S3-V2D'),required=True)
    parser.add_argument('--n-shell',type=int,required=True)
    parser.add_argument('--n-beam',type=int,required=True)
    parser.add_argument('--load',choices=('smooth','sine'),required=True)
    args=parser.parse_args()
    if not 1 <= args.n_shell <= 64 or not 2 <= args.n_beam <= 64:
        raise ValueError('bounded exploratory mesh inventory required')
    executable=args.executable.resolve(strict=True)
    identity=hashlib.sha256(executable.read_bytes()).hexdigest()
    if identity != EXPECTED_EXE_SHA256:
        raise ValueError('CalculiX executable identity mismatch')
    content,metadata=deck(args.topology,args.n_shell,args.n_beam,args.load)
    args.root.mkdir(parents=True,exist_ok=False)
    (args.root/'coupled.inp').write_text(content,encoding='ascii')
    env=os.environ.copy()
    env['OMP_NUM_THREADS']='1'
    try:
        process=subprocess.run([str(executable),'-i','coupled'],cwd=args.root,
                               env=env,capture_output=True,text=True,timeout=120,check=False)
        (args.root/'stdout.log').write_text(process.stdout,encoding='utf-8')
        (args.root/'stderr.log').write_text(process.stderr,encoding='utf-8')
        status=dict(exit_code=process.returncode,failure=None)
    except subprocess.TimeoutExpired as exc:
        (args.root/'stdout.log').write_bytes(exc.stdout or b'')
        (args.root/'stderr.log').write_bytes(exc.stderr or b'')
        status=dict(exit_code=None,failure='TIMEOUT_120_SECONDS')
    result=dict(purpose='UNREGISTERED_F03_COUPLED_EXECUTION_FEASIBILITY',
                executable_sha256=identity,model=metadata,**status,
                files=sorted(path.name for path in args.root.iterdir()))
    (args.root/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',
                                         encoding='utf-8')
    print(json.dumps(result,sort_keys=True))
    return 0 if status['exit_code']==0 else 1


if __name__=='__main__':
    raise SystemExit(main())
