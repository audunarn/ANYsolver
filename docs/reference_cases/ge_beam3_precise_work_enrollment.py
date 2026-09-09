"""Explicit new equilibrium enrollment; never convert an old accepted chain."""
from hashlib import sha256
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes


def enroll(model,program,source,expected_sha256):
    if type(source) is not bytes or sha256(source).hexdigest()!=expected_sha256:
        raise ValueError('original checkpoint external identity')
    original=strict_bytes(source)
    from anysolver import _ge_beam3_elastic_seed_continuation as owner
    from anysolver._ge_beam3_native_generalized_program import retained_model_identity
    from anysolver._ge_beam3_precise_geometric_work import POLICY
    from anysolver._ge_beam3_p5_seeded.core import canonical,sha
    if (original['schema']!=owner.SCHEMA or not original['records']
            or original['checkpoint_sha256']!=sha({k:v for k,v in original.items() if k!='checkpoint_sha256'})
            or original['physical_loading_path_from_rest'] is not False or original['elastic_only'] is not True):
        raise ValueError('original elastic chain schema/hash')
    elements=sorted(model.mesh.elements.items());row=original['records'][-1]
    if any(e.operator.arithmetic_policy!=POLICY for _,e in elements):raise ValueError('explicit precise candidate required')
    virgin=canonical(tuple(e.operator.cell.virgin() for _,e in elements))
    if canonical(row['histories'])!=virgin or canonical(row['origins'])!=virgin:
        raise ValueError('new equilibrium enrollment requires virgin source histories')
    old=original['program']
    if (old['control_node']!=program.control_node or canonical(old['direction'])!=canonical(program.direction)
            or canonical(old['nodal_forces'])!=canonical(program.nodal_forces)):
        raise ValueError('same physical control and dead load required')
    seed=canonical(dict(schema=owner.SEED_SCHEMA,model_sha256=retained_model_identity(model),
        operators=[e.operator.identity for _,e in elements],control_node=program.control_node,
        direction=program.direction,nodal_forces=program.nodal_forces,mechanical=row['mechanical'],
        parameter=row['parameter'],displacement=row['displacement_target'],source_sha256=expected_sha256))
    # Context actually checks equilibrium and a full correction before issuance.
    context=owner.Context(model,program,seed,expected_seed_sha256=sha256(seed).hexdigest())
    return context,seed
