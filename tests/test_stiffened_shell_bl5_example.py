"""Public headless BL5 construction and complete staged lifecycle example."""
from examples.stiffened_shell_bl5_staged import workflow


def test_public_bl5_staged_example(record_property):
    result = workflow()
    assert result['status'] == 'completed' and result['restart_identical']
    assert result['shell_elements'] > 1 and result['beam_elements'] > 1
    assert result['final_position'] == 2. and result['line_work_samples'] > 0
    record_property('bl5_example',result)
