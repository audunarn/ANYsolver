"""Prepared stdlib controls; not executed during branch-domain preparation."""
from decimal import Decimal as D, localcontext


def test_affine_fibre_domain_uses_flow_boundary_not_tangent_errors():
    from scripts.r8_f06_paired_branch_domain_dev import affine_row,candidate_scale
    law=dict(young=100.,yield_stress=2.,hardening=10.)
    row=dict(fibre_id='f',branch='PLASTIC_POSITIVE',algorithmic_modulus=[100./11.,0.])
    with localcontext() as ctx:
        ctx.prec=80
        base={**row,'total_strain':[.03,0.]}
        plus={**row,'total_strain':[.030001,0.]};minus={**row,'total_strain':[.029999,0.]}
        result=affine_row(base,plus,minus,[0.,0.,0.,0.],law)
        assert D(result['strain_margin'])>0 and D(result['two_sided_parameter_radius'])>0
        scale=candidate_scale(D(result['two_sided_parameter_radius']),D('.1'))
        assert 0<scale<1 and D.from_float(scale)*D('.1')<D(result['two_sided_parameter_radius'])


def test_crossing_or_zero_margin_refuses_saved_secant():
    from scripts.r8_f06_paired_branch_domain_dev import affine_row
    law=dict(young=100.,yield_stress=2.,hardening=10.)
    base=dict(fibre_id='f',branch='PLASTIC_POSITIVE',algorithmic_modulus=[1.,0.],total_strain=[.03,0.])
    try:
        affine_row(base,{**base,'branch':'ELASTIC'},base,[0.,0.,0.,0.],law)
    except ValueError:
        pass
    else:
        raise AssertionError('crossing secant accepted')
    at_yield={**base,'total_strain':[.015625,0.]}
    try:
        affine_row(at_yield,at_yield,at_yield,[0.,0.,0.,0.],dict(young=128.,yield_stress=2.,hardening=10.))
    except ValueError:
        pass
    else:
        raise AssertionError('zero-margin smooth branch accepted')


def test_uniform_scale_preserves_all_nonzero_channels():
    from scripts.r8_f06_paired_branch_domain_dev import candidate_scale
    scale=candidate_scale(D('1e-6'),D('1e-4'))
    original=[0.,1e-4,-2e-4,1000.,-30.,4e-5,200.,-.5]
    candidate=[scale*x for x in original]
    assert all((a==0)==(b==0) for a,b in zip(original,candidate))
    assert all(abs(b-scale*a)==0 for a,b in zip(original,candidate))
