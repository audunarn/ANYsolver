"""Independent bounded checks of the classical stability preflight."""

from pathlib import Path
import json
import hashlib
import subprocess
import sys

import numpy as np
import pytest
from scipy import linalg,sparse

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling
import _b3_e4_f03_nm128_stability as stability
import run_b3_e4_f03_nm128_stability as runner
import adjudicate_b3_e4_f03_nm128_stability as adjudicator


def test_p1_mass_and_dual_norm_have_exact_small_mesh_entries():
    mass,dual,info=stability.p1_norm(2)
    expected=np.array([[1/6,1/12,0.],
                       [1/12,1/3,1/12],
                       [0.,1/12,1/6]])
    np.testing.assert_allclose(mass[::3,::3],expected,rtol=0,atol=1e-15)
    np.testing.assert_allclose(mass,np.kron(expected,np.eye(3)),atol=1e-15)
    assert info['dual_min_eigen']>0 and info['mass_orthogonality_error']<1e-12
    np.testing.assert_allclose(dual,dual.T,rtol=0,atol=1e-15)
    oracle_mass,oracle_dual=adjudicator._reference_norm(2)
    np.testing.assert_allclose(mass,oracle_mass,rtol=0,atol=1e-15)
    np.testing.assert_allclose(dual,oracle_dual,rtol=1e-12,atol=1e-15)
    with pytest.raises(ValueError,match='count'):
        stability.p1_norm(129)


@pytest.mark.parametrize('topology',('Q4','CST-CB'))
def test_sparse_supported_schur_matches_bounded_independent_dense_oracle(topology):
    ns=2;ny=4;nb=64;nm=64
    actual=stability.analyze(ns,ny,nb,nm,topology,batch=7)
    assert actual['numerical_checks_pass']
    model=shell.panel(ns,ny,topology)
    ks=shell.stiffness(model)
    kb=beam.assembled_stiffness(nb)
    cs,cb,_=line.coupling(model,nb,nm,'P1')
    k=sparse.block_diag((ks,kb),format='csr')
    c=sparse.hstack((-cs,cb),format='csr')
    free=np.setdiff1d(np.arange(k.shape[0]),
                      np.r_[model.supported,model.dof_count+beam.root_dofs(nb)])
    local=free-model.dof_count
    u=2*nb+1;v=2*(nb+1)
    angular=(local>=u+v)|((local>=u)&(local<u+v)&((local-u)%2==1))
    d=np.where(angular,scaling.U0/scaling.L0,scaling.U0)
    kbar=(sparse.diags(d)@k[free,:][:,free]@sparse.diags(d)).toarray()/scaling.E0
    b=(c[:,free]@sparse.diags(d/scaling.U0)).toarray()
    s=b@linalg.solve(kbar,b.T,assume_a='pos',check_finite=True)
    mass,dual,_=stability.p1_norm(nm)
    values=linalg.eigh(s,dual,eigvals_only=True)
    l2=linalg.eigh(s,mass,eigvals_only=True)
    np.testing.assert_allclose((actual['minimum_generalized_eigen'],
                                actual['maximum_generalized_eigen']),
                               (values[0],values[-1]),rtol=1e-6,atol=1e-9)
    np.testing.assert_allclose((actual['l2_minimum_generalized_eigen'],
                                actual['l2_maximum_generalized_eigen']),
                               (l2[0],l2[-1]),rtol=1e-6,atol=1e-9)
    assert actual['physical_free']==len(free)
    assert actual['multiplier_rows']==195


def test_dimensionless_energy_and_coupling_are_unit_invariant():
    model=shell.panel(2,4,'Q4')
    k=sparse.block_diag((shell.stiffness(model),beam.assembled_stiffness(64)),
                        format='csr')
    cs,cb,_=line.coupling(model,64,64,'P1')
    c=sparse.hstack((-cs,cb),format='csr')
    free=np.setdiff1d(np.arange(k.shape[0]),np.r_[
        model.supported,model.dof_count+beam.root_dofs(64)])
    baseline=scaling.build(k,c,np.zeros(k.shape[0]),free,
                           model.dof_count,64,64,'P1')
    d=baseline.physical_coordinate_scale
    kbar=baseline.matrix[:len(free),:len(free)].toarray()
    b=(c[:,free]@sparse.diags(d/scaling.U0)).toarray()
    # Re-express the physical coordinates in a different displacement unit.
    conversion=np.ones(k.shape[0]);conversion[free]=1000.
    p=sparse.diags(conversion)
    new_k=p@k@p
    new_c=c@p
    new_d=d/conversion[free]
    red=sparse.diags(new_d)
    new_kbar=(red@new_k[free,:][:,free]@red).toarray()/scaling.E0
    new_b=(new_c[:,free]@sparse.diags(new_d/scaling.U0)).toarray()
    np.testing.assert_allclose(new_kbar,kbar,rtol=1e-12,atol=1e-9)
    np.testing.assert_allclose(new_b,b,rtol=1e-12,atol=1e-12)
    linalg.cholesky(kbar,check_finite=True)


def test_unsupported_stability_cases_are_rejected():
    with pytest.raises(ValueError,match='unsupported'):
        stability.analyze(2,4,64,129,'Q4')
    with pytest.raises(ValueError,match='unsupported'):
        stability.analyze(2,4,64,64,'CST')


def test_stability_supervisor_has_exact_four_cases_and_source_identity():
    assert runner.CASES=={'q4-nm64':('Q4',64),'q4-nm128':('Q4',128),
                          'cb-nm64':('CST-CB',64),'cb-nm128':('CST-CB',128)}
    assert len(runner._hashes())==6
    assert all(len(value)==64 for value in runner._hashes().values())
    assert runner.MAX_RSS==8*1024**3 and runner.MAX_SECONDS==900
    assert len(adjudicator._sha(Path(adjudicator.__file__)))==64


def test_supervisor_refuses_unregistered_case_before_creating_evidence(tmp_path):
    output=tmp_path/'unregistered'
    with pytest.raises(ValueError,match='registration'):
        runner._supervise('q4-nm64',output)
    assert not output.exists()


def test_adjudicator_rejects_bad_gate_under_optimized_python():
    command=[sys.executable,'-O','-c',
             'import sys; sys.path.insert(0, sys.argv[1]); '
             'import adjudicate_b3_e4_f03_nm128_stability as a; '
             "a._require(False, 'rejected gate')",
             str(Path(adjudicator.__file__).parent)]
    result=subprocess.run(command,capture_output=True,text=True)
    assert result.returncode!=0 and 'rejected gate' in result.stderr


@pytest.mark.parametrize('malformed',('[]','42',
                                      '{"phase":"identity","rss_bytes":"2"}'))
def test_supervisor_preserves_failure_when_phase_json_is_not_a_record(
        monkeypatch,tmp_path,malformed):
    class Completed:
        stdout='frozen\n'
    def git_command(*args,**kwargs):
        return Completed() if args[0][-2:]==('rev-parse','HEAD') else type(
            'Clean',(),{'stdout':''})()
    class Child:
        pid=1234
        def __init__(self,command,*,stdout,stderr,**kwargs):
            stdout.write((malformed+'\n').encode())
        def poll(self):
            return 0
        def wait(self):
            return 0
    monkeypatch.setattr(runner.subprocess,'run',git_command)
    monkeypatch.setattr(runner.subprocess,'Popen',Child)
    monkeypatch.setattr(runner.psutil,'Process',lambda pid: object())
    out=tmp_path/'failure'
    registered=tmp_path/'registration.json'
    path=Path(runner.__file__).resolve()
    commands=[[sys.executable,str(path),'--case',name,'--output',
               str((tmp_path/name if name!='q4-nm64' else out).resolve()),
               '--registration',str(registered.resolve())] for name in runner.CASES]
    registered.write_text(json.dumps(dict(
        execution_head='frozen',cases=list(runner.CASES),
        runner_source_hashes=runner._hashes(),runner_path=str(path),
        python_executable=sys.executable,commands=commands,
        limits=dict(max_rss_bytes=runner.MAX_RSS,max_seconds=runner.MAX_SECONDS),
        adjudicator_sha256=adjudicator._sha(Path(adjudicator.__file__)),
        dependency_file_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest()},
        threads=dict.fromkeys(('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS',
                               'MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'),'1'))))
    assert runner._supervise('q4-nm64',out,registered)==1
    result=json.loads((out/'result.json').read_text())
    assert result['reason']=='identity_or_phase_failure'
    assert result['malformed_phase_lines']==[1]
