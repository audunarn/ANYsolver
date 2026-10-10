"""Prepared invariant stages for exact planar homogeneous qualified Q4 recovery.

The per-case expressions follow e4_pl_element._recover_planar_mixed_fields and
compute_stresses in their original order. No transform/material/station map is
collapsed, and cases do not become columns in a reassociated matrix multiply.
"""
from dataclasses import dataclass
from types import MappingProxyType
import copy
import types
import numpy as np
from . import e4_pl_element as _native
from .boundary import _callable_authority, _callable_authority_matches
from .static_batch import _class_state
from .prepared_static_loads import PreparedStaticCapabilityError
from anymaterial import IsotropicMaterial

@dataclass(frozen=True)
class PreparedQ4Stages:
    transform: np.ndarray
    solution: np.ndarray
    stationary: np.ndarray
    coupling: np.ndarray
    station_fields: tuple
    membrane_map: np.ndarray
    curvature_map: np.ndarray
    shear_map: np.ndarray
    thickness: float
    constants: object
    implementation: str = 'prepared_q4_native_stages_v1'


def _frozen_layout(value):
    array = np.asarray(value)
    if not (array.flags.c_contiguous or array.flags.f_contiguous):
        raise PreparedStaticCapabilityError('prepared Q4 invariant has an unsupported strided layout')
    order = 'F' if array.flags.f_contiguous and not array.flags.c_contiguous else 'C'
    return np.frombuffer(array.tobytes(order=order), dtype=array.dtype).reshape(array.shape, order=order)


def compile_q4_stages(element, mesh, material):
    require_q4_kernel_authority()
    if type(element) is not _native.QualifiedE4PLShellElement:
        return None, 'not_exact_qualified_q4'
    if element.shell_section is not None:
        return None, 'generalized_section'
    if type(material) is not IsotropicMaterial:
        return None, 'nonisotropic_material'
    if getattr(material, 'hill_yield', None) is not None:
        return None, 'hill_material'
    if any(name.startswith('initial_') and value is not None for name, value in vars(element).items()):
        return None, 'initial_field_inputs'
    coordinates = element.get_node_coordinates(mesh)
    frame, local, warpage = _native.equation7_frame(coordinates)
    if warpage > element.planar_tolerance:
        return None, 'warped_geometry'
    c = _native._coefficients(local)
    determinants = [c['jc'], *(_native._jacobian(c, r, s)[4] for r, s in _native._GAUSS)]
    if min(determinants) <= 1e-12 * _native._local_jacobian_scale(local):
        raise PreparedStaticCapabilityError('prepared Q4 has a nonpositive native Jacobian')
    constitutive = element._constitutive_and_drill_stiffness(material, frame)[0]
    stationary, coupling, _gram = _native._stationary_blocks(local, c, constitutive)
    solution, _certification = _native._solve_stationary_system(stationary, coupling)
    stations = []
    for r, s in _native._GAUSS:
        sigma, epsilon = _native._source_fields(c, float(r), float(s))
        stations.append(tuple(_frozen_layout(value) for value in
            (_native._compatible(local, c, float(r), float(s)), epsilon, sigma)))
    _physical_frame, membrane, curvature, shear, _sign = element._physical_director_context(frame)
    zero_record = element.compute_stresses(mesh, np.zeros(24), material, return_global=False)
    # Only constant metadata/director survives; numeric response fields are made
    # by the canonical staged expressions below for every physical case.
    response_names = {'membrane_strain', 'curvature', 'transverse_shear_strain',
        'compatible_membrane_strain', 'compatible_curvature', 'compatible_transverse_shear_strain',
        'membrane_resultants', 'bending_resultants', 'transverse_shear_resultants',
        'membrane_xx', 'membrane_yy', 'membrane_xy', 'bending_xx', 'bending_yy', 'bending_xy',
        'shear_xz', 'shear_yz', 'von_mises', 'hill_utilization', 'equivalent_stress'}
    constants = {key: _frozen_layout(value) if isinstance(value, np.ndarray) else copy.deepcopy(value)
                 for key, value in zero_record.items() if key not in response_names}
    return PreparedQ4Stages(_frozen_layout(_native._global_transform(frame)), _frozen_layout(solution),
        _frozen_layout(stationary), _frozen_layout(coupling), tuple(stations),
        _frozen_layout(membrane), _frozen_layout(curvature), _frozen_layout(shear),
        float(element.thickness), tuple(constants.items())), ''


def recover_q4_stages(stages, displacements):
    local = stages.transform.T @ displacements
    parameters = -stages.solution @ local
    stress_parameters = parameters[:14]
    strain_parameters = parameters[14:]
    residual = stages.stationary @ parameters + stages.coupling.T @ local
    physical = np.concatenate(tuple(local[6 * node:6 * node + 5] for node in range(4)))
    compatible = np.zeros((4, 8), dtype=float)
    independent = np.zeros_like(compatible)
    resultants = np.zeros_like(compatible)
    for index, (b, epsilon, sigma) in enumerate(stages.station_fields):
        compatible[index] = b @ physical
        independent[index] = epsilon @ strain_parameters
        resultants[index] = sigma @ stress_parameters
    for values in (local, parameters, residual, compatible, independent, resultants):
        if not np.all(np.isfinite(values)):
            raise ValueError('prepared Q4 mixed recovery produced nonfinite fields')
    independent = np.column_stack((independent[:, :3] @ stages.membrane_map.T,
        independent[:, 3:6] @ stages.curvature_map.T, independent[:, 6:] @ stages.shear_map.T))
    compatible = np.column_stack((compatible[:, :3] @ stages.membrane_map.T,
        compatible[:, 3:6] @ stages.curvature_map.T, compatible[:, 6:] @ stages.shear_map.T))
    resultants = np.column_stack((resultants[:, :3] @ stages.membrane_map.T,
        resultants[:, 3:6] @ stages.curvature_map.T, resultants[:, 6:] @ stages.shear_map.T))
    recovered = {key: value.copy() if isinstance(value, np.ndarray) else copy.deepcopy(value)
                 for key, value in stages.constants}
    for prefix, array in (('', independent), ('compatible_', compatible)):
        recovered[prefix + 'membrane_strain'] = array[:, :3].copy()
        recovered[prefix + 'curvature'] = array[:, 3:6].copy()
        recovered[prefix + 'transverse_shear_strain'] = array[:, 6:].copy()
    recovered.update(membrane_resultants=resultants[:, :3].copy(), bending_resultants=resultants[:, 3:6].copy(),
                     transverse_shear_resultants=resultants[:, 6:].copy())
    thickness = stages.thickness
    membrane = resultants[:, :3] / thickness
    bending = 6.0 * resultants[:, 3:6] / (thickness * thickness)
    transverse = resultants[:, 6:] / thickness
    for prefix, array in (('membrane_', membrane), ('bending_', bending)):
        for index, name in enumerate(('xx', 'yy', 'xy')):
            recovered[prefix + name] = array[:, index].copy()
    recovered['shear_xz'] = transverse[:, 0].copy()
    recovered['shear_yz'] = transverse[:, 1].copy()
    top = membrane + bending
    bottom = membrane - bending
    vm_top = np.sqrt(top[:, 0] ** 2 - top[:, 0] * top[:, 1] + top[:, 1] ** 2
        + 3.0 * (top[:, 2] ** 2 + transverse[:, 0] ** 2 + transverse[:, 1] ** 2))
    vm_bottom = np.sqrt(bottom[:, 0] ** 2 - bottom[:, 0] * bottom[:, 1] + bottom[:, 1] ** 2
        + 3.0 * (bottom[:, 2] ** 2 + transverse[:, 0] ** 2 + transverse[:, 1] ** 2))
    recovered['von_mises'] = np.maximum(vm_top, vm_bottom)
    recovered['hill_utilization'] = np.zeros(4, dtype=float)
    recovered['equivalent_stress'] = recovered['von_mises'].copy()
    for value in recovered.values():
        if isinstance(value, np.ndarray) and not np.all(np.isfinite(value)):
            raise ValueError('prepared Q4 physical recovery produced nonfinite fields')
    return recovered


def recover_q4_stage_columns(stages, displacements):
    """Linear response fields of recover_q4_stages for many displacement columns.

    Used only to probe affine maps at preparation (M21); every field gains a
    trailing column axis. Derived measures and constants are not produced.
    Rounding can differ from the per-vector kernel, which stays canonical.
    """
    columns = np.asarray(displacements, dtype=float)
    count = columns.shape[1]
    local = stages.transform.T @ columns
    parameters = -stages.solution @ local
    stress_parameters = parameters[:14]
    strain_parameters = parameters[14:]
    physical = np.concatenate(tuple(local[6 * node:6 * node + 5] for node in range(4)))
    compatible = np.zeros((4, 8, count))
    independent = np.zeros_like(compatible)
    resultants = np.zeros_like(compatible)
    for index, (b, epsilon, sigma) in enumerate(stages.station_fields):
        compatible[index] = b @ physical
        independent[index] = epsilon @ strain_parameters
        resultants[index] = sigma @ stress_parameters
    def mapped(values):
        return np.concatenate((np.einsum('ij,sjk->sik', stages.membrane_map, values[:, :3]),
                               np.einsum('ij,sjk->sik', stages.curvature_map, values[:, 3:6]),
                               np.einsum('ij,sjk->sik', stages.shear_map, values[:, 6:])), axis=1)
    independent, compatible, resultants = mapped(independent), mapped(compatible), mapped(resultants)
    made = {}
    for prefix, array in (('', independent), ('compatible_', compatible)):
        made[prefix + 'membrane_strain'] = array[:, :3]
        made[prefix + 'curvature'] = array[:, 3:6]
        made[prefix + 'transverse_shear_strain'] = array[:, 6:]
    made.update(membrane_resultants=resultants[:, :3], bending_resultants=resultants[:, 3:6],
                transverse_shear_resultants=resultants[:, 6:])
    thickness = stages.thickness
    membrane = resultants[:, :3] / thickness
    bending = 6.0 * resultants[:, 3:6] / (thickness * thickness)
    transverse = resultants[:, 6:] / thickness
    for prefix, array in (('membrane_', membrane), ('bending_', bending)):
        for index, name in enumerate(('xx', 'yy', 'xy')):
            made[prefix + name] = array[:, index]
    made['shear_xz'] = transverse[:, 0]
    made['shear_yz'] = transverse[:, 1]
    for value in made.values():
        if not np.all(np.isfinite(value)):
            raise ValueError('prepared Q4 column recovery produced nonfinite fields')
    return made


def require_q4_kernel_authority():
    if _class_state(PreparedQ4Stages) != _STAGE_CLASS_FACTS:
        raise PreparedStaticCapabilityError('prepared Q4 stage class authority changed')
    for name, function, authority, bindings in _KERNEL_FACTS:
        if (globals().get(name) is not function or not _callable_authority_matches(function, authority)
                or any(function.__globals__.get(key) is not value for key, value in bindings)):
            raise PreparedStaticCapabilityError('prepared Q4 kernel executable authority changed')

_STAGE_CLASS_FACTS = _class_state(PreparedQ4Stages)
_KERNEL_FACTS = tuple((name, value, _callable_authority(value),
    tuple((key, value.__globals__[key]) for key in value.__code__.co_names if key in value.__globals__))
    for name, value in tuple(globals().items()) if type(value) is types.FunctionType
    and value.__module__ == __name__)
