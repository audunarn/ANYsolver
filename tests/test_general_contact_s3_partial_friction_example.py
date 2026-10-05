"""The standalone example uses the ordinary solver and emits a real checkpoint."""
import importlib.util
import json
from pathlib import Path
import sys


def test_partial_example_press_cli_checkpoint(monkeypatch,tmp_path,capsys):
    path=Path(__file__).resolve().parents[1]/'examples/general_contact_s3_partial_friction.py'
    spec=importlib.util.spec_from_file_location('partial_friction_example',path)
    example=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(example)
    checkpoint=tmp_path/'press.json'
    monkeypatch.setattr(sys,'argv',[str(path),'--max-load-factor','.2',
                                  '--checkpoint-output',str(checkpoint)])
    example.main()
    output=json.loads(capsys.readouterr().out)
    saved=json.loads(checkpoint.read_text())
    assert output['status']=='completed'
    assert output['accepted_steps']==saved['path_state']['accepted_step']==1
    assert output['profile']=='S3_PARTIAL_MATERIAL_REPLAY_STATIC_DEV_V1'
    assert len(saved['path_state']['friction_state']['frames'])==1
    assert output['cumulative_dissipation_j']==0
    assert max(abs(value) for value in output['reactions_n'][0])>0
