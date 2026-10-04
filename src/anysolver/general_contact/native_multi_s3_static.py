"""Separate retained-native owner for explicit multiple physical S3 interiors.

All native internal unknowns and complete structural/contact blocks are retained.
This does not widen the original single-native/single-S3 profile.
"""
from dataclasses import dataclass, replace
from hashlib import sha256
from math import isfinite

import numpy as np
from scipy import sparse
from anymaterial import IsotropicMaterial
from anysolver._ge_beam3_native_analysis import NativeBeamAnalysis
from anysolver._ge_beam3_native_definition import NativeBeamDefinition
from anysolver._ge_beam3_native_generalized_element import NativeGeneralizedStaticElement
from anysolver._ge_beam3_retained_nodal_loading import Context, Program
from anysolver._ge_beam3_generalized_static_boundary import spatial_jacobian
from anysolver._ge_beam3_p5_seeded.core import canonical, sha
from anysolver._ge_beam3_p5_seeded.codec import MAX_BYTES, _load
from anysolver.e4_pl_s3_v2d_element import NativeParityE4PLS3V2DShellElement
from anysolver.fe_core import FEModel
from .native_retained_line_s3_work import NativeRetainedLineS3Work
from .native_material_s3 import NativeRetainedMaterialS3Work
from .native_retained_s3_static import NativeRetainedRoundS3Analysis
from .native_retained_station import _readonly
from .s3_skin_work import S3SkinWorkAdapter
from .native_s3_swept import native_s3_swept_admissible
from .native_shell_static_driver import solve_native_shell

PROFILE = 'NATIVE_B3_GE_MULTIPLE_ELASTIC_S3_INTERIORS_STATIC_DEV_V1'
MATERIAL_PROFILE = 'NATIVE_B3_GE_TWO_MATERIAL_PATCHES_SHARED_S3_STATIC_DEV_V1'
MATERIAL_MULTIPATCH_PROFILE = 'NATIVE_B3_GE_MULTIPLE_MATERIAL_PATCHES_S3_STATIC_DEV_V1'
SCHEMA = 'NATIVE_B3_GE_MULTIPLE_S3_CHECKPOINT_DEV_V1'


@dataclass(frozen=True)
class NativeS3ContactPair:
    name: str
    work: NativeRetainedLineS3Work | NativeRetainedMaterialS3Work
    gap_tolerance_m: float
    maximum_swept_intervals: int

    def __post_init__(self):
        if type(self.name) is not str or not self.name or type(self.work) not in (NativeRetainedLineS3Work,NativeRetainedMaterialS3Work):
            raise ValueError('named native/S3 pair requires exact physical work')
        if (type(self.gap_tolerance_m) not in (int, float) or not isfinite(self.gap_tolerance_m)
                or self.gap_tolerance_m <= 0):
            raise ValueError('native/S3 pair requires positive dimensional gap tolerance')
        if type(self.maximum_swept_intervals) is not int or self.maximum_swept_intervals < 1:
            raise ValueError('native/S3 pair requires a finite swept interval budget')

    def descriptor(self):
        mapping = self.work.work_map
        if not sparse.isspmatrix_csr(mapping):
            raise ValueError('native/S3 combined work map requires CSR coordinates')
        return {'name': self.name, 'work': self.work._fingerprint(),
            'combined_work_map': {'shape': mapping.shape, 'data': mapping.data,
                'indices': mapping.indices, 'indptr': mapping.indptr},
            'kernel': self.work.contact._fingerprint(), 'gap_tolerance_m': self.gap_tolerance_m,
            'maximum_swept_intervals': self.maximum_swept_intervals}


def _physical_summary(pairs):
    fields = ('potential_j', 'active_intervals', 'integration_intervals', 'integration_evaluations',
              'energy_error_j', 'force_error_n', 'tangent_error_n_per_m')
    area=type(pairs[0][0].work) is NativeRetainedMaterialS3Work
    summed_fields=tuple(k for k in fields if k!='active_intervals') if area else fields
    result = {key: sum(getattr(r.contact, key) for _, r in pairs) for key in summed_fields}
    if area:
        result.update(active_intervals=None,measure='fixed_reference_material_area',
            minimum_gap_estimate_m=min(r.contact.minimum_gap_estimate_m for _,r in pairs))
    for key in ('beam_force_n', 'shell_force_n', 'beam_moment_nm', 'shell_moment_nm'):
        result[key] = sum((getattr(r.contact, key) for _, r in pairs), np.zeros(3))
    result['minimum_gap_m'] = min(r.contact.minimum_gap_m for _, r in pairs)
    result['minimum_rim_clearance_m'] = min(r.contact.minimum_rim_clearance_m for _, r in pairs)
    result['pairs'] = [{'name': p.name, 'beam_element': p.work.contact.beam_element_id,
        'shell_body': p.work.shell.body_id, 'shell_element': p.work.shell.element_id,
        'shell_side': p.work.shell.side, 'gap_tolerance_m': p.gap_tolerance_m,
        'maximum_swept_intervals': p.maximum_swept_intervals,
        **{key: getattr(r.contact, key) for key in (*fields, 'beam_force_n', 'shell_force_n',
            'beam_moment_nm', 'shell_moment_nm', 'minimum_gap_m', 'minimum_rim_clearance_m')}}
        for p, r in pairs]
    if area:
        for row,(_,r) in zip(result['pairs'],pairs):
            row.update(measure='fixed_reference_material_area',minimum_gap_estimate_m=r.contact.minimum_gap_estimate_m)
    return result


@dataclass(frozen=True)
class NativeMultiS3Physical:
    pairs: tuple

    def __getattr__(self, name):
        values = _physical_summary(self.pairs)
        if name not in values: raise AttributeError(name)
        return values[name]

    def to_dict(self):
        return _physical_summary(self.pairs)


@dataclass(frozen=True)
class NativeMultiS3WorkResult:
    contact: NativeMultiS3Physical
    residual: np.ndarray
    tangent: sparse.csr_matrix
    pairs: tuple
    profile: str = PROFILE


@dataclass(frozen=True)
class NativeMultiS3Accepted:
    mechanical: object
    native_histories: tuple
    shell_displacement: np.ndarray
    completed_targets: int
    contact: NativeMultiS3WorkResult


@dataclass(frozen=True)
class NativeMultiS3Run:
    status: str
    accepted: NativeMultiS3Accepted
    failure: str | None
    checkpoint: bytes
    profile: str = PROFILE

    @property
    def checkpoint_sha256(self):
        return sha256(self.checkpoint).hexdigest()


class NativeRetainedMultiS3Analysis:
    """One or two retained native beams with explicit independent S3 pairs.

    The shell structural model is elastic reference-stiffness S3, with physical
    skin work and zero prescribed supports. Each selected beam must participate;
    all shell elements must be represented. Rims/patch unions remain unsupported.
    """
    profile = PROFILE
    schema = SCHEMA
    run_type = NativeMultiS3Run
    _assemble_structural = NativeRetainedRoundS3Analysis._assemble_structural
    _step = NativeRetainedRoundS3Analysis._step
    _recoverable_trial_error = staticmethod(NativeRetainedRoundS3Analysis._recoverable_trial_error)

    def __init__(self, definitions, boundaries, program, shell_model, pairs, *,
                 equilibrium_tolerance, maximum_pairs=8, maximum_coupled_coordinates=256, activation_settings=None):
        if (type(definitions) is not tuple or not 1 <= len(definitions) <= 2
                or any(type(d) is not NativeBeamDefinition for d in definitions)
                or type(program) is not Program or type(shell_model) is not FEModel):
            raise TypeError('multiple native/S3 owner requires one/two exact native definitions, program and shell model')
        if (type(maximum_pairs) is not int or not 1 <= maximum_pairs <= 8
                or type(pairs) is not tuple or not 2 <= len(pairs) <= maximum_pairs
                or any(type(p) is not NativeS3ContactPair for p in pairs)
                or len({p.name for p in pairs}) != len(pairs)):
            raise ValueError('multiple native/S3 owner requires two to eight unique explicit pairs within resource cap')
        if (type(equilibrium_tolerance) not in (int, float) or not isfinite(equilibrium_tolerance)
                or equilibrium_tolerance <= 0 or type(maximum_coupled_coordinates) is not int
                or not 1 <= maximum_coupled_coordinates <= 256):
            raise ValueError('multiple native/S3 equilibrium/resource controls invalid')
        kinds={type(p.work) for p in pairs}
        if len(kinds)!=1:
            raise ValueError('multiple native/S3 owner does not admit mixed line and area profiles')
        self._material_mode=kinds=={NativeRetainedMaterialS3Work}
        if self._material_mode:
            if type(self) is not NativeRetainedMultiS3Analysis:
                raise ValueError('material-area multiple owner requires the exact owner without activation controller')
            self.profile=(MATERIAL_PROFILE if len(definitions)==2 and len(pairs)==2
                and shell_model.mesh.dof_manager.total_dofs==18
                and len({p.work.shell.element_id for p in pairs})==1 else MATERIAL_MULTIPATCH_PROFILE)
        if activation_settings is not None:
            if not self._material_mode:
                raise ValueError('base multiple activation settings require the material-area owner')
            from .native_material_activation import validate_settings
            validate_settings(activation_settings, tuple(p.work for p in pairs),
                              tuple(p.gap_tolerance_m for p in pairs))
        # The historical line subclass owns its own settings and hook.
        if self._material_mode or type(self) is NativeRetainedMultiS3Analysis:
            self.activation_settings = activation_settings
            self.activation_total_queries = 0
        self.native = NativeBeamAnalysis(definitions, boundaries)
        self.context = Context(self.native.model, program)
        if (len(self.context.elements) != len(definitions)
                or any(type(e) is not NativeGeneralizedStaticElement for _, e in self.context.elements)):
            raise ValueError('multiple native/S3 owner requires exact retained generalized elements')
        self.shell_model, self.program = shell_model, program
        self.pairs = tuple(sorted(pairs, key=lambda p: p.name))
        self.equilibrium_tolerance = float(equilibrium_tolerance)
        self.maximum_pairs, self.maximum_coupled_coordinates = maximum_pairs, maximum_coupled_coordinates
        n_shell = shell_model.mesh.dof_manager.total_dofs
        if self.context.count+n_shell > maximum_coupled_coordinates:
            raise MemoryError('multiple native/S3 coupled-coordinate resource cap exceeded')
        elements = {eid: (i, e) for i, (eid, e) in enumerate(self.context.elements)}
        indices = []; owned = set(); envelopes = {}; shell_bodies = {}
        for p in self.pairs:
            work, kernel = p.work, p.work.contact
            if kernel.beam_element_id not in elements:
                raise ValueError('native/S3 pair beam does not bind owner')
            i, element = elements[kernel.beam_element_id]
            if (tuple(element.node_ids) != kernel.beam_node_ids
                    or sha(element.operator.reference.canonical_data()) != sha(kernel.beam_reference.canonical_data())
                    or work.work_map.shape != (51, 42+n_shell)):
                raise ValueError('native/S3 pair work/reference does not bind authoritative coordinates')
            key = (kernel.beam_element_id, work.shell.element_id, work.shell.side)
            if key in owned: raise ValueError('duplicate physical native beam/S3 skin pair')
            owned.add(key); indices.append(i)
            eid = kernel.beam_element_id
            if eid in envelopes and envelopes[eid] != kernel.radius:
                raise ValueError('shared native beam has conflicting round radius')
            envelopes[eid] = kernel.radius
            sid = work.shell.element_id
            if sid in shell_bodies and shell_bodies[sid] != work.shell.body_id:
                raise ValueError('physical S3 feature has conflicting body identity')
            shell_bodies[sid] = work.shell.body_id
        if set(elements) != set(envelopes):
            raise ValueError('multiple native/S3 definition has an unreferenced beam')
        self.beam_indices = tuple(indices)
        self.shell_stiffness, self.shell_free, self.shell_fixed = self._shell_contract()
        self.shell_stiffness = _readonly(self.shell_stiffness)
        self.shell_free.setflags(write=False); self.shell_fixed.setflags(write=False)
        self.shell_contract_sha = self._shell_contract_sha()
        self.identity = self._identity()
        self.candidate_evaluations = self.pair_evaluations = 0
        initial = self.context.initial
        u = np.zeros(n_shell)
        first = self._contact(initial.mechanical, u)
        for p, r in first.pairs:
            scale = max(1., np.max(np.abs(p.work.contact.beam_reference.coordinates)),
                        np.max(np.abs(p.work.shell.reference_positions)))
            if r.contact.minimum_gap_m < -256*np.finfo(float).eps*scale:
                raise ValueError(p.name+': unresolved initial native/S3 penetration')
        self.initial = NativeMultiS3Accepted(initial.mechanical, initial.histories, _readonly(u), 0, first)

    def _shell_contract(self):
        model = self.shell_model
        selected = {p.work.shell.element_id for p in self.pairs}
        if (set(model.mesh.elements) != selected or model.constraint_equations
                or model.load_cases or model.mesh.element_activity is not None):
            raise ValueError('multiple native/S3 owner requires represented active S3 elements and simple supports')
        n = model.mesh.dof_manager.total_dofs
        if n+self.context.count > self.maximum_coupled_coordinates:
            raise MemoryError('multiple native/S3 shell coordinate resource cap exceeded')
        K = np.zeros((n, n)); nodes = set()
        for eid, element in sorted(model.mesh.elements.items()):
            if type(element) is not NativeParityE4PLS3V2DShellElement or element.shell_section is not None:
                raise ValueError('multiple native/S3 owner requires exact elastic S3 V2D')
            material = model.materials.get(element.material_name)
            if (type(material) is not IsotropicMaterial or material.yield_stress != 0.
                    or material.hardening_curve is not None):
                raise ValueError('multiple native/S3 owner requires isotropic elastic skin material')
            nodes.update(element.node_ids)
            slots = np.asarray(element.get_dof_mapping(model.mesh), int)
            local = element.compute_stiffness_matrix(model.mesh, material)
            if local.shape != (18, 18) or not np.all(np.isfinite(local)):
                raise ValueError('multiple native/S3 structural block invalid')
            K[np.ix_(slots, slots)] += local
        if nodes != set(model.mesh.nodes) or not np.allclose(K, K.T, rtol=1e-10, atol=1e-10):
            raise ValueError('multiple native/S3 orphan coordinates or nonsymmetric shell structure')
        for p in self.pairs:
            shell = p.work.shell
            element = model.mesh.elements[shell.element_id]
            fresh = S3SkinWorkAdapter.from_model(model, shell.body_id, shell.element_id, shell.side)
            combined = sparse.block_diag((sparse.eye(42, format='csr'), fresh.work_map), format='csr')
            if (tuple(element.node_ids) != shell.node_ids
                    or not np.array_equal(fresh.reference_positions, shell.reference_positions)
                    or not np.array_equal(fresh.director, shell.director)
                    or fresh.physical_offset != shell.physical_offset
                    or (fresh.work_map != shell.work_map).nnz
                    or not sparse.isspmatrix_csr(p.work.work_map)
                    or p.work.work_map.shape != combined.shape
                    or (combined != p.work.work_map).nnz):
                raise ValueError('multiple native/S3 physical skin adapter does not bind model')
        fixed = set()
        for bc in model.boundary_conditions:
            for dof, value in bc.get_constrained_dofs(model.mesh.dof_manager):
                if not np.isfinite(value) or value != 0.:
                    raise ValueError('multiple native/S3 owner admits zero shell supports only')
                fixed.add(int(dof))
        free = np.array(sorted(set(range(n))-fixed), int)
        if len(free) == 0 or np.linalg.matrix_rank(K[np.ix_(free, free)]) < len(free):
            raise ValueError('multiple native/S3 shell has a static mechanism or no deformable coordinates')
        return K, free, np.array(sorted(fixed), int)

    def _shell_contract_sha(self):
        K, free, fixed = self._shell_contract()
        return sha({'K': K, 'free': free, 'fixed': fixed,
            'elements': [{'id': eid, 'nodes': e.node_ids, 'formulation': e.formulation_id,
                'thickness': e.thickness, 'offset': e.reference_surface_offset, 'polarity': e.director_polarity,
                'coordinates': [self.shell_model.mesh.nodes[n].coords() for n in e.node_ids],
                'material': {name: getattr(self.shell_model.materials[e.material_name], name)
                    for name in ('name', 'elastic_modulus', 'poisson_ratio', 'density', 'yield_stress')}}
                for eid, e in sorted(self.shell_model.mesh.elements.items())],
            'pairs': [p.descriptor() for p in self.pairs]})

    def _identity(self):
        descriptor = {'profile': self.profile if self._material_mode else PROFILE, 'revision': 'uncondensed_explicit_native_s3_work_v1',
            'native': self.context.identity, 'support': sha256(self.context.support_identity).hexdigest(),
            'shell': self.shell_contract_sha, 'cached_shell': [self.shell_stiffness, self.shell_free, self.shell_fixed],
            'pairs': [p.descriptor() for p in self.pairs], 'beam_indices': self.beam_indices,
            'native_slots': self.context.slots, 'equilibrium_tolerance': self.equilibrium_tolerance,
            'maximum_pairs': self.maximum_pairs, 'maximum_coupled_coordinates': self.maximum_coupled_coordinates}
        if self._material_mode and self.activation_settings is not None:
            from .native_material_activation import REVISION
            descriptor['activation'] = (REVISION, self.activation_settings)
        return sha(descriptor)

    def _guard(self):
        self.context.guard(); self.native._guard()
        if self._identity() != self.identity or self._shell_contract_sha() != self.shell_contract_sha:
            raise ValueError('multiple native/S3 definition/settings/model changed')

    def _contact(self, mechanical, displacement):
        if self._identity() != self.identity:
            raise ValueError('multiple native/S3 consumed work/settings changed')
        total = self.context.count+len(displacement)
        residual = np.zeros(total); tangent = sparse.csr_matrix((total, total)); pairs = []
        for p, i in zip(self.pairs, self.beam_indices):
            nodes = self.context.nodes[i]
            result = p.work.evaluate(mechanical.positions[nodes], mechanical.position_low[nodes],
                                     mechanical.cell_rotations[i], displacement)
            slots = np.r_[self.context.slots[i], self.context.count+np.arange(len(displacement))]
            np.add.at(residual, slots, result.residual)
            P = sparse.coo_matrix((np.ones(len(slots)), (np.arange(len(slots)), slots)),
                                  shape=(len(slots), total)).tocsr()
            tangent += P.T@result.tangent@P
            pairs.append((p, result)); self.pair_evaluations += 1
        self.candidate_evaluations += 1
        return NativeMultiS3WorkResult(NativeMultiS3Physical(tuple(pairs)), _readonly(residual), tangent.tocsr(), tuple(pairs),
            self.profile if self._material_mode else PROFILE)

    def _contact_admissible(self, result):
        return all(r.contact.minimum_gap_m >= -p.gap_tolerance_m for p, r in result.pairs)

    def _assemble(self, mechanical, displacement, parameter, origins):
        residual, tangent, responses = self._assemble_structural(mechanical, displacement, parameter, origins)
        contact = self._contact(mechanical, displacement)
        residual += contact.residual
        for (p, result), i in zip(contact.pairs, self.beam_indices):
            block = result.tangent.toarray()
            if type(p.work) is not NativeRetainedMaterialS3Work:
                block[:42, :42] = spatial_jacobian(result.residual[:42], block[:42, :42])
            slots = np.r_[self.context.slots[i], self.context.count+np.arange(len(displacement))]
            rows, cols = np.meshgrid(slots, slots, indexing='ij')
            np.add.at(tangent, (rows, cols), block)
        n = self.context.count; scaled = residual[:n]/self.context.scale
        metrics = (float(np.linalg.norm(scaled[self.context.equilibrium])),
            float(np.linalg.norm(scaled[self.context.compatibility])),
            float(np.linalg.norm(residual[n+self.shell_free])))
        return residual, tangent, metrics, responses, contact

    def _activation_fraction(self, start, u_start, step, fraction, contact, cancellation_token):
        if self.activation_settings is None:
            return fraction
        from .native_material_activation import activation_fraction
        return activation_fraction(self, start, u_start, step, fraction, contact, cancellation_token)

    def _swept_admissible(self, start, u_start, increment, end, u_end, *_):
        first = self._contact(start, u_start); last = self._contact(end, u_end)
        admitted = []
        for (p, r0), (_, r1), i in zip(first.pairs, last.pairs, self.beam_indices):
            a, b = r0.contact, r1.contact
            if type(p.work) is NativeRetainedMaterialS3Work:
                nodes=self.context.nodes[i];work=p.work
                pose=work._configuration(start.positions[nodes],start.position_low[nodes],
                    start.cell_rotations[i],u_start)
                translations=(end.positions[nodes]-start.positions[nodes]
                              +end.position_low[nodes]-start.position_low[nodes])
                angular=np.array([increment[self.context.nodal_count+24*i+3*c:
                                            self.context.nodal_count+24*i+3*c+3] for c in (0,1)])
                try:work.certify_orientation_path(pose,translations,angular,u_end-u_start,
                    p.maximum_swept_intervals)
                except ValueError as exc:
                    if self._recoverable_trial_error(exc):return False
                    raise
                def geometry_query(state,u):
                    return work.geometry_gap(state.positions[nodes],state.position_low[nodes],
                        state.cell_rotations[i],u)
                admitted.append(native_s3_swept_admissible(self.context,work,i,p.gap_tolerance_m,
                    p.maximum_swept_intervals,self._recoverable_trial_error,start,u_start,increment,
                    end,u_end,a.minimum_gap_m,b.minimum_gap_m,a.minimum_rim_clearance_m,
                    b.minimum_rim_clearance_m,geometry_only=True,geometry_query=geometry_query,
                    material_radius=work.contact.radius))
                continue
            admitted.append(native_s3_swept_admissible(self.context, p.work, i, p.gap_tolerance_m,
                p.maximum_swept_intervals, self._recoverable_trial_error, start, u_start, increment,
                end, u_end, a.minimum_gap_m, b.minimum_gap_m,
                a.minimum_rim_clearance_m, b.minimum_rim_clearance_m))
        return all(admitted)

    def _record(self, target, mechanical, displacement, origins, previous_sha256):
        if type(target) is not int or not 1 <= target <= len(self.program.targets):
            raise ValueError('multiple native/S3 checkpoint target')
        mechanical = self.context.make(mechanical.descriptor())
        u = np.asarray(displacement, float).reshape(-1)
        if (u.size != self.shell_stiffness.shape[0] or not np.all(np.isfinite(u))
                or np.any(u[self.shell_fixed] != 0.)):
            raise ValueError('multiple native/S3 checkpoint shell displacement')
        r, K, metrics, responses, contact = self._assemble(mechanical, u, self.program.targets[target-1], origins)
        _, correction = self._step(r, K)
        if max(*metrics, correction) > self.equilibrium_tolerance or not self._contact_admissible(contact):
            raise ValueError('multiple native/S3 checkpoint requires complete equilibrium and every pair gap')
        histories = self.context.histories(tuple(r.history for r in responses))
        row = {'target': target, 'previous_sha256': previous_sha256,
            'mechanical': mechanical.descriptor(), 'histories': histories, 'shell_displacement': u,
            'contact': contact.contact.to_dict()}
        accepted = NativeMultiS3Accepted(mechanical, histories, _readonly(u), target, contact)
        return accepted, _load(canonical(row).decode('ascii'))

    def _checkpoint(self, records):
        self._guard()
        if type(records) is not tuple or len(records) > len(self.program.targets):
            raise ValueError('multiple native/S3 checkpoint extent')
        body = {'schema': self.schema, 'profile': self.profile, 'identity': self.identity,
                'completed_targets': len(records), 'records': records}
        raw = canonical({**body, 'checkpoint_sha256': sha(body)})
        if len(raw) > MAX_BYTES: raise MemoryError('multiple native/S3 checkpoint byte limit')
        return raw

    def _restore(self, raw, expected_sha256):
        self._guard()
        if type(raw) is not bytes or type(expected_sha256) is not str or sha256(raw).hexdigest() != expected_sha256:
            raise ValueError('multiple native/S3 external checkpoint hash mismatch')
        value = _load(raw.decode('ascii'))
        if type(value) is not dict or set(value) != {'schema', 'profile', 'identity', 'completed_targets', 'records', 'checkpoint_sha256'}:
            raise ValueError('multiple native/S3 checkpoint schema')
        body = {k: v for k, v in value.items() if k != 'checkpoint_sha256'}
        if value['schema'] != self.schema or value['profile'] != self.profile or value['identity'] != self.identity or sha(body) != value['checkpoint_sha256']:
            raise ValueError('multiple native/S3 checkpoint definition/settings binding')
        count = value['completed_targets']
        if type(count) is not int or not 0 <= count <= len(self.program.targets) or type(value['records']) is not list or len(value['records']) != count:
            raise ValueError('multiple native/S3 checkpoint target extent')
        accepted = self.initial; records = (); previous = sha({'schema': self.schema, 'identity': self.identity})
        for index, row in enumerate(value['records'], 1):
            if (type(row) is not dict or set(row) != {'target', 'previous_sha256', 'mechanical', 'histories', 'shell_displacement', 'contact'}
                    or row['target'] != index or row['previous_sha256'] != previous):
                raise ValueError('multiple native/S3 checkpoint accepted chain')
            mechanical = self.context.make(row['mechanical'], decoded=True)
            accepted, replay = self._record(index, mechanical, row['shell_displacement'], accepted.native_histories, previous)
            if canonical(row) != canonical(replay): raise ValueError('multiple native/S3 checkpoint replay mismatch')
            records += (replay,); previous = sha(replay)
        if self._checkpoint(records) != raw: raise ValueError('multiple native/S3 noncanonical checkpoint replay')
        return accepted, records

    def solve(self, *, checkpoint=None, expected_sha256=None, stop_after=None,
              cancellation_token=None, progress=None):
        result=solve_native_shell(self, self.schema, self.run_type, checkpoint=checkpoint,
            expected_sha256=expected_sha256, stop_after=stop_after,
            cancellation_token=cancellation_token, progress=progress)
        return replace(result,profile=self.profile) if self._material_mode else result


def create_native_contact_analysis(definitions, boundaries, program, shell_model, pairs, *,
        equilibrium_tolerance, maximum_pairs=8, maximum_coupled_coordinates=256,
        activation_settings=None):
    """Create the explicit retained multiple-S3 development owner.

    Native definitions stay under NativeBeamAnalysis, not generic FEModel.
    """
    owner = NativeRetainedMultiS3Analysis
    extra = {}
    if activation_settings is not None:
        if (type(pairs) is tuple and pairs
                and all(type(p.work) is NativeRetainedMaterialS3Work for p in pairs)):
            extra['activation_settings'] = activation_settings
        else:
            from .native_activation_static import NativeActivationMultiS3Analysis
            owner = NativeActivationMultiS3Analysis
            extra['activation_settings'] = activation_settings
    return owner(definitions, boundaries, program, shell_model, pairs,
        equilibrium_tolerance=equilibrium_tolerance, maximum_pairs=maximum_pairs,
        maximum_coupled_coordinates=maximum_coupled_coordinates, **extra)
