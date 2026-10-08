"""Independent continuous Timoshenko beam with finite, exact P0 means.

Development reference only. No native element, attachment or sparse solver is
used. Both endpoint translations are fixed; root spin is free and tip moment
is prescribed. Positive physical line force p satisfies V'=-p, M'=-V,
M=EI*phi', V=kGA*(u'-phi). Each support enforces integral(u)=0.
"""
from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class P0CarrierReference:
    length: float
    bending: float
    shear: float
    moment: float
    boundaries: np.ndarray
    starts: np.ndarray
    densities: np.ndarray
    rho: float
    scaled_condition: float
    backward_error: float

    def fields(self, x):
        """Physical u, phi, V, M; continuous at support boundaries."""
        x = np.asarray(x, dtype=float)
        if not np.all(np.isfinite(x)) or np.any(x < 0.) or np.any(x > self.length):
            raise ValueError("finite in-member coordinate required")
        t = x / self.length
        i = np.clip(np.searchsorted(self.boundaries, t, side="right")-1,
                    0, len(self.densities)-1)
        s = t-self.boundaries[i]
        u, phi, v, m = np.moveaxis(self.starts[i], -1, 0)
        p = self.densities[i]
        return np.array((
            (u+(phi+self.rho*v)*s+(m-self.rho*p)*s*s/2-v*s**3/6+p*s**4/24)
            *self.moment*self.length**2/self.bending,
            (phi+m*s-v*s*s/2+p*s**3/6)*self.moment*self.length/self.bending,
            (v-p*s)*self.moment/self.length,
            (m-v*s+p*s*s/2)*self.moment))

    def transfer_moments(self, highest=3):
        """Beam-side integral(x**k * p dx), about x=0, without force arms."""
        return np.array([
            self.moment*self.length**(k-1)
            *np.sum(self.densities*np.diff(self.boundaries**(k+1))/(k+1))
            for k in range(highest+1)])

    def controls(self):
        # Four-point Gauss is exact for these polynomial fields and their energy.
        xi, wi = np.polynomial.legendre.leggauss(4)
        a, b = self.boundaries[:-1], self.boundaries[1:]
        x = self.length*(a[:, None]+(b-a)[:, None]*(xi+1)/2)
        u, phi, v, m = self.fields(x)
        weights = self.length*(b-a)[:, None]*wi/2
        means = np.sum(weights*u, axis=1)
        energy = float(np.sum(weights*(v*v/self.shear+m*m/self.bending)))
        end = self.fields(np.array((0., self.length)))
        work = float(self.moment*end[1, 1])
        line_work = float(np.sum(self.densities*self.moment/self.length**2*means))
        displacement_scale = abs(self.moment)*self.length**2/self.bending
        moment_scale = abs(self.moment)
        transfer = self.transfer_moments(1)
        root, tip = -float(end[2, 0]), float(end[2, 1])
        return dict(
            scaled_support_mean=float(np.max(abs(means)/(self.length*(b-a)*displacement_scale))),
            scaled_endpoint_displacement=float(np.max(abs(end[0]))/displacement_scale),
            scaled_endpoint_moment=float(max(abs(end[3, 0]), abs(end[3, 1]-self.moment))/moment_scale),
            energy_work=abs(energy-work)/max(abs(work), np.finfo(float).tiny),
            line_work=abs(line_work)/max(abs(work), np.finfo(float).tiny),
            force_balance=abs(root+tip+transfer[0])*self.length/moment_scale,
            moment_balance=abs(tip*self.length+transfer[1]+self.moment)/moment_scale,
            energy=energy, work=work, endpoint_reactions=[root, tip],
            scaled_condition=self.scaled_condition, backward_error=self.backward_error)


def solve_p0_carrier(length, bending, shear, moment, support_endpoints):
    """Solve a bounded (support_count+2) system by exact interval propagation.

    With t=x/L, u=Mtip*L²/EI*v, phi=Mtip*L/EI*theta, V=Mtip/L*s,
    p=Mtip/L²*w, the only section parameter is rho=EI/(kGA*L²).
    Unknowns are theta(0), s(0), and one w per support. Initial v=m=0;
    final v=0,m=1 and all support means=0 determine the unknowns.
    """
    values = (length, bending, shear, moment)
    if (not all(math.isfinite(v) for v in values) or
            min(length, bending, shear) <= 0. or moment == 0.):
        raise ValueError("finite positive section/length and nonzero moment required")
    endpoints = np.array(support_endpoints, dtype=float, copy=True)
    if (endpoints.ndim != 1 or len(endpoints) < 2 or
            not np.all(np.isfinite(endpoints)) or endpoints[0] != 0. or
            endpoints[-1] != length or np.any(np.diff(endpoints) <= 0.)):
        raise ValueError("strictly increasing support partition of the complete beam required")
    t = endpoints/length
    rho = (bending/shear)/length**2
    if not math.isfinite(rho) or rho <= 0.:
        raise ValueError("section/length ratio is not representable")
    n = len(t)-1
    # Rows carry v,theta,s,m coefficient vectors; there is no affine state term.
    state = np.zeros((4, n+2))
    state[1, 0], state[2, 1] = 1., 1.
    rows, starts = [], []
    for i, h in enumerate(np.diff(t)):
        starts.append(state.copy())
        u, theta, v, m = state
        p = np.zeros(n+2); p[i+2] = 1.
        rows.append(u+(theta+rho*v)*h/2+(m-rho*p)*h*h/6-v*h**3/24+p*h**4/120)
        state = np.array((
            u+(theta+rho*v)*h+(m-rho*p)*h*h/2-v*h**3/6+p*h**4/24,
            theta+m*h-v*h*h/2+p*h**3/6,
            v-p*h,
            m-v*h+p*h*h/2))
    matrix = np.array(rows+[state[0], state[3]])
    rhs = np.zeros(n+2); rhs[-1] = 1.
    row_scale = np.max(abs(matrix), axis=1)
    if np.any(row_scale == 0.):
        raise ValueError("reference has an unsupported equation")
    scaled = matrix/row_scale[:, None]
    column_scale = np.max(abs(scaled), axis=0)
    if np.any(column_scale == 0.):
        raise ValueError("reference has an unsupported variable")
    scaled /= column_scale[None, :]
    unknowns = np.linalg.solve(scaled, rhs/row_scale)/column_scale
    backward = float(np.max(abs(matrix@unknowns-rhs)) /
                     (np.linalg.norm(matrix, ord=np.inf)*np.max(abs(unknowns))+1.))
    start_values = np.array(starts)@unknowns
    densities = unknowns[2:].copy()
    if not np.all(np.isfinite(start_values)) or not np.all(np.isfinite(densities)):
        raise ValueError("reference solution is nonfinite")
    for array in (t, start_values, densities): array.setflags(write=False)
    result = P0CarrierReference(length, bending, shear, moment, t, start_values,
                               densities, rho, float(np.linalg.cond(scaled)), backward)
    checks = result.controls()
    names = ("scaled_support_mean", "scaled_endpoint_displacement", "scaled_endpoint_moment",
             "energy_work", "line_work", "force_balance", "moment_balance", "backward_error")
    if any(not math.isfinite(checks[name]) or checks[name] > 1e-8 for name in names):
        raise ValueError("reference physical/numerical controls failed: "+str(checks))
    if checks["work"] <= 0. or checks["energy"] <= 0.:
        raise ValueError("reference work/energy must be positive")
    return result


def compare_saved_carrier(evidence_root):
    """Read only named, hashed saved mechanical outputs; launch no native solve."""
    import hashlib
    import io
    import json
    from pathlib import Path
    import zipfile
    from scipy.integrate import quad
    if __package__:
        from .r8_bl5_rigid_carrier_dev import carrier_reference
    else:
        from r8_bl5_rigid_carrier_dev import carrier_reference

    evidence_root = Path(evidence_root)
    manifest = json.loads((evidence_root/"raw-v1.json").read_text(encoding="utf-8-sig"))
    raw = (evidence_root/"raw-v1.zip").read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest["archive_sha256"]:
        raise ValueError("saved evidence archive identity changed")
    results = []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        def read(name):
            data = archive.read(name)
            if hashlib.sha256(data).hexdigest() != manifest["files"][name]:
                raise ValueError("saved member identity changed: "+name)
            return data
        for case in ("16x4-32", "32x8-64", "64x16-128"):
            prefix = "run-"+case+"/outputs/"
            summary = json.loads(read(prefix+"summary.json"))
            transfer = json.loads(read(prefix+"transfer.json"))
            p = summary["physical"]
            ref = solve_p0_carrier(p["length_m"], p["EI_z_Nm2"], p["kGA_y_N"],
                                   p["tip_moment_Nm"], summary["policy"]["support_endpoints_m"])
            moment_scale, length = abs(ref.moment), ref.length
            checks = ref.controls()
            endpoint = ref.fields(length)
            native = summary["native"]
            native_moments = [row[1] for row in transfer["polynomial_transfer_moments"]]
            records = transfer["station_records"]
            # Direct normal moment is released. Mz about the beam root is x*Fy;
            # verify this identity before interpreting the third force moment.
            if any(abs(r["beam_wrench_about_root_density"][5]-r["x_m"]*
                       r["beam_wrench_about_root_density"][1])*length/moment_scale > 1e-10
                   for r in records):
                raise ValueError("saved transfer does not have the admitted normal-spin work map")
            native_moments.append(sum(r["measure_m"]*r["x_m"]**3*
                                     r["beam_wrench_about_root_density"][1] for r in records))
            with np.load(io.BytesIO(read(prefix+"state.npz")), allow_pickle=False) as state:
                halfcells = summary["policy"]["beam_halfcells"]
                shell_nodes = len(state["xyz"])-halfcells-1
                native_reactions = state["reactions"][[6*shell_nodes+1, 6*(len(state["xyz"])-1)+1]]
                np.testing.assert_allclose(state["xyz"][shell_nodes:, 0],
                                           np.linspace(0., length, halfcells+1), atol=1e-14, rtol=0.)
            ref_moments = ref.transfer_moments(3)
            strong_moments = np.array([quad(
                lambda x: x**k*ref.shear*carrier_reference(
                    ref.length, ref.bending, ref.shear, ref.moment, x)[1],
                0., length, epsabs=moment_scale*length**(k-1)*1e-12,
                epsrel=1e-12)[0] for k in range(4)])
            results.append(dict(case=case, support_count=len(ref.densities),
                reference_controls=checks,
                physical_reference=dict(phi_tip_rad=float(endpoint[1]),
                    endpoint_reactions=checks["endpoint_reactions"],
                    force_moments=ref_moments.tolist(),
                    support_force_density_N_per_m=(ref.densities*ref.moment/length**2).tolist()),
                native=dict(phi_tip_rad=native["phi_tip_rad"],
                    endpoint_reactions=native_reactions.tolist(),force_moments=native_moments),
                native_vs_same_p0=dict(tip_spin_relative=native["phi_tip_rad"]/float(endpoint[1])-1.,
                    force_moment_relative=(np.array(native_moments)/ref_moments-1.).tolist(),
                    reaction_difference_applied_force_scale=(
                        (native_reactions-np.array(checks["endpoint_reactions"]))*length/moment_scale).tolist()),
                strong_tie_force_moments=strong_moments.tolist(),
                same_p0_vs_strong_tie=dict(tip_spin_relative=float(endpoint[1])/summary["analytic"]["phi_tip_rad"]-1.,
                    force_moment_relative=(ref_moments/strong_moments-1.).tolist()),
                saved_summary_sha256=manifest["files"][prefix+"summary.json"],
                saved_transfer_sha256=manifest["files"][prefix+"transfer.json"],
                saved_state_sha256=manifest["files"][prefix+"state.npz"]))
    return dict(status="COMPLETED_DEVELOPMENT_ONLY", reference="continuous Timoshenko with actual finite P0 means",
                saved_archive_sha256=manifest["archive_sha256"], cases=results,
                scope="rigid carrier, straight uncoupled section, released normal spin; not M2/F03 acceptance")


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saved-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    report = compare_saved_carrier(args.saved_evidence)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "cases": [
        {"case": r["case"], "tip_relative": r["native_vs_same_p0"]["tip_spin_relative"],
         "transfer_relative": r["native_vs_same_p0"]["force_moment_relative"]} for r in report["cases"]]}))
