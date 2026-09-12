"""Runner unit/failure checks, separate from all G3b mechanical inventories."""
from hashlib import sha256
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("g3b_runner",ROOT/"scripts/confirm_ge_beam3_g3b.py")
c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)


def test_missing_lease_rejects_before_imports(tmp_path):
    path=tmp_path/"lease.json"; path.write_bytes(b'{}\n')
    with pytest.raises(ValueError,match="hash"): c.validate_lease(path,"0"*64)
    with pytest.raises(ValueError,match="schema"):
        c.validate_lease(path,sha256(path.read_bytes()).hexdigest())
    assert not (tmp_path/"attempt.json").exists()


def test_publication_is_exclusive_and_failure_leaves_no_aggregate(tmp_path):
    target=tmp_path/"aggregate.json"
    with patch.object(c.os,"link",side_effect=OSError("injected")):
        with pytest.raises(OSError): c.publish(target,dict(status="fixture"))
    assert not target.exists() and (tmp_path/"aggregate.json.pending").exists()
    other=tmp_path/"accepted.json"; c.publish(other,dict(status="fixture")); before=other.read_bytes()
    with pytest.raises(FileExistsError): c.publish(other,dict(status="overwrite"))
    assert other.read_bytes()==before


@pytest.mark.parametrize("kind",("timeout","wave","memory","inactivity","crash"))
def test_resource_failure_terminates_tree_and_never_publishes(tmp_path,kind):
    class Job:
        terminated=False; closed=False
        def launch(self,command,**kwargs):
            assert all(kwargs["env"][key]=="1" for key in c.THREADS)
            assert "-I" in command and "-S" in command and "-B" in command
            return SimpleNamespace(poll=lambda:1 if kind=="crash" else None,
                wait=lambda timeout:None,returncode=1)
        def accounting(self):
            return (0,0 if self.terminated or kind=="crash" else 1,
                    24*1024**3+1 if kind=="memory" else 1000)
        def terminate(self): self.terminated=True
        def close(self): self.closed=True
    job=Job(); times=iter([0,1,122,123] if kind=="inactivity" else [0,601 if kind=="timeout" else 1,602])
    with patch.object(c,"process_module",return_value=SimpleNamespace(_ProcessJob=lambda n:job)), \
         patch.object(c.time,"monotonic",side_effect=lambda:next(times)),patch.object(c.time,"sleep"):
        with pytest.raises(ValueError): c.run_child(tmp_path,dict(disposable=True),0 if kind=="wave" else 1800)
    assert job.closed and (job.terminated or kind=="crash")
    assert not (tmp_path/"aggregate.json").exists()


def test_progress_observes_completed_output_not_intention():
    import io
    target=io.StringIO(); s=c.ProgressStream(target)
    s.write("G3B CHECK"); assert not s.phases
    s.write("POINT assembly\n"); assert s.phases=={"assembly"}
    s.write("planned restart\n"); assert s.phases=={"assembly"}
    assert target.getvalue()=="G3B CHECKPOINT assembly\nplanned restart\n"


@pytest.mark.parametrize("kind",("unknown","changed"))
def test_import_guard_rejects_before_loader(tmp_path,kind):
    (tmp_path/"site").mkdir()
    source=tmp_path/"site/module.py"; source.write_text("raise AssertionError('must not execute')")
    expected=c.environment.digest(source)
    frozen=dict(files={"module.py":expected} if kind=="changed" else {},runtime={})
    lease=dict(environment=str(tmp_path/"environment.json"),inputs=dict(files={}))
    if kind=="changed": source.write_text("raise AssertionError('changed, must not execute')")
    with patch.object(c.importlib.machinery.PathFinder,"find_spec",return_value=SimpleNamespace(origin=str(source))):
        guard=c.install_import_guard(lease,frozen)
        try:
            with pytest.raises(ImportError): guard.find_spec("module")
        finally: sys.meta_path.remove(guard)


def test_unknown_import_origin_rejected(tmp_path):
    fake=tmp_path/"alien.py"; fake.write_text("")
    sys.modules["g3b_unbound_fixture"]=SimpleNamespace(__file__=str(fake))
    try:
        with patch.object(c.environment,"git",return_value=b""):
            with pytest.raises(ValueError,match="unbound"): c.import_origins(dict(files={},runtime={}),tmp_path/"environment.json")
    finally: del sys.modules["g3b_unbound_fixture"]


@pytest.mark.parametrize("mutation",(None,"packet","identity","process"))
def test_coordinator_two_cycles_or_diagnostic_only(tmp_path,monkeypatch,mutation):
    inv=c.authority.inventory(c.authority.INVENTORY.read_bytes().replace(b"\r\n",b"\n"))
    frozen=dict(candidate="a"*40,tree="b"*40,files={},git={})
    out=tmp_path/"run"; calls=[]
    monkeypatch.setattr(c,"isolated_startup",lambda:True)
    monkeypatch.setattr(c.sys,"pycache_prefix",str(tmp_path/"cache"))
    monkeypatch.setattr(c,"inputs",lambda _:dict(frozen,tree="changed") if mutation=="identity" and len(calls)>7 else frozen)
    monkeypatch.setattr(c.environment,"verify",lambda *a: {})
    def child(directory,lease,deadline):
        calls.append((lease["cycle"],lease["lane"]))
        if mutation=="process": raise ValueError("injected process failure")
    monkeypatch.setattr(c,"run_child",child)
    monkeypatch.setattr(c,"scientific",lambda directory,row:c.authority.canonical(dict(lane=row["lane"],
        mutated=mutation=="packet" and directory.parent.name=="cycle-2")))
    monkeypatch.setattr(c.sys,"argv",["confirmation","--rehearse","--candidate","a"*40,
        "--environment",str(tmp_path/"environment.json"),"--environment-sha256","c"*64,"--output",str(out)])
    if mutation:
        with pytest.raises(ValueError): c.main()
        assert (out/"failure.json").exists() and not (out/"rehearsal.json").exists()
    else:
        assert c.main()==0
        body=c.authority.strict((out/"rehearsal.json").read_bytes())
        assert body["terminal"]=="REHEARSAL_ONLY" and body["cycles"]==2
        assert [row["lane"] for row in body["lanes"]]==list(c.authority.LANES)
    assert len(calls)==len(set(calls))  # no retry of a lane/cycle
    assert not (out/"aggregate.json").exists()


def test_formal_review_missing_precedes_output(tmp_path,monkeypatch):
    monkeypatch.setattr(c,"isolated_startup",lambda:True)
    monkeypatch.setattr(c.sys,"pycache_prefix",str(tmp_path/"cache"))
    monkeypatch.setattr(c,"inputs",lambda _:dict(tree="b"*40))
    monkeypatch.setattr(c.environment,"verify",lambda *a: {})
    output=tmp_path/"run"
    monkeypatch.setattr(c.sys,"argv",["confirmation","--candidate","a"*40,"--environment",str(tmp_path/"env"),
        "--environment-sha256","c"*64,"--output",str(output)])
    with pytest.raises(ValueError,match="independent review"): c.main()
    assert not output.exists()
