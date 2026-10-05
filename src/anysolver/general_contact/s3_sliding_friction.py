"""Material-anchor friction on a convex, conforming planar S3 target patch.

Development profile: fixed reference source quadrature; shared mortar pressure;
material anchors convected by the target FE map. A return moves the anchor across
facets. The physical virtual-work map holds that returned anchor fixed, whereas
the candidate tangent differentiates the complete return. No finite-rotation,
crease, partial source coverage, or swept friction qualification is implied.
"""

from dataclasses import asdict, dataclass

import numpy as np
from scipy import sparse
from scipy.spatial import ConvexHull

from .s3_friction_point import S3SkinMaterialPoint
from .s3_skin_work import S3SkinWorkAdapter


PROFILE = "S3_PLANAR_MATERIAL_ANCHOR_STATIC_DEV_V1"
_QUADRATURE = ((2/3, 1/6, 1/6), (1/6, 2/3, 1/6), (1/6, 1/6, 2/3))


def _reference_quadrature(level):
    cells=[np.eye(3)]
    for _ in range(level):
        refined=[]
        for a,b,c in cells:
            ab,bc,ca=(a+b)/2,(b+c)/2,(c+a)/2
            refined.extend(((a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)))
        cells=[np.asarray(cell) for cell in refined]
    fraction=1/(3*4**level)
    return tuple((tuple(float(x) for x in np.asarray(bary)@cell),fraction)
                 for cell in cells for bary in _QUADRATURE)


@dataclass(frozen=True)
class S3SlidingFrictionSettings:
    friction_coefficient: float
    tangential_stiffness_Pa_per_m: float
    steps_by_dof: tuple[float, ...]
    maximum_candidate_evaluations: int = 145
    geometry_relative_tolerance: float = 1e-10
    maximum_probe_barycentric_change: float = 1e-3
    source_quadrature_refinement: int = 0
    maximum_material_points: int = 4096
    activation_history: str = "endpoint"
    maximum_probe_touch_fraction_change: float = 1e-3

    def __post_init__(self):
        steps = tuple(float(x) for x in self.steps_by_dof)
        values = (self.friction_coefficient, self.tangential_stiffness_Pa_per_m,
                  self.geometry_relative_tolerance,self.maximum_probe_barycentric_change,
                  self.maximum_probe_touch_fraction_change)
        if (not np.all(np.isfinite(values)) or self.friction_coefficient < 0
                or self.tangential_stiffness_Pa_per_m <= 0
                or not 0 < self.geometry_relative_tolerance <= 1e-6
                or not 0 < self.maximum_probe_barycentric_change <= 1
                or not 0 < self.maximum_probe_touch_fraction_change <= 1):
            raise ValueError("sliding friction needs finite mu>=0, stiffness>0 and geometry tolerance")
        if not steps or not np.all(np.isfinite(steps)) or min(steps) <= 0:
            raise ValueError("sliding friction needs explicit positive FE derivative steps")
        if type(self.maximum_candidate_evaluations) is not int or self.maximum_candidate_evaluations < 1:
            raise ValueError("sliding friction evaluation cap must be positive")
        if type(self.source_quadrature_refinement) is not int or not 0<=self.source_quadrature_refinement<=5:
            raise ValueError("friction quadrature refinement must be an integer from0 to5")
        if type(self.maximum_material_points) is not int or self.maximum_material_points<1:
            raise ValueError("friction material-point cap must be positive")
        if self.activation_history not in {"endpoint","linear_constant_normal_touch_dev"}:
            raise ValueError("unsupported friction activation-history rule")
        object.__setattr__(self, "steps_by_dof", steps)


@dataclass(frozen=True)
class S3MaterialAnchorState:
    target_element: int | None = None
    barycentric: tuple[float, float, float] | None = None
    cumulative_plastic_slip_m: float = 0.0
    cumulative_dissipation_Pa_m: float = 0.0
    stored_energy_Pa_m: float = 0.0

    def __post_init__(self):
        if (self.target_element is None) != (self.barycentric is None):
            raise ValueError("material anchor needs both facet and material coordinates")
        if self.target_element is not None:
            if type(self.target_element) is not int:
                raise ValueError("anchor facet identity must be an integer")
            b = np.asarray(self.barycentric, dtype=float)
            if (b.shape != (3,) or not np.all(np.isfinite(b)) or min(b) < 0
                    or abs(b.sum()-1) > 1e-12):
                raise ValueError("anchor needs nonnegative barycentric material coordinates")
            object.__setattr__(self, "barycentric", tuple(float(x) for x in b))
        scalars = (self.cumulative_plastic_slip_m, self.cumulative_dissipation_Pa_m,
                   self.stored_energy_Pa_m)
        if not np.all(np.isfinite(scalars)) or min(scalars) < 0:
            raise ValueError("anchor history must be finite and nonnegative")
        if self.target_element is None and self.stored_energy_Pa_m != 0:
            raise ValueError("open anchor cannot retain elastic storage")


def _skew(a):
    x, y, z = a
    return np.array(((0, -z, y), (z, 0, -x), (-y, x, 0)))


class S3SlidingFrictionManager:
    def __init__(self, model, normal, settings):
        from .s3_patch_static import GeneralS3PatchManager
        if type(settings) is not S3SlidingFrictionSettings:
            raise TypeError("sliding friction needs S3SlidingFrictionSettings")
        if (type(normal) is not GeneralS3PatchManager or normal.augmented
                or not normal.projected_work
                or normal.settings.normal_discretization != "primal_mortar"):
            raise ValueError("material-anchor friction needs the projected S3 patch penalty owner")
        self.normal, self.friction_settings = normal, settings
        self.n_dof = model.mesh.dof_manager.total_dofs
        if len(settings.steps_by_dof) != self.n_dof:
            raise ValueError("sliding friction steps must match authoritative FE coordinates")
        interaction = normal.definition.interactions[0]
        surfaces = {s.name: s for s in normal.definition.surfaces}
        source, target = surfaces[interaction.surface], surfaces[interaction.target]
        self.source_adapters = tuple(S3SkinWorkAdapter.from_model(model, 1, e, source.side)
                                     for e in sorted(source.element_ids))
        self.target_adapters = {e: S3SkinWorkAdapter.from_model(model, 2, e, target.side)
                                for e in sorted(target.element_ids)}
        edge_owners = {}
        for e, adapter in self.target_adapters.items():
            for i in range(3):
                edge = tuple(sorted(adapter.node_ids[k] for k in range(3) if k != i))
                edge_owners.setdefault(edge, []).append(e)
        self.boundary_edges = frozenset(edge for edge, owners in edge_owners.items() if len(owners)==1)
        point_count=len(self.source_adapters)*3*4**settings.source_quadrature_refinement
        if point_count>settings.maximum_material_points:
            raise MemoryError("friction reference quadrature exceeds its material-point cap")
        columns=set(normal.map.indices)
        for adapter in (*self.source_adapters,*self.target_adapters.values()):
            columns.update(adapter.work_map.indices)
        self.work_columns=np.asarray(sorted(columns),dtype=np.intp)
        self.work_columns.setflags(write=False)
        self.columns=tuple(self.work_columns)
        self.target_maps={e:a.work_map[:,self.work_columns].toarray().reshape(3,3,-1)
                          for e,a in self.target_adapters.items()}
        self.points, self.weights, self.pressure_indices = [], [], []
        quadrature=_reference_quadrature(settings.source_quadrature_refinement)
        for adapter in self.source_adapters:
            c = adapter.reference_positions
            area = np.linalg.norm(np.cross(c[1]-c[0], c[2]-c[0]))/2
            for bary,fraction in quadrature:
                self.points.append(S3SkinMaterialPoint(adapter, bary))
                self.weights.append(area*fraction)
                self.pressure_indices.append(tuple(normal.law.source_node_ids.index(n)
                                                   for n in adapter.node_ids))
        self.point_maps=tuple(p.position_map[:,self.work_columns].toarray() for p in self.points)
        self.point_reference=tuple(np.asarray(p.barycentric)@p.adapter.reference_positions for p in self.points)
        for mapping in (*self.point_maps,*self.target_maps.values()):
            mapping.setflags(write=False)
        if 1+2*len(self.columns) > settings.maximum_candidate_evaluations:
            raise MemoryError("material-anchor friction derivative evaluation cap exceeded")
        self.committed_displacement = np.zeros(self.n_dof)
        self.history = tuple(S3MaterialAnchorState() for _ in self.points)
        self.last_committed_summary = None
        self._patch(self.committed_displacement)

    def __getattr__(self, name):
        return getattr(self.normal, name)

    def restrict_tangent_to_reduced_variations(self, transform):
        self.normal.restrict_tangent_to_reduced_variations(transform)
        reachable = np.asarray(sparse.csr_matrix(transform).getnnz(axis=1)).ravel() > 0
        self.columns = tuple(c for c in self.columns if reachable[c])

    def _patch(self, u, *, validate=True,require_full_coverage=True):
        """Validate a conforming convex planar union; return current facet data."""
        corners = {e: a.current_positions(u) for e, a in self.target_adapters.items()}
        first = next(iter(corners.values()))
        v, w = first[1]-first[0], first[2]-first[0]
        # Area-vector normal depends on the physical patch boundary; internal
        # triangulation edges cancel. Its derivative must use this same definition.
        cross = sum((np.cross(c[1]-c[0], c[2]-c[0]) for c in corners.values()), np.zeros(3))
        norm = np.linalg.norm(cross)
        if norm <= 1e-14*np.linalg.norm(v)*np.linalg.norm(w):
            raise ValueError("degenerate target material patch")
        n = cross/norm
        frame = np.column_stack((v/np.linalg.norm(v), np.cross(n, v/np.linalg.norm(v)), n))
        if validate:
            tol = self.friction_settings.geometry_relative_tolerance
            scale = max(np.linalg.norm(c-first[0], axis=1).max() for c in corners.values())
            vertices, edges = {}, {}
            for e, c in corners.items():
                a = self.target_adapters[e]
                ref = a.reference_positions
                raw = np.cross(c[1]-c[0], c[2]-c[0])
                if (raw@n <= 1e-12*np.linalg.norm(raw)
                        or raw@np.cross(ref[1]-ref[0], ref[2]-ref[0]) <= 0
                        or np.max(np.abs((c-first[0])@n)) > tol*scale):
                    raise ValueError("target friction patch must be valid, consistently oriented and planar")
                for node, xyz in zip(a.node_ids, c):
                    if node in vertices and np.linalg.norm(vertices[node]-xyz) > tol*scale:
                        raise ValueError("target physical skins are discontinuous at a material node")
                    vertices[node] = xyz
                for i in range(3):
                    edge = (a.node_ids[i], a.node_ids[(i+1)%3])
                    edges.setdefault(tuple(sorted(edge)), []).append(edge)
            if any(len(v)>2 or (len(v)==2 and v[0] != v[1][::-1]) for v in edges.values()):
                raise ValueError("target friction patch is not a conforming oriented manifold")
            boundary = [v[0] for v in edges.values() if len(v)==1]
            next_node = dict(boundary)
            if len(next_node) != len(boundary) or not boundary:
                raise ValueError("target friction patch needs one simple boundary")
            visited, node = set(), boundary[0][0]
            while node not in visited and node in next_node:
                visited.add(node)
                node = next_node[node]
            if node != boundary[0][0] or len(visited) != len(boundary):
                raise ValueError("target friction patch has holes or disconnected boundaries")
            if len(vertices)-len(edges)+len(corners) != 1:
                raise ValueError("target friction patch topology must be a disk")
            uv = (np.asarray(list(vertices.values()))-first[0])@frame[:, :2]
            hull = ConvexHull(uv)
            area = sum(np.linalg.norm(np.cross(c[1]-c[0], c[2]-c[0]))/2 for c in corners.values())
            if abs(area-hull.volume) > tol*area:
                raise ValueError("target friction patch must be a convex union without overlaps")
            # Convexity makes complete corner coverage sufficient for each source triangle.
            if require_full_coverage:
                for adapter in self.source_adapters:
                    for position in adapter.current_positions(u):
                        self._locate(position, corners, n, frame, first[0])
        return corners, n, frame, first[0]

    def _locate(self, position, corners, n, frame, origin):
        for e, c in corners.items():  # Stable element-ID order owns seam ties.
            b = self._facet_coordinates(position,c,frame)
            # Geometry admission tolerance must not snap a return across a finite
            # band. Only machine-roundoff barycentric ties may be normalized.
            if min(b) >= -128*np.finfo(float).eps:
                b = np.maximum(b, 0)
                b /= b.sum()
                return e, tuple(float(x) for x in b)
        raise ValueError("material friction point/source facet left the target patch")

    @staticmethod
    def _facet_coordinates(position, corners, frame):
        q = (corners-corners[0])@frame[:, :2]
        uv = np.linalg.solve(q[1:].T,(np.asarray(position)-corners[0])@frame[:, :2])
        return np.array((1-uv.sum(), *uv))

    def _on_rim(self, element, bary):
        nodes = self.target_adapters[element].node_ids
        return any(value <= 128*np.finfo(float).eps
                   and tuple(sorted(nodes[k] for k in range(3) if k != i)) in self.boundary_edges
                   for i,value in enumerate(bary))

    def _normal_variation(self, corners, n, *, local=False):
        width=len(self.work_columns) if local else self.n_dof
        raw, derivative = np.zeros(3), np.zeros((3,width))
        for element, c in corners.items():
            v, w = c[1]-c[0], c[2]-c[0]
            J=(self.target_maps[element] if local else
               self.target_adapters[element].work_map.toarray().reshape(3,3,self.n_dof))
            raw += np.cross(v, w)
            derivative += -_skew(w)@(J[1]-J[0])+_skew(v)@(J[2]-J[0])
        return (np.eye(3)-np.outer(n, n))@derivative/np.linalg.norm(raw)

    def _work(self, point, u, element, bary, n, Dn, *, local_index=None, corners=None):
        adapter = self.target_adapters[element]
        c=adapter.current_positions(u) if corners is None else corners[element]
        P = np.eye(3)-np.outer(n, n)
        Js=point.position_map.toarray() if local_index is None else self.point_maps[local_index]
        # Shape functions are extended off the chosen facet only by the private
        # disposable tangent probes. Physical state coordinates remain nonnegative.
        Jt=np.einsum('i,ijk->jk',np.asarray(bary),
            adapter.work_map.toarray().reshape(3,3,self.n_dof) if local_index is None else self.target_maps[element])
        x=(np.asarray(point.barycentric)@point.adapter.current_positions(u) if local_index is None else
           self.point_reference[local_index]+Js@u[self.work_columns])
        y = np.asarray(bary)@c
        r = x-y
        gap = n@r
        elastic = P@r
        De = P@(Js-Jt)-(np.outer(n, r)+gap*np.eye(3))@Dn
        return elastic, De, y

    def _friction(self, u, *, branches=None, validate=True, linearized_elements=None,
                  linearized_barycentric=None, local_force=False,linearized_touch=None):
        if linearized_elements is not None and (validate or branches is None):
            raise ValueError("facet extrapolation is restricted to disposable tangent probes")
        if not validate and linearized_elements is None:
            raise ValueError("unvalidated evaluation is restricted to disposable tangent probes")
        if linearized_touch is not None and (validate or len(linearized_touch)!=len(self.points)):
            raise ValueError("first-touch probes must match disposable material points")
        if branches is not None and linearized_elements is None:
            raise ValueError("branch freezing is restricted to disposable tangent probes")
        if linearized_elements is not None:
            if (linearized_barycentric is None or len(branches)!=len(self.points)
                    or len(linearized_elements)!=len(self.points)
                    or len(linearized_barycentric)!=len(self.points)
                    or any(b not in {"open","activation","stick","slip"} for b in branches)):
                raise ValueError("facet tangent topology must cover the same material points")
            for branch,element,bary in zip(branches,linearized_elements,linearized_barycentric):
                if branch!="open" and (element not in self.target_adapters or bary is None):
                    raise ValueError("facet tangent topology contains an invalid material anchor")
        u = np.asarray(u, dtype=float)
        if u.shape != (self.n_dof,) or not np.all(np.isfinite(u)):
            raise ValueError("material friction pose needs finite authoritative coordinates")
        corners, n, frame, origin = self._patch(u, validate=validate)
        Dn = self._normal_variation(corners,n,local=True)
        source, target = self.normal._positions(u)
        state = self.normal.law.evaluate(source, target, self.normal.normal_multipliers)
        settings = self.friction_settings
        kt, mu = settings.tangential_stiffness_Pa_per_m, settings.friction_coefficient
        residual, records, histories = np.zeros(len(self.work_columns)), [], []
        local_u=u[self.work_columns]
        touch_path=None
        if (settings.activation_history=="linear_constant_normal_touch_dev"
                and any(h.target_element is None for h in self.history)):
            from .s3_friction_touch import S3LinearTouchPath
            touch_path=S3LinearTouchPath(self,u,corners)
        for j, (point, area, indices, old) in enumerate(zip(
                self.points, self.weights, self.pressure_indices, self.history)):
            x=self.point_reference[j]+self.point_maps[j]@local_u
            gap = float(n@(x-origin))
            pressure = 0.0 if gap >= 0 else float(np.asarray(point.barycentric)@state.pressure[list(indices)])
            fixed = None if branches is None else branches[j]
            pressure = max(0.0, pressure)
            branch, traction, dissipation, plastic, storage, return_drop = "open", np.zeros(3), 0., 0., 0., 0.
            element, bary = None, None
            touch=None
            new = (S3MaterialAnchorState(None,None,old.cumulative_plastic_slip_m,
                                         old.cumulative_dissipation_Pa_m)
                   if linearized_elements is None else None)
            if (fixed is None and gap < 0) or fixed in ("stick", "slip", "activation"):
                anchor_element,anchor_bary=old.target_element,old.barycentric
                if anchor_element is None and touch_path is not None:
                    touch=touch_path.anchor(j,probe=None if linearized_touch is None else linearized_touch[j])
                    if touch is None:
                        raise ValueError("first-touch branch cannot resolve closing contact")
                    anchor_element,anchor_bary,_fraction=touch
                if anchor_element is None:
                    if linearized_elements is None:
                        element,bary = self._locate(x,corners,n,frame,origin)
                    else:
                        element = linearized_elements[j]
                        bary = tuple(self._facet_coordinates(x,corners[element],frame))
                    branch = "activation"  # Recontact starts stress-free at the current projection.
                else:
                    element,bary=anchor_element,anchor_bary
                    elastic,_map,old_anchor=self._work(point,u,element,bary,n,Dn,local_index=j,corners=corners)
                    length = np.linalg.norm(elastic)
                    cap = mu*pressure
                    branch = ("stick" if kt*length <= cap else "slip") if fixed is None else fixed
                    if branch == "slip":
                        if length == 0:
                            raise ValueError("explicit FE step cannot resolve the slip generalized derivative")
                        returned = (cap/kt)*elastic/length
                        projected_source = x-gap*n
                        if linearized_elements is None:
                            element,bary = self._locate(projected_source-returned,corners,n,frame,origin)
                        else:
                            element = linearized_elements[j]
                            bary = tuple(self._facet_coordinates(projected_source-returned,corners[element],frame))
                        # Current physical distance between the advected and returned material anchors.
                        moved = np.asarray(bary)@corners[element]-old_anchor
                        plastic = float(np.linalg.norm((np.eye(3)-np.outer(n, n))@moved))
                        dissipation = cap*plastic
                    elastic,work,_anchor=self._work(point,u,element,bary,n,Dn,local_index=j,corners=corners)
                    traction = -kt*elastic
                    storage = .5*kt*float(elastic@elastic)
                    if branch == "slip":
                        return_drop = max(0., .5*kt*length**2-storage)
                        # A finite return step uses endpoint pressure and current
                        # material distance. Separate its projection loss from
                        # frictional dissipation; this is not a path-integral claim.
                        cone_error = max(0., np.linalg.norm(traction)-cap)
                        geometry_scale = max(np.linalg.norm(x-origin),
                            *(np.linalg.norm(c-c[0],axis=1).max() for c in corners.values()))
                        roundoff = 512*np.finfo(float).eps*kt*geometry_scale
                        if validate and cone_error > roundoff:
                            raise ValueError("material-anchor return violates its Coulomb cap")
                    residual -= area*(work.T@traction)
                if linearized_elements is not None:
                    if (not np.all(np.isfinite(bary)) or
                            np.max(np.abs(np.asarray(bary)-linearized_barycentric[j]))
                            > settings.maximum_probe_barycentric_change):
                        raise ValueError("explicit FE step exceeds the material-facet derivative resolution bound")
                if linearized_elements is None:
                    new = S3MaterialAnchorState(element,bary,old.cumulative_plastic_slip_m+plastic,
                                                old.cumulative_dissipation_Pa_m+dissipation,storage)
            records.append(dict(branch=branch, pressure_pa=pressure, traction_pa=traction.tolist(),
                                dissipation_increment_j=area*dissipation, storage_j=area*storage,
                                storage_change_j=area*(storage-old.stored_energy_Pa_m),
                                return_storage_drop_j=area*return_drop,
                                return_projection_loss_j=area*max(0.,return_drop-dissipation),
                                released_storage_j=area*old.stored_energy_Pa_m if branch=="open" else 0.,
                                sliding_seam=(branch=="slip" and min(bary) <= 128*np.finfo(float).eps),
                                sliding_rim=(branch=="slip" and self._on_rim(element,bary)),
                                target_element=element,target_barycentric=bary))
            records[-1]["first_touch"]=touch
            if new is not None:
                histories.append(new)
        if not local_force:
            global_residual=np.zeros(self.n_dof)
            global_residual[self.work_columns]=residual
            residual=global_residual
        return residual, tuple(histories), records

    def evaluate(self, displacement, *, tangent=True):
        force, stiffness, certificate = self.normal.evaluate(displacement, tangent=tangent)
        friction, _history, records = self._friction(displacement)
        if tangent:
            if any(r["sliding_rim"] for r in records):
                raise ValueError("physical target-rim generalized tangent is not yet admitted")
            derivative = np.zeros((len(self.work_columns),len(self.columns)))
            branches = [r["branch"] for r in records]
            elements = [r["target_element"] for r in records]
            coordinates = [r["target_barycentric"] for r in records]
            touch=[r["first_touch"] for r in records]
            for local, column in enumerate(self.columns):
                delta = np.zeros(self.n_dof)
                delta[column] = self.friction_settings.steps_by_dof[column]
                plus_probe = self._friction(np.asarray(displacement)+delta,branches=branches,validate=False,
                                      linearized_elements=elements,linearized_barycentric=coordinates,local_force=True,
                                      linearized_touch=touch)
                minus_probe = self._friction(np.asarray(displacement)-delta,branches=branches,validate=False,
                                       linearized_elements=elements,linearized_barycentric=coordinates,local_force=True,
                                       linearized_touch=touch)
                if any(r["sliding_rim"] for result in (plus_probe,minus_probe) for r in result[2]):
                    raise ValueError("physical target-rim derivative probe is not admitted")
                derivative[:, local] = (plus_probe[0]-minus_probe[0])/(2*delta[column])
            if not np.all(np.isfinite(derivative)):
                raise ValueError("material friction tangent exceeded finite range")
            rows, local = np.nonzero(derivative)
            stiffness = stiffness+sparse.coo_matrix((derivative[rows,local],
                (self.work_columns[rows],np.asarray(self.columns)[local])),shape=(self.n_dof,self.n_dof)).tocsr()
        return force+friction, stiffness, certificate

    def prepare_commit(self, displacement):
        u = np.asarray(displacement, dtype=float).copy()
        _force, history, records = self._friction(u)
        summary = dict(profile=PROFILE, branch=[r["branch"] for r in records],
                       friction_point_count=len(self.points),
                       source_quadrature_refinement=self.friction_settings.source_quadrature_refinement,
                       activation_history=self.friction_settings.activation_history,
                       first_touch_fraction=[None if r["first_touch"] is None else r["first_touch"][2] for r in records],
                       traction_measure="force_per_source_reference_area",
                       pressure_measure="shared_mortar_pressure_coefficient",
                       dissipation_measure="endpoint_pressure_current_material_chord",
                       pressure_pa=[r["pressure_pa"] for r in records],
                       traction_pa=[r["traction_pa"] for r in records],
                       target_elements=[r["target_element"] for r in records])
        for key in ("dissipation_increment_j", "storage_j", "storage_change_j",
                    "return_storage_drop_j", "return_projection_loss_j", "released_storage_j"):
            summary[key] = sum(r[key] for r in records)
        return u, history, summary

    def commit(self, prepared):
        self.committed_displacement, self.history, self.last_committed_summary = prepared

    def checkpoint_state(self):
        return dict(displacement=self.committed_displacement.tolist(), history=[asdict(h) for h in self.history])

    def restart_contract(self):
        return dict(normal=self.normal.restart_contract(), friction_profile=PROFILE,
                    friction_settings=asdict(self.friction_settings),
                    source_quadrature=[dict(element=p.adapter.element_id, barycentric=p.barycentric, weight_m2=w)
                                       for p, w in zip(self.points, self.weights)],
                    recontact=("stress_free_first_touch_projection" if self.friction_settings.activation_history
                               =="linear_constant_normal_touch_dev" else "stress_free_current_projection"),
                    activation_path=("affine_full_FE_constant_target_normal_v1" if self.friction_settings.activation_history
                                     =="linear_constant_normal_touch_dev" else "endpoint"),
                    tangent="bounded_fixed_return_facet_generalized_difference_v2")

    def restore(self, state, displacement):
        if type(state) is not dict or set(state) != {"displacement", "history"}:
            raise ValueError("invalid material-anchor checkpoint")
        u = np.asarray(state["displacement"], dtype=float)
        if u.shape != (self.n_dof,) or not np.array_equal(u, displacement) or not np.all(np.isfinite(u)):
            raise ValueError("material-anchor checkpoint pose differs from structural state")
        if len(state["history"]) != len(self.history):
            raise ValueError("material-anchor checkpoint point count differs")
        history = tuple(S3MaterialAnchorState(**h) for h in state["history"])
        corners, n, _frame, _origin = self._patch(u)
        Dn = self._normal_variation(corners,n)
        for point, h in zip(self.points, history):
            if h.target_element is not None and h.target_element not in self.target_adapters:
                raise ValueError("checkpoint anchor is outside the target material patch")
            if h.target_element is not None:
                e, _map, _y = self._work(point,u,h.target_element,h.barycentric,n,Dn)
                expected = .5*self.friction_settings.tangential_stiffness_Pa_per_m*float(e@e)
                if not np.isclose(expected,h.stored_energy_Pa_m,rtol=1e-9,atol=1e-12):
                    raise ValueError("checkpoint elastic storage differs from material anchor/pose")
        self.committed_displacement, self.history = u.copy(), history
        self.last_committed_summary = None
