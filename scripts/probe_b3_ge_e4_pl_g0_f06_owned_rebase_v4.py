"""G0-only owner-issued loaded chart rebase and restart prototype.

This is deliberately separate from the V1 coupled owner and its checkpoint.
It admits only the curved S3 fixture below and one rebase at cursor two.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from threading import Lock
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from anysolver.control import cancellation_safe_point
from anysolver._ge_beam3_g3c_local_shell import deformation
from anysolver._ge_beam3_pose_joint import _exp_terms
from anysolver._ge_beam3_p5_seeded.core import canonical
from anysolver._ge_beam3_shell_joint_state import (
    CoupledShellBeamAnalysis, SCHEMA as LEGACY_SCHEMA, decode, decoded_array,
)
from anysolver._ge_beam3_shell_joint_trial import ShellBeamTrial
from anysolver._native_reference_modal import _owned

from scripts.probe_b3_ge_e4_pl_g0_f06_loaded_rebase_v3 import fixture, shell_spatial


SCHEMA = "G0_F06_CURVED_S3_OWNED_REBASE_PROTOTYPE_V1"
TARGETS = (.5, 1., .75)


def _hash(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _near(a, b, label, tolerance=1.e-9):
    x, y = np.asarray(a), np.asarray(b)
    if x.shape != y.shape or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError(f"F06 {label} shape/nonfinite disagreement")
    if np.linalg.norm(x-y) > tolerance*max(1., np.linalg.norm(x), np.linalg.norm(y)):
        raise ValueError(f"F06 {label} physical disagreement")


def physical_tangent(response, u, count):
    """Columns in left-spatial shell increments; other columns unchanged."""
    p = np.eye(count)
    for i, row in enumerate(u.reshape(-1, 6)):
        _, jac, _ = _exp_terms(row[3:])
        p[6*i+3:6*i+6, 6*i+3:6*i+6] = jac
    return np.linalg.solve(p.T, response.tangent.T).T


def _check_tangent_directions(old, old_u, new, new_u, count):
    left, right = physical_tangent(old, old_u, count), physical_tangent(new, new_u, count)
    rng = np.random.default_rng(606)
    for index in range(3):
        direction = rng.standard_normal(count)
        direction /= np.linalg.norm(direction)
        _near(left@direction, right@direction, f"chart tangent direction {index}")


@dataclass(frozen=True)
class PrototypeState:
    mechanical: object
    shell_u: np.ndarray
    multipliers: np.ndarray
    beam_origins: tuple
    beam_histories: tuple
    shell_origin: bytes
    shell_history: bytes
    anchor: np.ndarray
    cursor: int

    def descriptor(self):
        return dict(mechanical=self.mechanical, shell_u=self.shell_u,
            multipliers=self.multipliers, beam_origins=self.beam_origins,
            beam_histories=self.beam_histories, shell_origin=decode(self.shell_origin),
            shell_history=decode(self.shell_history), anchor=self.anchor, cursor=self.cursor)


@dataclass(frozen=True)
class PrototypeRun:
    state: PrototypeState
    checkpoint: bytes
    status: str

    @property
    def checkpoint_sha256(self):
        return _hash(self.checkpoint)


class OwnedRebasePrototype:
    """Owns an event checkpoint and the one anchored successor transaction."""

    def __init__(self):
        seed = fixture("S3-V2D", True)
        self.owner = CoupledShellBeamAnalysis(seed.assembly, targets=TARGETS,
            shell_fixed=seed.shell_fixed, nodal_forces=seed.forces,
            max_iterations=seed.max_iterations, max_backtracks=seed.max_backtracks)
        self._lock = Lock()
        self._consumed_base = set()
        self._head_sha256 = None
        self._generation = None

    @property
    def head_sha256(self):
        return self._head_sha256

    @property
    def generation(self):
        return self._generation

    def legacy_prefix(self):
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("concurrent F06 prototype operation")
        try:
            run = self.owner.solve(stop_after=2)
            if run.status == "paused" and run.state.cursor == 2 and self._head_sha256 is None:
                self._head_sha256, self._generation = _hash(run.checkpoint), 0
            return run
        finally:
            self._lock.release()

    def _anchored_evaluate(self, predecessor, mechanical, u, multipliers, cursor):
        owner = self.owner; a = owner.assembly
        owner.guard()
        mechanical, u, multipliers = owner._arrays(mechanical, u, multipliers)
        parameter = owner.targets[cursor-1]
        origins, shell_origin = predecessor.beam_histories, predecessor.shell_history
        br, bj, _, responses, _ = a.beam.assemble(mechanical, parameter, origins)
        kin = deformation(np.asarray(a.coordinates), u, predecessor.anchor)
        sr, spatial_jac, _, candidate = shell_spatial(a, decode(shell_origin), kin, u)
        p = np.eye(a.shell_count)
        for i, row in enumerate(u.reshape(-1, 6)):
            _, jac, _ = _exp_terms(row[3:])
            p[6*i+3:6*i+6, 6*i+3:6*i+6] = jac
        sj = spatial_jac@p
        bi = a.beam.index[a.beam_node]
        shell = u.reshape(-1, 6)[a.shell_node]
        ports = a.joint.evaluate_ports(
            np.array([a.coordinates[a.shell_node]+shell[:3], mechanical.positions[bi]]),
            np.array([predecessor.anchor[a.shell_node]@a.frame,
                      mechanical.nodal_frames[bi]]), multipliers,
            rotation_coordinates=np.array([shell[3:], np.zeros(3)]),
            charted_ports=(True, False),
            position_low=np.array([np.zeros(3), mechanical.position_low[bi]]))
        jr = ports.pose.residual
        jj = ports.pose.spatial_jacobian@ports.coordinate_map
        residual = np.r_[sr, br, np.zeros(6)]
        tangent = np.zeros((a.count, a.count))
        tangent[:a.shell_count, :a.shell_count] = sj
        tangent[a.shell_count:-6, a.shell_count:-6] = bj
        residual[list(a.slots)] += jr
        tangent[np.ix_(a.slots, a.slots)] += jj
        if not np.isfinite(residual).all() or not np.isfinite(tangent).all():
            raise ValueError("nonfinite anchored F06 trial")
        fingerprint = _hash(canonical(dict(mechanical=mechanical, shell_u=u,
            multipliers=multipliers, anchor=predecessor.anchor, parameter=parameter)))
        response = ShellBeamTrial(a.identity, _hash(canonical(predecessor.descriptor())),
            fingerprint, _owned(residual), _owned(tangent), ports.pose.constraints,
            _owned(jr), _owned(jj), canonical(candidate),
            canonical(tuple(r.history for r in responses)))
        loaded = residual.copy()
        loaded[:len(owner.forces)] -= parameter*owner.forces
        owner.guard()
        return response, loaded

    def _rebased_state(self, base):
        a = self.owner.assembly; n = len(a.coordinates)
        anchor = np.array([_exp_terms(row[3:])[0]
            for row in base.shell_u.reshape(n, 6)])
        u = np.array(base.shell_u, copy=True)
        u.reshape(n, 6)[:, 3:] = 0.
        state = PrototypeState(base.mechanical, _owned(u), base.multipliers,
            base.beam_origins, base.beam_histories, base.shell_origin,
            base.shell_history, _owned(anchor), base.cursor)
        old = deformation(np.asarray(a.coordinates), base.shell_u,
            np.tile(np.eye(3), (n, 1, 1)))
        new = deformation(np.asarray(a.coordinates), state.shell_u, state.anchor)
        for label in ("deformation", "rotations", "current_positions"):
            _near(getattr(old, label), getattr(new, label), label)
        old_response, old_residual, _, _ = self.owner._evaluate(base, base.mechanical,
            base.shell_u, base.multipliers, base.cursor)
        new_response, new_residual = self._anchored_evaluate(
            state, state.mechanical, state.shell_u, state.multipliers, state.cursor)
        _near(old_response.constraints, new_response.constraints, "joint gap")
        _near(old_residual, new_residual, "loaded residual")
        _check_tangent_directions(old_response, base.shell_u,
            new_response, state.shell_u, a.count)
        # Resolve translational forces and rotational moments separately.
        for axis, name in ((slice(0, 3), "force"), (slice(3, 6), "moment")):
            _near(old_residual[:a.shell_count].reshape(-1, 6)[:, axis],
                new_residual[:a.shell_count].reshape(-1, 6)[:, axis], name)
        origin = decode(base.shell_history)
        _, _, old_work, old_candidate = shell_spatial(a, origin, old, base.shell_u)
        _, _, new_work, new_candidate = shell_spatial(a, origin, new, state.shell_u)
        _near(old_work, new_work, "shell virtual work")
        for name in ("layer_strain", "layer_stress"):
            x, y = np.asarray(old_candidate[name]), np.asarray(new_candidate[name])
            if np.linalg.norm(x) <= 1.e-8 or np.linalg.norm(y) <= 1.e-8:
                raise ValueError(f"nontrivial S3 {name} response required")
            _near(x, y, name)
        if canonical(old_candidate) != canonical(new_candidate):
            # Numerical fields may differ in their final bits across charts.
            from scripts.probe_b3_ge_e4_pl_g0_f06_loaded_rebase_v3 import numeric_state
            p0, v0 = numeric_state(old_candidate)
            p1, v1 = numeric_state(new_candidate)
            if p0 != p1:
                raise ValueError("F06 shell material state paths changed")
            _near(v0, v1, "shell material history")
        if (state.beam_origins != base.beam_origins or
                canonical(state.beam_histories) != canonical(base.beam_histories) or
                state.shell_origin != base.shell_origin or
                state.shell_history != base.shell_history):
            raise ValueError("F06 accepted material history changed")
        return state

    def _event(self, base_checkpoint, base, state):
        return dict(schema=SCHEMA, definition_sha256=self.owner.identity,
            base_checkpoint=base_checkpoint.decode("ascii"),
            base_sha256=_hash(base_checkpoint), cursor=base.cursor,
            base_state=base.descriptor(),
            base_state_sha256=_hash(canonical(base.descriptor())),
            anchor=state.anchor, rebased_state=state.descriptor(),
            rebased_state_sha256=_hash(canonical(state.descriptor())),
            successor=None, production_qualified=False)

    def _snapshot_state(self, data, cursor=2):
        if type(data) is not dict or set(data) != {
                "mechanical", "shell_u", "multipliers", "beam_origins",
                "beam_histories", "shell_origin", "shell_history", "anchor", "cursor"}:
            raise ValueError("F06 direct rebased snapshot shape mismatch")
        if type(data["cursor"]) is not int or data["cursor"] != cursor:
            raise ValueError("F06 direct accepted snapshot cursor mismatch")
        beam = self.owner.assembly.beam
        n = len(self.owner.assembly.coordinates)
        state = PrototypeState(
            beam.make(data["mechanical"], decoded=True),
            decoded_array(data["shell_u"], (6*n,)),
            decoded_array(data["multipliers"], (6,)),
            beam.histories(data["beam_origins"], decoded=True),
            beam.histories(data["beam_histories"], decoded=True),
            canonical(data["shell_origin"]), canonical(data["shell_history"]),
            decoded_array(data["anchor"], (n, 3, 3)), cursor)
        if canonical(state.descriptor()) != canonical(data):
            raise ValueError("F06 direct rebased snapshot encoding mismatch")
        return state

    def _captured_base(self, raw, expected_sha256, captured):
        """Bind the directly captured cursor-two state to the V1 bytes."""
        if _hash(raw) != expected_sha256:
            raise ValueError("F06 prototype base hash mismatch")
        outer = decode(raw)
        if (type(outer) is not dict or set(outer) != {
                "schema", "policy", "definition_sha256", "definition", "initial",
                "records", "production_qualified"} or
                outer["schema"] != LEGACY_SCHEMA or
                outer["definition_sha256"] != self.owner.identity or
                outer["production_qualified"] is not False or
                type(outer["records"]) is not list or len(outer["records"]) != 2 or
                canonical(outer) != raw or
                canonical(outer["records"][-1]["state"]) != canonical(captured)):
            raise ValueError("F06 captured base/checkpoint state mismatch")
        n = len(self.owner.assembly.coordinates)
        fields = {key: captured[key] for key in (
            "mechanical", "shell_u", "multipliers", "beam_origins",
            "beam_histories", "shell_origin", "shell_history", "cursor")}
        fields["anchor"] = np.tile(np.eye(3), (n, 1, 1))
        return self._snapshot_state(fields)

    def rebase(self, checkpoint, *, expected_sha256, cancellation_token=None):
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("concurrent F06 prototype operation")
        try:
            cancellation_safe_point(cancellation_token, "f06.rebase.start")
            if type(checkpoint) is not bytes or _hash(checkpoint) != expected_sha256:
                raise ValueError("external F06 base checkpoint hash required")
            if self._head_sha256 is not None and self._head_sha256 != expected_sha256:
                raise ValueError("F06 stale base is not this owner's accepted head")
            if expected_sha256 in self._consumed_base:
                raise ValueError("F06 stale base generation already rebased by this owner")
            base, records = self.owner._restore(checkpoint, expected_sha256, cancellation_token)
            if base.cursor != 2 or len(records) != 2:
                raise ValueError("loaded cursor-two F06 prefix required")
            before = canonical(base.descriptor())
            state = self._rebased_state(base)
            if canonical(base.descriptor()) != before:
                raise ValueError("F06 base state mutated")
            event = self._event(checkpoint, base, state)
            raw = canonical(event)
            cancellation_safe_point(cancellation_token, "f06.rebase.before_commit")
            self._consumed_base.add(expected_sha256)
            self._head_sha256, self._generation = _hash(raw), 1
            return PrototypeRun(state, raw, "REBASED_AT_LOADED_CURSOR_2")
        finally:
            self._lock.release()

    def _accepted_successor(self, predecessor, mechanical, u, multipliers, iterations,
                            predecessor_sha256):
        owner = self.owner
        if type(iterations) is not int or not 0 <= iterations <= owner.max_iterations:
            raise ValueError("bounded F06 successor iteration count required")
        if type(predecessor_sha256) is not str or len(predecessor_sha256) != 64:
            raise ValueError("F06 successor predecessor generation hash required")
        mechanical, u, multipliers = owner._arrays(mechanical, u, multipliers)
        response, residual = self._anchored_evaluate(predecessor, mechanical, u,
            multipliers, 3)
        _, metric, correction = owner._step(response, residual, mechanical, u, multipliers)
        if max(metric, correction, float(np.linalg.norm(response.constraints))) > 1.e-11:
            raise ValueError("F06 anchored successor not equilibrated")
        histories = owner.assembly.beam.histories(decode(response.beam_histories), decoded=True)
        state = PrototypeState(mechanical, _owned(u), _owned(multipliers),
            predecessor.beam_histories, histories, predecessor.shell_history,
            response.shell_candidate, predecessor.anchor, 3)
        record = dict(generation=2, predecessor_sha256=predecessor_sha256,
            iterations=iterations, state=state.descriptor(),
            residual=residual, constraints=response.constraints, metric=metric,
            correction=correction, tangent_sha256=_hash(canonical(response.tangent)))
        return state, record

    def _direct_successor(self, predecessor, row, predecessor_sha256):
        """Decode the issued state and check one current trial, without replay."""
        required = {"generation", "predecessor_sha256", "iterations", "state",
            "residual", "constraints", "metric", "correction", "tangent_sha256"}
        if (type(row) is not dict or set(row) != required or row["generation"] != 2 or
                row["predecessor_sha256"] != predecessor_sha256 or
                type(row["iterations"]) is not int or
                not 0 <= row["iterations"] <= self.owner.max_iterations or
                type(row["tangent_sha256"]) is not str or
                len(row["tangent_sha256"]) != 64):
            raise ValueError("F06 successor generation/record mismatch")
        state = self._snapshot_state(row["state"], cursor=3)
        if (canonical(state.anchor) != canonical(predecessor.anchor) or
                canonical(state.beam_origins) != canonical(predecessor.beam_histories) or
                state.shell_origin != predecessor.shell_history):
            raise ValueError("F06 direct successor material/chart lineage mismatch")
        owner = self.owner; a = owner.assembly
        owner._arrays(state.mechanical, state.shell_u, state.multipliers)
        kin = deformation(np.asarray(a.coordinates), state.shell_u, state.anchor)
        bi = a.beam.index[a.beam_node]
        shell = state.shell_u.reshape(-1, 6)[a.shell_node]
        joint = a.joint.evaluate(
            np.array([kin.current_positions[a.shell_node],
                      state.mechanical.positions[bi]]),
            np.array([kin.rotations[a.shell_node]@a.frame,
                      state.mechanical.nodal_frames[bi]]), state.multipliers,
            position_low=np.array([np.zeros(3), state.mechanical.position_low[bi]]))
        constraints = decoded_array(row["constraints"], (6,))
        _near(joint.constraints, constraints, "direct successor joint gap")
        residual = decoded_array(row["residual"], (a.count,))
        metric = float(np.linalg.norm((residual/owner.scale)[list(owner.free)]))
        if (type(row["metric"]) is not float or type(row["correction"]) is not float or
                not np.isfinite((row["metric"], row["correction"])).all() or
                abs(metric-row["metric"]) > 1.e-13 or
                max(metric, row["correction"], float(np.linalg.norm(constraints))) > 1.e-11):
            raise ValueError("F06 direct successor equilibrium record mismatch")
        response, actual_residual = self._anchored_evaluate(predecessor,
            state.mechanical, state.shell_u, state.multipliers, 3)
        if state.shell_history != response.shell_candidate:
            raise ValueError("F06 direct successor shell history disagreement")
        beam_candidate = a.beam.histories(decode(response.beam_histories), decoded=True)
        if canonical(state.beam_histories) != canonical(beam_candidate):
            raise ValueError("F06 direct successor beam history disagreement")
        if canonical(actual_residual) != canonical(residual):
            raise ValueError("F06 direct successor residual disagreement")
        if _hash(canonical(response.tangent)) != row["tangent_sha256"]:
            raise ValueError("F06 direct successor tangent disagreement")
        if canonical(response.constraints) != canonical(constraints):
            raise ValueError("F06 direct successor trial gap disagreement")
        _, actual_metric, actual_correction = owner._step(response,
            actual_residual, state.mechanical, state.shell_u, state.multipliers)
        if (abs(actual_metric-row["metric"]) > 1.e-13 or
                abs(actual_correction-row["correction"]) > 1.e-13 or
                max(actual_metric, actual_correction,
                    float(np.linalg.norm(response.constraints))) > 1.e-11):
            raise ValueError("F06 direct successor correction disagreement")
        return state

    def _restore(self, checkpoint, expected_sha256, cancellation_token=None):
        if type(checkpoint) is not bytes or _hash(checkpoint) != expected_sha256:
            raise ValueError("external F06 prototype checkpoint hash required")
        value = decode(checkpoint)
        if (type(value) is not dict or set(value) != {
                "schema", "definition_sha256", "base_checkpoint", "base_sha256",
                "cursor", "base_state", "base_state_sha256", "anchor",
                "rebased_state", "rebased_state_sha256", "successor",
                "production_qualified"} or value["schema"] != SCHEMA or
                value["definition_sha256"] != self.owner.identity or
                value["production_qualified"] is not False or value["cursor"] != 2 or
                type(value["base_checkpoint"]) is not str):
            raise ValueError("F06 prototype checkpoint schema/identity mismatch")
        base_raw = value["base_checkpoint"].encode("ascii")
        if value["base_state_sha256"] != _hash(canonical(value["base_state"])):
            raise ValueError("F06 captured base state hash mismatch")
        base = self._captured_base(base_raw, value["base_sha256"], value["base_state"])
        # The continuation consumes the rebased snapshot directly. It validates
        # captured geometry and constitutive response, without V1 history replay.
        state = self._snapshot_state(value["rebased_state"])
        if (canonical(value["anchor"]) != canonical(state.anchor) or
                value["rebased_state_sha256"] != _hash(canonical(state.descriptor()))):
            raise ValueError("F06 prototype rebase event mismatch")
        oracle = self._rebased_state(base)
        if canonical(state.descriptor()) != canonical(oracle.descriptor()):
            raise ValueError("F06 prototype rebase event mismatch")
        if value["successor"] is not None:
            predecessor_sha256 = _hash(canonical({**value, "successor": None}))
            state = self._direct_successor(state, value["successor"], predecessor_sha256)
        cancellation_safe_point(cancellation_token, "f06.restore.complete")
        return state, value

    def audit_legacy_replay(self, checkpoint, *, expected_sha256):
        """Optional full V1 replay oracle, never called by normal restoration."""
        state, event = self._restore(checkpoint, expected_sha256)
        base_raw = event["base_checkpoint"].encode("ascii")
        legacy, records = self.owner._restore(base_raw, event["base_sha256"])
        if legacy.cursor != 2 or len(records) != 2:
            raise ValueError("F06 diagnostic V1 replay prefix mismatch")
        if canonical(legacy.descriptor()) != canonical(event["base_state"]):
            raise ValueError("F06 diagnostic V1 replay disagrees with captured base")
        if canonical(self._rebased_state(legacy).descriptor()) != canonical(event["rebased_state"]):
            raise ValueError("F06 diagnostic V1 replay disagrees with rebase")
        if event["successor"] is not None:
            row = event["successor"]
            predecessor = self._snapshot_state(event["rebased_state"])
            data = row["state"]
            mechanical = self.owner.assembly.beam.make(data["mechanical"], decoded=True)
            u = decoded_array(data["shell_u"], (self.owner.assembly.shell_count,))
            multipliers = decoded_array(data["multipliers"], (6,))
            replayed, expected = self._accepted_successor(predecessor, mechanical,
                u, multipliers, row["iterations"], row["predecessor_sha256"])
            if canonical(row) != canonical(expected) or canonical(state.descriptor()) != canonical(replayed.descriptor()):
                raise ValueError("F06 diagnostic successor replay disagreement")
        return state

    def restore(self, checkpoint, *, expected_sha256, cancellation_token=None):
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("concurrent F06 prototype operation")
        try:
            state, event = self._restore(checkpoint, expected_sha256, cancellation_token)
            predecessor_hash = _hash(canonical({**event, "successor": None}))
            admissible = {expected_sha256}
            if state.cursor == 2:
                admissible.add(event["base_sha256"])
            else:
                admissible.add(predecessor_hash)
            if self._head_sha256 is not None and self._head_sha256 not in admissible:
                raise ValueError("F06 stale restore disagrees with accepted head")
            cancellation_safe_point(cancellation_token, "f06.restore.before_commit")
            self._head_sha256 = expected_sha256
            self._generation = 1 if state.cursor == 2 else 2
            return state
        finally:
            self._lock.release()

    def continue_loaded(self, checkpoint, *, expected_sha256, cancellation_token=None):
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("concurrent F06 prototype operation")
        try:
            if self._head_sha256 is not None and self._head_sha256 != expected_sha256:
                raise ValueError("F06 stale successor predecessor is not accepted head")
            accepted, event = self._restore(checkpoint, expected_sha256, cancellation_token)
            if accepted.cursor != 2 or event["successor"] is not None:
                raise ValueError("one F06 anchored successor from rebase event required")
            self._head_sha256, self._generation = expected_sha256, 1
            owner = self.owner; a = owner.assembly
            mechanical, u, lm = accepted.mechanical, accepted.shell_u, accepted.multipliers
            for iteration in range(owner.max_iterations+1):
                cancellation_safe_point(cancellation_token, "f06.successor.before_assembly")
                response, residual = self._anchored_evaluate(accepted, mechanical, u, lm, 3)
                step, metric, correction = owner._step(response, residual, mechanical, u, lm)
                if max(metric, correction, float(np.linalg.norm(response.constraints))) <= 1.e-11:
                    proposed, record = self._accepted_successor(accepted, mechanical, u,
                        lm, iteration, expected_sha256)
                    output = canonical({**event, "successor": record})
                    cancellation_safe_point(cancellation_token, "f06.successor.before_commit")
                    self._head_sha256, self._generation = _hash(output), 2
                    return PrototypeRun(proposed, output, "ACCEPTED_LOADED_CURSOR_3")
                if iteration == owner.max_iterations:
                    raise RuntimeError("F06 anchored Newton limit")
                for cut in range(owner.max_backtracks+1):
                    cancellation_safe_point(cancellation_token, "f06.successor.before_trial")
                    delta = step*(.5**cut)
                    try:
                        candidate = a.beam.advance(mechanical, delta[a.shell_count:-6])
                        cu, cm = u+delta[:a.shell_count], lm+delta[-6:]
                        _, trial = self._anchored_evaluate(accepted, candidate, cu, cm, 3)
                    except ValueError as error:
                        if "requires cutback" in str(error):
                            continue
                        raise
                    changed = float(np.linalg.norm((trial/owner.scale)[list(owner.free)]))
                    if changed < metric:
                        mechanical, u, lm = candidate, cu, cm
                        break
                else:
                    raise RuntimeError("F06 anchored line search limit")
        finally:
            self._lock.release()


def main():
    """Run only the disposable curved-S3 prototype; emit no gate receipt."""
    source = OwnedRebasePrototype()
    prefix = source.legacy_prefix()
    if prefix.status != "paused" or prefix.state.cursor != 2:
        raise RuntimeError(f"loaded F06 seed failed: {prefix.status}: {prefix.failure}")
    rebased = source.rebase(prefix.checkpoint, expected_sha256=_hash(prefix.checkpoint))
    fresh = OwnedRebasePrototype()
    restored = fresh.restore(rebased.checkpoint,
        expected_sha256=rebased.checkpoint_sha256)
    successor = fresh.continue_loaded(rebased.checkpoint,
        expected_sha256=rebased.checkpoint_sha256)
    replayed = OwnedRebasePrototype().restore(successor.checkpoint,
        expected_sha256=successor.checkpoint_sha256)
    if restored.cursor != 2 or replayed.cursor != 3:
        raise RuntimeError("F06 prototype replay cursor disagreement")
    print(canonical(dict(scope="G0_SYNTHETIC_NOT_QUALIFICATION",
        rebase_status=rebased.status, successor_status=successor.status,
        target=TARGETS[2], rebase_sha256=rebased.checkpoint_sha256,
        successor_sha256=successor.checkpoint_sha256)).decode("ascii"))


if __name__ == "__main__":
    main()
