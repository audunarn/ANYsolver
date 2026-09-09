"""Read-only source integration audit, NOT a scientific qualification runner.

No production module is imported or executed. Passing checks establish only
the explicitly inspected routing/metadata boundary, never numerical validity.
"""
import argparse
import ast
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path


SOURCES = {
    'factory': 'src/anysolver/elements.py',
    'facade': 'src/anysolver/ge_beam3_element.py',
    'facade_state': 'src/anysolver/ge_beam3_state.py',
    'native': 'src/anysolver/_ge_beam3_native_generalized_element.py',
    'modal': 'src/anysolver/_ge_beam3_native_generalized_modal.py',
    'retained': 'src/anysolver/_ge_beam3_retained_generalized_state.py',
    'arc': 'src/anysolver/_ge_beam3_retained_arc.py',
}
EVIDENCE = {
    'lifecycle': (
        'docs/reference_cases/ge_beam3_plastic_arc_lifecycle_status.json',
        '95367C3171379A069330B0425577CA01B7EC189354C834E85276F1892B449C9E'),
    'onset': (
        'docs/reference_cases/ge_beam3_fine_onset_status.json',
        'F2E689B5E5203DC213C27AFA2475D23A6E23C92BDE227C3C457153A14E809477'),
}
GAPS = (
    'current_curved_core_public_integration',
    'actual_spatial_postbuckled_branch_validation',
    'complete_section_load_solver_restart_parity',
    'production_dynamic_internal_coordinate_assembly',
    'complete_environment_and_installed_wheel_qualification',
    'independent_review',
    'objective_eccentric_curved_beam_shell_connections',
)


class BoundaryError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise BoundaryError(message)


def named(scope, kind, name):
    found = [n for n in scope.body if isinstance(n, kind) and n.name == name]
    require(len(found) == 1, f'one explicit declaration required: {name}')
    return found[0]


def assigned(scope, name):
    found = [n.value for n in scope.body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    require(len(found) == 1, f'one explicit assignment required: {name}')
    return found[0]


def literal(scope, name):
    try:
        return ast.literal_eval(assigned(scope, name))
    except (TypeError, ValueError) as error:
        raise BoundaryError(f'literal boundary required: {name}') from error


def strict_json(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result

    def nonfinite(value):
        raise BoundaryError(f'nonfinite JSON: {value}')

    def finite_float(value):
        result = float(value)
        require(isfinite(result), 'nonfinite JSON number')
        return result

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite,
                        parse_float=finite_float)
    # Status hash authority is checked separately; no reserialization of old evidence.
    require(type(result) is dict, 'status must be an object')
    return result


def audit(source_bytes, evidence_bytes):
    require(set(source_bytes) == set(SOURCES), 'complete source inventory required')
    require(set(evidence_bytes) == set(EVIDENCE), 'complete evidence inventory required')
    trees = {key: ast.parse(raw.decode('utf-8-sig')) for key, raw in source_bytes.items()}
    factory = named(trees['factory'], ast.FunctionDef, 'create_element')
    matches = [n for n in factory.body if isinstance(n, ast.If)
               and ast.dump(n.test) == ast.dump(ast.parse('normalized_type == "ge-beam3"', mode='eval').body)]
    require(len(matches) == 1, 'exact ge-beam3 factory route required')
    route = matches[0]
    imports = [n for n in route.body if isinstance(n, ast.ImportFrom)]
    require(len(imports) == 1 and imports[0].level == 1
            and imports[0].module == 'ge_beam3_element'
            and [(n.name, n.asname) for n in imports[0].names]
            == [('GeometricallyExactBeam3D3NElement', None)], 'old facade factory target changed')
    returns = [n for n in route.body if isinstance(n, ast.Return)]
    require(len(returns) == 1 and isinstance(returns[0].value, ast.Call)
            and isinstance(returns[0].value.func, ast.Name)
            and returns[0].value.func.id == 'GeometricallyExactBeam3D3NElement',
            'old facade constructor changed')
    facade = named(trees['facade'], ast.ClassDef, 'GeometricallyExactBeam3D3NElement')
    gaps = named(facade, ast.FunctionDef, 'capability_gaps')
    declared_gaps = {n.value for n in ast.walk(gaps) if isinstance(n, ast.Constant) and type(n.value) is str}
    require({'curved_reference', 'history_bearing_sections', 'beam_shell_connection',
             'current_state_modal', 'current_state_buckling'} <= declared_gaps,
            'old facade capability scope changed')
    public_id = literal(trees['facade_state'], 'GE_BEAM3_QUALIFIED_FORMULATION_ID')
    require(public_id == 'GE_BEAM3_DC_MIXED_K1_MACRO_V2', 'old facade identity changed')

    native = named(trees['native'], ast.ClassDef, 'NativeGeneralizedStaticElement')
    require(literal(native, 'production_qualified') is False, 'private native core activated')
    require(type(literal(native, 'num_nodes')) is int and literal(native, 'num_nodes') == 3
            and type(literal(native, 'dofs_per_node')) is int and literal(native, 'dofs_per_node') == 6,
            'native external topology changed')
    mass = assigned(native, 'compute_mass_matrix')
    require(isinstance(mass, ast.Name) and mass.id == '_unsupported',
            'static adapter mass route must remain unsupported')
    unsupported = named(native, ast.FunctionDef, '_unsupported')
    require(len(unsupported.body) == 1 and isinstance(unsupported.body[0], ast.Raise),
            'unsupported native routes must raise')
    native_id = literal(trees['native'], 'FORMULATION')
    native_schema = literal(trees['native'], 'SCHEMA')
    retained_schema = literal(trees['retained'], 'SCHEMA')
    arc_schema = literal(trees['arc'], 'SCHEMA')
    require(len({public_id, native_id, native_schema, retained_schema, arc_schema}) == 5,
            'distinct formulation/state owners required')
    require(literal(trees['modal'], 'MASS_POLICY') ==
            'CENTERED_LIFTED_CELL_INERTIA_24_POINT_NO_STATIC_REDUCTION',
            'physical cell inertia policy changed')
    require(literal(trees['modal'], 'MATERIAL_POLICY') ==
            'COMMITTED_HISTORY_ELASTIC_INTERIOR_NO_ADVANCE', 'modal history policy changed')

    statuses = {}
    for role, raw in evidence_bytes.items():
        require(sha256(raw).hexdigest().upper() == EVIDENCE[role][1], f'{role} status hash changed')
        status = strict_json(raw)
        require(status.get('production_qualified') is False and status.get('independent_review') == 'PENDING',
                f'{role} private evidence boundary changed')
        statuses[role] = status
    require(statuses['onset'].get('postbuckled_branch_qualified') is False,
            'onset cannot authorize a spatial postbuckled branch')
    require(statuses['lifecycle'].get('explicit_mid_history_reversal_qualified') is False,
            'lifecycle cannot authorize arbitrary arc reversal')

    inventory = []
    for role, raw in sorted({**source_bytes, **evidence_bytes}.items()):
        path = SOURCES[role] if role in SOURCES else EVIDENCE[role][0]
        inventory.append(dict(role=role, path=path, bytes=len(raw), sha256=sha256(raw).hexdigest()))
    return dict(schema='GE_BEAM3_INTEGRATION_BOUNDARY_AUDIT_V1',
                disposition='SOURCE_BOUNDARY_CHECKED_NOT_QUALIFICATION',
                scientific_execution=False, independent_review=False,
                production_activation_authorized=False,
                existing_public_formulation=public_id, private_native_formulation=native_id,
                native_external_dofs=18, state_schemas=[native_schema, retained_schema, arc_schema],
                mass_policy=literal(trees['modal'], 'MASS_POLICY'),
                unresolved_programme=list(GAPS), inventory=inventory,
                scope='Direct source declarations and two status hashes only; not full call-graph, archive or mechanics validation.')


def inspect_repository(root):
    root = Path(root)
    return audit({key: (root/path).read_bytes() for key, path in SOURCES.items()},
                 {key: (root/data[0]).read_bytes() for key, data in EVIDENCE.items()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_repository(args.repo), sort_keys=True, allow_nan=False, indent=2))
