from pathlib import Path
import runpy


def test_signed_distributed_public_example(monkeypatch):
    examples=Path(__file__).resolve().parents[1]/'examples'
    monkeypatch.syspath_prepend(str(examples))
    result=runpy.run_path(str(examples/'stiffened_shell_ge_distributed_programme.py'))['workflow']()
    assert result['accepted_positions']==(1.,2.)
    assert result['final_force_N']==(0.,0.,-200.)
    assert result['restart_identical'] and not result['production_qualified']
