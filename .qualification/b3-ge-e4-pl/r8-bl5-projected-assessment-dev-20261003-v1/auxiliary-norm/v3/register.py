from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent
scalar=json.loads((root/'scalar.json').read_text());rep=json.loads((root/'representation.json').read_text())
assert scalar['status']=='UNRESOLVED_COARSE_DEVELOPMENT_BOUND'
assert max(rep['physical_L2_normalized_Gram_condition'].values())<=1e4
assert rep['quotient_congruence_relative_difference']<=1e-10
out=dict(status='ELIGIBLE_PHYSICAL_L2_REPRESENTATION_DEV',fixture=scalar['fixture'],
scalar_registration_sha256=hashlib.sha256((root/'scalar.json').read_bytes()).hexdigest(),
representation_sha256=hashlib.sha256((root/'representation.json').read_bytes()).hexdigest(),
original_failed_predicate='recorded-coefficient Gram condition >1e4; unchanged evidence',
physical_L2_basis_scale=[v**-.5 for v in rep['physical_L2_density_mass_diagonal']],
scalar_extremizer=[v for pair in rep['worst_lifting_multiplier_coefficients'] for v in pair],
safe_case_floor=scalar['safe_case_floor'],shell_modes=scalar['reference_preparation'][-1]['modes'],
criteria=dict(reference_error=1e-3,inverse_eigen_symmetry=1e-10,condition_budget=1e4,
beta_absolute_arithmetic_margin=1e-6,variational_ceiling=(1+1e-6)**2),
interpretation='new prospective canonical density basis, not Gram whitening or relaxed criterion; coarse sufficient bound is not policy selection',
limitations=scalar['limitations'])
(root/'physical-registration.json').write_text(json.dumps(out,indent=2)+'\n')
print(out['status'])
