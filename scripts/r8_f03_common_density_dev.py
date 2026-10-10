"""Saved BL5 common physical-density actions and resultant-only stationarity.

Development decision support, not F03, a stability norm, or a physical solve.
Import is stdlib-only. Numerical routines are prospective until authorized.
No full retained condensation, added gauge support, or matrix symmetrization.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "docs/agent_plans/development/r8-bl5-matched-comparison-20261001/refinement-v1-raw/native/n16"
CAPTURE = ROOT / "docs/agent_plans/development/r8-bl5-external-operator-20261009/fy-fullgeneral-v3"
RAW_SHA = "ebacac2ea27341decc25a1a8ace6ca388b9b99391331f10f33297106804255b5"
NATIVE_SHA = "dd14400f93f5eaf53f54cc89300917c87326a8913aec2c1c1588d39c0af5c0d5"
BINARY_SHA = "25ba42e1672526137d765d9c3631d1403e091f54f5afcdb9242f9243c63c3a96"
SOURCE_CHANNELS = ("tx_N_per_m", "ty_N_per_m", "tz_N_per_m", "mx_N", "my_N")
LOCAL_HESSIAN_DEFECT_LIMIT = Fraction(1, 10**9)
RESULTANT_UNIT_CONGRUENCE = {"force_coordinates": 6, "force_scale_N": 1,
                             "moment_coordinates": 12, "moment_scale_Nm": 1,
                             "reference_length_m": 1, "work_scale_J": 1}


class ContractRefusal(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ContractRefusal(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def role_indices(layout):
    """All nodal six and cell rotations stay x; only 18/member are p."""
    counts = layout["counts"]
    require(counts["physical_dofs"] == 708 and counts["full_q"] == 1092 and
            counts["members"] == 16 and counts["retained_dofs"] == 384 and
            counts["retained_cell_rotations"] == 96 and
            counts["retained_resultants"] == 288,
            "only admitted 16x4 legacy BL5 saved fixture supported")
    x = list(range(708))
    blocks = []
    for member in range(16):
        offset = 708 + 24*member
        record = layout["retained_members"][member]
        require(record["member_index"] == member and
                record["retained_24_offset"] == offset and
                record["cell_rotation_slots"] == list(range(offset, offset+6)) and
                record["resultant_slots"] == list(range(offset+6, offset+24)),
                "actual retained role map disagrees with source24 layout")
        x.extend(range(offset, offset+6))
        blocks.append(tuple(range(offset+6, offset+24)))
    return tuple(x), tuple(blocks)


def native_density(source):
    """Physical support-major five channels -> native channel-major signs."""
    require(len(source) == 40, "eight P0 supports times five physical channels required")
    result = [0]*40
    for j in range(8):
        for row, channel, sign in ((0, 0, -1), (1, 1, -1), (2, 2, -1),
                                   (3, 4, -1), (4, 3, 1)):
            result[8*row+j] = sign*source[5*j+channel]
    return result


def exact_yaw_balance(source, applied_root_mz=0):
    """Declared constant-density beam yaw balance, no floating tolerance/gauge.

    Eight supports [j/8,(j+1)/8], beam root x=0, beam director ez.
    Director couples mx,my give no rz action. Traction offset is along ez.
    Only exact rational density data are accepted for this proof.
    """
    require(len(source) == 40, "40 source coefficients required")
    require(all(type(v) in (int, Fraction) for v in (*source, applied_root_mz)),
            "exact integer/rational declared densities and applied moment required")
    connection_mz = sum((Fraction(source[5*j+1]) *
                         (Fraction(j+1, 8)**2-Fraction(j, 8)**2)/2
                         for j in range(8)), Fraction())
    remainder = Fraction(applied_root_mz)-connection_mz
    require(remainder == 0,
            "unbalanced prescribed beam yaw load: original coupled saddle required")
    return {"applied_root_mz_Nm": Fraction(applied_root_mz),
            "connection_root_mz_Nm": connection_mz, "remainder_Nm": remainder}


def balanced_perturbation_basis():
    """39 independent physical density columns in the zero-yaw-work kernel.

    Leave all32 non-ty coordinates free. For each first seven ty coordinates,
    compensate at support7 by -(2j+1)/15. The omitted ty7 has nonzero weight
    15/128. Projection onto the other39 coordinates is the identity, proving
    independence and representation of every balanced40-vector without rank
    computation. This is a source basis, not a request for39 physical solves.
    """
    columns = []
    for i in range(40):
        if i == 36:  # source support7 ty
            continue
        column = [Fraction() for _ in range(40)]
        column[i] = Fraction(1)
        if i % 5 == 1:
            column[36] = -Fraction(2*(i//5)+1, 15)
        columns.append(tuple(column))
    return tuple(columns)


def proposed_comparison_actions():
    """Three independent source columns for a reserved future comparison.

    No execution or assessment is authorized by this selection. Unit density
    amplitudes name physical loads, not a norm or equivalence of primal fields.
    """
    basis = balanced_perturbation_basis()
    return {"support0_tx_1N_per_m": basis[0],
            "support0_mx_1N": basis[3],
            "support0_ty_1N_per_m_with_support7_compensation": basis[1]}


def source_binding():
    """Stdlib bytes/metadata only; no array decoding or operator execution."""
    require(sha(CAPTURE / "raw.json") == RAW_SHA, "captured raw identity changed")
    require(sha(NATIVE / "operators.npz") == NATIVE_SHA, "native operator identity changed")
    raw = json.loads((CAPTURE / "raw.json").read_text())
    layout = json.loads((NATIVE / "layout.json").read_text())
    role_indices(layout)
    require(raw["binary_sha256"] == BINARY_SHA and raw["opensees_version"] == "3.8.0",
            "adopted binary/version identity changed")
    require(raw["system_size"] == 783 and raw["analyze_code"] == 0,
            "complete successful captured system required")
    return {"native_operators_sha256": NATIVE_SHA, "external_raw_sha256": RAW_SHA,
            "binary_sha256": BINARY_SHA, "opensees_version": "3.8.0",
            "exact_cpp_build_commit": None,
            "layout_sha256": sha(NATIVE / "layout.json"),
            "inputs_sha256": sha(NATIVE / "inputs.json"),
            "capture_source_sha256": sha(CAPTURE / "executed-capture-source.py"),
            "physical_primal_dimensions": {"native_x": 804, "native_p": 288,
                                           "external_nodal": 708},
            "scope": "legacy BL5 n16/span4; not current L1/P0-span2 F03 family",
            "printA_order": "F", "qualification": False}


def decode_fullgeneral(raw):
    """Official Matrix storage is column-major; retain raw unsymmetry."""
    import numpy as np
    size = raw["system_size"]
    require(size == 783 and len(raw["printA"]) == size*size, "783 square capture required")
    matrix = np.asarray(raw["printA"], dtype=float).reshape((size, size), order="F")
    require(np.isfinite(matrix).all(), "finite captured entries required")
    return matrix


def external_physical_rows(raw, layout):
    """Original integrated MP rows, before dependent-row/Lagrange scaling."""
    import numpy as np
    nodes = [str(row["external_node"]) for row in layout["typed_physical_nodes"]]
    require(len(nodes) == 118 and len(set(nodes)) == 118, "typed node identity changed")
    coordinates = [(node, dof) for node in nodes for dof in range(1, 7)]
    lookup = {key: i for i, key in enumerate(coordinates)}
    ids = [raw["node_dofs"][node][dof-1] for node, dof in coordinates]
    require(len(set(ids)) == 708 and all(type(i) is int and 0 <= i < 783 for i in ids),
            "all physical coordinates must retain distinct equation IDs")
    rows = raw["raw_inventory"]["equations"]
    require(len(rows) == 40, "original40 MP rows required")
    c = np.zeros((40, 708))
    for j, row in enumerate(rows):
        require(len(row) % 3 == 0, "MP triple row malformed")
        seen = set()
        for node, dof, value in zip(row[::3], row[1::3], row[2::3]):
            key = (str(node), dof)
            require(key in lookup and key not in seen, "duplicate or unknown physical row term")
            seen.add(key)
            c[j, lookup[key]] = value
    require(np.isfinite(c).all(), "finite original MP rows required")
    return c, tuple(ids)


def _rational_rows(matrix):
    return [[Fraction(float(value)) for value in row] for row in matrix]


def _squared_frobenius(rows):
    return sum((value*value for row in rows for value in row), Fraction())


def _upper_sqrt(value):
    """Outward bound checked against exact rational square, not assumed ulps."""
    require(value >= 0, "nonnegative certificate squared norm required")
    if value == 0:
        return Fraction()
    try:
        made = math.sqrt(float(value))
    except (OverflowError, ValueError) as exc:
        raise ContractRefusal("certificate norm representation uncertain") from exc
    require(math.isfinite(made) and made > 0, "certificate norm representation uncertain")
    while Fraction(made)**2 < value:
        made = math.nextafter(made, math.inf)
    return Fraction(made)


def _exact_product(left, right):
    return [[sum((a*b for a, b in zip(row, column) if a and b), Fraction())
             for column in zip(*right)] for row in left]


def local_complementary_certificate(local):
    """Bounded represented-D feasibility, not a global mechanical norm.

    Qp has first6 physical 1N and last12 physical 1Nm entries; work scale1J.
    Thus G=Qp.T D Qp/1J has the same numeric SI entries for this fixture.
    Raw D is never replaced. Lower-completion H is only an auxiliary witness.
    Every residual/norm square below uses exact represented binary64 values.
    """
    import numpy as np
    require(local.shape == (18, 18) and np.isfinite(local).all(),
            "finite local18 complementary tangent required")
    g = _rational_rows(local)
    defect = [[g[i][j]-g[j][i] for j in range(18)] for i in range(18)]
    defect_squared = _squared_frobenius(defect)
    reference_squared = max(Fraction(1), _squared_frobenius(g))
    require(defect_squared <= LOCAL_HESSIAN_DEFECT_LIMIT**2*reference_squared,
            "local conservative-Hessian defect exceeds normalized1e-9; feasibility uncertain")
    # np.linalg.cholesky uses the lower triangle. Explicitly define that
    # witness matrix; it is not a replacement tangent or an entry average.
    h = np.tril(local) + np.tril(local, -1).T
    try:
        lower = np.linalg.cholesky(h)
        inverse_witness = np.linalg.solve(lower, np.eye(18))
    except np.linalg.LinAlgError as exc:
        raise ContractRefusal("local complementary quadratic certificate unavailable; feasibility uncertain") from exc
    require(np.isfinite(lower).all() and np.isfinite(inverse_witness).all(),
            "local certificate factors nonfinite; feasibility uncertain")
    hr, lr, xr = (_rational_rows(value) for value in (h, lower, inverse_witness))
    llt = _exact_product(lr, list(map(list, zip(*lr))))
    lx = _exact_product(lr, xr)
    residual = [[Fraction(i == j)-lx[i][j] for j in range(18)] for i in range(18)]
    r = _upper_sqrt(_squared_frobenius(residual))
    require(r < 1, "local inverse-factor witness unbounded; feasibility uncertain")
    x_squared = _squared_frobenius(xr)
    require(x_squared > 0, "nonzero local inverse witness required")
    beta = (1-r)**2/x_squared
    rho = _upper_sqrt(_squared_frobenius([[hr[i][j]-llt[i][j] for j in range(18)] for i in range(18)]))
    delta = _upper_sqrt(_squared_frobenius([[g[i][j]-hr[i][j] for j in range(18)] for i in range(18)]))
    lower_bound = beta-rho-delta
    require(lower_bound > 0,
            "local complementary quadratic positivity not certified; feasibility uncertain")
    return {"unit_congruence": RESULTANT_UNIT_CONGRUENCE.copy(),
            "conservative_Hessian_defect_limit": 1e-9,
            "represented_exact_symmetry": defect_squared == 0,
            "normalized_defect_upper": float(_upper_sqrt(defect_squared/reference_squared)),
            "inverse_factor_residual_upper": float(r),
            "factor_product_residual_upper": float(rho),
            "lower_completion_discrepancy_upper": float(delta),
            "quadratic_lower_bound": float(lower_bound),
            "strict_positive_lower_bound_proven_exactly": True,
            "bound_computation": "exact binary64 rational residuals and outward checked sqrt; auxiliary witness only"}


@dataclass
class CommonActions:
    native: object
    external: object

    def loads(self, source):
        import numpy as np
        source = np.asarray(source, dtype=float)
        require(source.shape == (40,) and np.isfinite(source).all(), "finite density40 required")
        return self.native @ source, self.external @ source

    def declared_body_loads(self, source, applied_root_mz):
        """Refuse unbalanced prescribed loading before mapping either body."""
        exact_yaw_balance(source, applied_root_mz)
        return self.loads(source)

    def perturbation_loads(self, source_base, source_delta, applied_root_mz):
        """Base balances applied load; delta balances zero applied yaw work."""
        exact_yaw_balance(source_base, applied_root_mz)
        exact_yaw_balance(source_delta, 0)
        return self.declared_body_loads([a+b for a, b in zip(source_base, source_delta)],
                                        applied_root_mz)


def common_actions(c_native, c_external):
    """Ln=-Cn.T T, Le=-Ce.T. ds is already in original physical rows."""
    import numpy as np
    require(c_native.shape == (40, 1092) and c_external.shape == (40, 708),
            "admitted action-map dimensions required")
    transform = np.column_stack([native_density([int(i == j) for i in range(40)])
                                 for j in range(40)])
    return CommonActions(-(c_native.T @ transform), -c_external.T.copy())


class ResultantStationarity:
    """K=[[A,E],[B,-D]], local complementary D only; no full-body solve.

    Does not assert full K SPD or interpret eliminated variables as mass.
    E and B are kept separately; no silent symmetry repair. A valid symmetric
    local D quadratic certificate is required. The original signed K remains unchanged.
    """
    def __init__(self, k, c, layout):
        import numpy as np
        self.np = np
        self.x, full_blocks = role_indices(layout)
        self.p = tuple(i for block in full_blocks for i in block)
        require(k.shape == (1092, 1092) and c.shape == (40, 1092), "saved shape changed")
        require(np.isfinite(k).all() and np.isfinite(c).all(), "finite saved operators required")
        require(np.count_nonzero(c[:, self.p]) == 0, "resultants must have zero trace action")
        self.k = k.copy()
        self.a = k[np.ix_(self.x, self.x)].copy()
        self.e = k[np.ix_(self.x, self.p)].copy()
        self.b = k[np.ix_(self.p, self.x)].copy()
        self.cx = c[:, self.x].copy()
        self.d = -k[np.ix_(self.p, self.p)].copy()
        self.local_d = []
        self.local_certificates = []
        offblock = self.d.copy()
        for j in range(16):
            segment = slice(18*j, 18*(j+1))
            local = self.d[segment, segment].copy()
            self.local_certificates.append(local_complementary_certificate(local))
            self.local_d.append(local)
            offblock[segment, segment] = 0
        require(np.count_nonzero(offblock) == 0, "cross-member resultant tangent prevents local lift")

    def solve_d(self, rhs):
        np = self.np
        rhs = np.asarray(rhs, dtype=float)
        require(rhs.shape[0] == 288 and np.isfinite(rhs).all(), "288 finite resultant RHS required")
        return np.concatenate([np.linalg.solve(d, rhs[18*j:18*(j+1)])
                               for j, d in enumerate(self.local_d)], axis=0)

    def lift(self, x, resultant_rhs=None):
        np = self.np
        x = np.asarray(x, dtype=float)
        require(x.shape == (804,) and np.isfinite(x).all(), "all804 finite mechanical x required")
        rp = np.zeros(288) if resultant_rhs is None else np.asarray(resultant_rhs, dtype=float)
        require(rp.shape == (288,) and np.isfinite(rp).all(), "finite resultant load288 required")
        q = np.empty(1092)
        q[list(self.x)] = x
        q[list(self.p)] = self.solve_d(self.b @ x-rp)
        return q

    def action(self, x):
        """Sx=Ax+E D^-1 Bx; no global inverse/dense Schur construction."""
        return self.a @ x + self.e @ self.solve_d(self.b @ x)

    def effective_rhs(self, full_rhs):
        """Retain ALL cell/nodal rotational loads: fx+E D^-1 fp."""
        np = self.np
        rhs = np.asarray(full_rhs, dtype=float)
        require(rhs.shape == (1092,) and np.isfinite(rhs).all(), "finite full load required")
        return rhs[list(self.x)] + self.e @ self.solve_d(rhs[list(self.p)])


def load_saved_contract():
    """Prospective saved-only API; no assembly, body/equilibrium solve or gauge."""
    binding = source_binding()
    import numpy as np
    from scipy import sparse
    raw = json.loads((CAPTURE / "raw.json").read_text())
    layout = json.loads((NATIVE / "layout.json").read_text())
    matrix = decode_fullgeneral(raw)
    ce, ids = external_physical_rows(raw, layout)
    ke = matrix[np.ix_(ids, ids)].copy()
    with np.load(NATIVE / "operators.npz", allow_pickle=False) as archive:
        operators = {name: np.array(archive[name], copy=True) for name in
                     ("K_data", "K_indices", "K_indptr", "K_shape",
                      "C_data", "C_indices", "C_indptr", "C_shape")}
    matrices = {tag: sparse.csr_matrix((operators[tag+"_data"], operators[tag+"_indices"],
                                       operators[tag+"_indptr"]),
                                      shape=tuple(operators[tag+"_shape"])).toarray()
                for tag in ("K", "C")}
    stationarity = ResultantStationarity(matrices["K"], matrices["C"], layout)
    return {"binding": binding, "native_K_signed": matrices["K"], "external_K": ke,
            "native_C": matrices["C"], "external_C_original": ce,
            "actions": common_actions(matrices["C"], ce), "stationarity": stationarity,
            "external_augmented_raw": matrix, "qualification": False}
