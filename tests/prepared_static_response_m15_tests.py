from prepared_static_response_m15_relation_limit import *

def test_closed_form_signed_load_counterexamples():
    positive=counterexample(1);negative=counterexample(-1)
    assert positive['adversarial_output']==-negative['adversarial_output']
    assert positive['output_error']>positive['output_target']

def test_exact_and_underflow_controls():
    assert all(controls().values())

def test_counterexample_does_not_claim_native_schedule_equivalence():
    # Sequential scalar substitution on these same values is exactly zero
    # in the output: it is a different statement from relation admission.
    M=2.**20;b1=1.;x1=b1/1.;x0=(0.-M*x1)/1.
    assert x0+M*x1==0.
    assert counterexample()['actual_native_result_not_claimed']
