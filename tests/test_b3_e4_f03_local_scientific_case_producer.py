from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_local_scientific_case_entry as case_entry
from scripts import _b3_e4_f03_local_scientific_case_producer as producer
from scripts import _b3_e4_f03_scaled_sparse as scaled_sparse
from scripts import _b3_e4_f03_sparse_factor_candidate as factor_candidate


DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
SOURCE = "d" * 40


class _Candidate:
    def __init__(self, blocks):
        self.q = np.array([1.0])
        self.eta = np.array([2.0, 3.0, 4.0])
        self.z = np.arange(4.0)
        self._blocks = blocks
        self.stream_calls = 0
        self.completed = False

    def inverse_blocks(self):
        self.stream_calls += 1
        for item in self._blocks:
            yield item
        self.completed = True

    @property
    def work(self):
        if not self.completed:
            raise AssertionError("work read before inverse stream completed")
        return {"complete": True}


def _harness(monkeypatch, directory: Path, *, fail_at=None):
    events = []

    def step(name, value=None):
        events.append(name)
        if name == fail_at:
            raise RuntimeError(name)
        return value

    def write(name):
        def operation(*args, **kwargs):
            step(f"write:{name}")
            path = directory.joinpath(*Path(name).parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(name.encode("ascii"))
        return operation

    blocks = (
        SimpleNamespace(start=0, columns=4, rows=8, name="inverse/block_0000_4.npy"),
        SimpleNamespace(start=4, columns=4, rows=8, name="inverse/block_0004_4.npy"),
    )
    plan = SimpleNamespace(case_id="q1_l0", inverse_blocks=blocks)
    case = SimpleNamespace(case_id="q1_l0", physical_dofs=5, degree=1)
    record = SimpleNamespace(case=case)
    records = (record,)
    grid = object()
    primary = SimpleNamespace(
        shell="primary-shell", beam="primary-beam", root="primary-root",
        load="primary-load", diagnostics="primary-diagnostics",
    )
    alternate = SimpleNamespace(
        shell="alternate-shell", beam="alternate-beam", root="alternate-root",
        load="alternate-load", diagnostics="alternate-diagnostics",
    )
    primary_scaled = SimpleNamespace(
        stiffness="primary-kbar", root="primary-cbar", matrix="primary-h",
        rhs="primary-b", diagonal="d", root_scale="r", metadata="primary-meta",
    )
    alternate_scaled = SimpleNamespace(
        stiffness="alternate-kbar", root="alternate-cbar", matrix="alternate-h",
        rhs="alternate-b", diagonal="d", root_scale="r", metadata="alternate-meta",
    )
    candidate = _Candidate(
        ((0, np.zeros((8, 4))), (4, np.zeros((8, 4))))
    )
    factors = SimpleNamespace(metadata="factor-meta")
    primary_operators = SimpleNamespace(
        shell="primary-shell", beam="primary-beam", root="primary-root",
        load="primary-load",
    )
    alternate_operators = SimpleNamespace(
        shell="alternate-shell", beam="alternate-beam", root="alternate-root",
        load="alternate-load",
    )
    scaled_evidence = SimpleNamespace(
        kbar="primary-kbar", d="d", h="primary-h", b="primary-b",
        q=candidate.q, eta=candidate.eta, z=candidate.z, h_z="h-z",
    )
    saved = SimpleNamespace(
        interface="saved-interface", work="saved-work", norm="saved-norm",
        support="support",
    )
    bundle = SimpleNamespace(trace="trace-budget", composition="composition-budget")

    monkeypatch.setattr(
        producer.archive, "read_plan_envelope",
        lambda path: step("read:plan-envelope", plan),
    )

    def start(*args):
        step("write:start.json")
        with (directory / "start.json").open("xb") as stream:
            stream.write(b"start")
        return DIGEST_A

    monkeypatch.setattr(producer.lifecycle, "write_start", start)
    monkeypatch.setattr(
        producer.archive, "validate_plan",
        lambda *args: step("validate:retained-envelope", plan),
    )
    monkeypatch.setattr(
        producer.archive, "read_plan",
        lambda *args: step("read:plan-full", plan),
    )
    monkeypatch.setattr(producer.archive, "_payload", lambda value: b"same-plan")
    monkeypatch.setattr(
        producer.budgets, "make_scientific_budgets",
        lambda: step("budgets:make", bundle),
    )
    monkeypatch.setattr(
        producer.budgets, "preflight_inventory",
        lambda value: step("budgets:preflight", ()),
    )
    monkeypatch.setattr(
        producer.cases, "compile_case",
        lambda value: step("compile:grid", grid),
    )

    def prepare_directory(path):
        step("write:inverse/")
        (directory / "inverse").mkdir()

    monkeypatch.setattr(producer.inverse_storage, "prepare_directory", prepare_directory)

    assembly_calls = []

    def assemble(grid_arg, budget, *, extra_beam_order, load_order):
        name = "assemble_alternate" if extra_beam_order else "assemble_primary"
        assembly_calls.append((grid_arg, extra_beam_order, load_order))
        return step(name, alternate if extra_beam_order else primary)

    monkeypatch.setattr(producer.assembly, "assemble", assemble)
    monkeypatch.setattr(
        producer, "_operator_evidence",
        lambda value: alternate_operators if value is alternate else primary_operators,
    )
    monkeypatch.setattr(
        producer.numerical_storage, "write_operators",
        lambda path, value, case: write(Path(path).name)(),
    )

    prepare_calls = []

    def prepare(shell, beam, root, load, budget, *, reference=None):
        prepare_calls.append((shell, beam, root, load, reference))
        if reference is None:
            return step("scale_primary", primary_scaled)
        assert reference is primary_scaled
        return step("scale_alternate", alternate_scaled)

    monkeypatch.setattr(producer.scaled_sparse, "prepare", prepare)
    monkeypatch.setattr(
        producer.scaled_sparse, "SolveBudget",
        lambda *args: step("budget:solve", "solve-budget"),
    )
    monkeypatch.setattr(
        producer.scaled_sparse, "solve_candidate",
        lambda system, budget: step("solve", candidate),
    )
    monkeypatch.setattr(producer, "_scaled_evidence", lambda *args: scaled_evidence)
    monkeypatch.setattr(
        producer.numerical_storage, "write_scaled",
        lambda path, value, case: write("scaled_state.npz")(),
    )
    monkeypatch.setattr(
        producer.factor_candidate, "FactorBudget",
        lambda *args: step("budget:factor", "factor-budget"),
    )
    monkeypatch.setattr(
        producer.factor_candidate, "produce",
        lambda matrix, budget: step("factor", factors),
    )
    monkeypatch.setattr(producer, "_positivity_evidence", lambda value: "positivity")
    monkeypatch.setattr(
        producer.numerical_storage, "write_positivity",
        lambda path, value, case: write("positivity.npz")(),
    )

    def write_block(directory_arg, plan_arg, start, value):
        expected = next(block for block in blocks if block.start == start)
        write(expected.name)()

    monkeypatch.setattr(producer.inverse_storage, "write_block", write_block)
    monkeypatch.setattr(
        producer.inverse_storage, "write_index",
        lambda *args: write("inverse_index.json")(),
    )
    monkeypatch.setattr(
        producer.port_factory, "produce_port_evidence",
        lambda *args, **kwargs: step("ports:produce", "ports"),
    )
    monkeypatch.setattr(
        producer.port_storage, "write_ports",
        lambda *args: write("ports.npz")(),
    )

    monkeypatch.setattr(
        producer.numerical_index, "NumericalEvidence",
        lambda *args: SimpleNamespace(parts=args),
    )
    monkeypatch.setattr(
        producer.numerical_index, "assembly_producer",
        lambda *args, **kwargs: step(
            "record:assembly_alternate" if kwargs["alternate"] else "record:assembly_primary",
            kwargs["alternate"],
        ),
    )
    monkeypatch.setattr(
        producer.numerical_index, "scaling_producer",
        lambda *args, **kwargs: step(
            "record:scaling_primary" if kwargs["primary"] else "record:scaling_alternate",
            kwargs["primary"],
        ),
    )
    monkeypatch.setattr(
        producer.numerical_index, "kkt_producer",
        lambda plan, work, **kwargs: step("record:kkt", work),
    )
    monkeypatch.setattr(
        producer.numerical_index, "positivity_producer",
        lambda *args: step("record:positivity", "positivity-record"),
    )
    monkeypatch.setattr(
        producer.numerical_index, "build_index",
        lambda *args: step("index:numerical", "numerical-index"),
    )

    def write_numerical(*args):
        write("numerical_index.json")()
        return DIGEST_B

    monkeypatch.setattr(producer.numerical_index, "write_index", write_numerical)
    monkeypatch.setattr(producer, "_produce_prolongation", lambda *args: "prolongation")

    def write_prolongation(*args):
        write("prolongations.npz")()
        write("prolongation_weights.json")()

    monkeypatch.setattr(producer.prolongation_storage, "write", write_prolongation)
    monkeypatch.setattr(
        producer.saved_factory, "produce_saved_observations",
        lambda *args, **kwargs: step("saved:produce", saved),
    )
    monkeypatch.setattr(
        producer.saved_storage, "write_interface",
        lambda *args: write("saved_interface.npz")(),
    )
    monkeypatch.setattr(
        producer.saved_storage, "write_work",
        lambda *args: write("saved_work.npz")(),
    )
    monkeypatch.setattr(
        producer.saved_storage, "write_norm",
        lambda *args: write("saved_norm.npz")(),
    )
    monkeypatch.setattr(
        producer.composition, "verify_composition",
        lambda *args, **kwargs: step("composition:verify", "composition"),
    )
    monkeypatch.setattr(
        producer.result_storage, "composition_summary",
        lambda value: step("composition:summarize", "summary"),
    )
    monkeypatch.setattr(
        producer.result_storage, "write_composition",
        lambda *args: write("saved_composition.npz")(),
    )
    monkeypatch.setattr(
        producer.result_storage, "balance_snapshot",
        lambda *args: step("balance:snapshot", "balance"),
    )
    monkeypatch.setattr(
        producer.result_storage, "write_balances",
        lambda *args: write("balances.npz")(),
    )

    def write_evidence(*args):
        write("evidence_index.json")()
        return SimpleNamespace(total_bytes=123), DIGEST_C

    monkeypatch.setattr(producer.evidence_index, "write_index", write_evidence)
    return SimpleNamespace(
        events=events,
        plan=plan,
        record=record,
        records=records,
        candidate=candidate,
        primary_scaled=primary_scaled,
        assembly_calls=assembly_calls,
        prepare_calls=prepare_calls,
    )


def test_case_producer_follows_exclusive_write_order_and_frozen_work(tmp_path, monkeypatch):
    harness = _harness(monkeypatch, tmp_path)
    result = producer.produce_case(
        tmp_path, harness.record, harness.records, SOURCE, DIGEST_A,
    )

    assert result == producer.ProducedCase("q1_l0", DIGEST_A, DIGEST_B, DIGEST_C, 123)
    assert harness.candidate.stream_calls == 1
    assert [(extra, order) for _, extra, order in harness.assembly_calls] == [
        (False, 48),
        (True, 64),
    ]
    assert harness.assembly_calls[0][0] is harness.assembly_calls[1][0]
    assert harness.prepare_calls[0][-1] is None
    assert harness.prepare_calls[1][-1] is harness.primary_scaled
    assert harness.events[:7] == [
        "read:plan-envelope",
        "write:start.json",
        "validate:retained-envelope",
        "read:plan-full",
        "budgets:make",
        "budgets:preflight",
        "compile:grid",
    ]
    assert harness.events.count("solve") == 1
    assert harness.events.count("factor") == 1
    writes = [event for event in harness.events if event.startswith("write:")]
    assert writes == [
        "write:start.json",
        "write:inverse/",
        "write:operators_primary.npz",
        "write:operators_alternate.npz",
        "write:scaled_state.npz",
        "write:positivity.npz",
        "write:inverse/block_0000_4.npy",
        "write:inverse/block_0004_4.npy",
        "write:inverse_index.json",
        "write:ports.npz",
        "write:numerical_index.json",
        "write:prolongations.npz",
        "write:prolongation_weights.json",
        "write:saved_interface.npz",
        "write:saved_work.npz",
        "write:saved_norm.npz",
        "write:saved_composition.npz",
        "write:balances.npz",
        "write:evidence_index.json",
    ]
    assert writes[-1] == "write:evidence_index.json"
    assert not (tmp_path / "terminal.json").exists()
    assert not (tmp_path / "case_receipt.json").exists()


def test_second_attempt_stops_at_exclusive_start_marker(tmp_path, monkeypatch):
    harness = _harness(monkeypatch, tmp_path)
    producer.produce_case(tmp_path, harness.record, harness.records, SOURCE, DIGEST_A)
    before = tuple(harness.events)
    with pytest.raises(FileExistsError):
        producer.produce_case(tmp_path, harness.record, harness.records, SOURCE, DIGEST_A)
    assert tuple(harness.events[len(before):]) == (
        "read:plan-envelope", "write:start.json",
    )


def test_process_route_builds_inventory_only_after_exclusive_start(tmp_path, monkeypatch):
    harness = _harness(monkeypatch, tmp_path)
    monkeypatch.setattr(
        producer.cases,
        "preflight_inventory",
        lambda: harness.events.append("cases:preflight-inventory") or harness.records,
    )
    result = producer.produce_registered_case(tmp_path, SOURCE, DIGEST_A)
    assert result.case_id == "q1_l0"
    assert harness.events[:4] == [
        "read:plan-envelope",
        "write:start.json",
        "cases:preflight-inventory",
        "validate:retained-envelope",
    ]


def test_process_entry_forwards_only_registered_child_inputs(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        case_entry.producer,
        "produce_registered_case",
        lambda *args: calls.append(args),
    )
    assert case_entry.main((
        "--directory", str(tmp_path),
        "--source-commit", SOURCE,
        "--registration-sha256", DIGEST_A,
    )) == 0
    assert calls == [(tmp_path, SOURCE, DIGEST_A)]


@pytest.mark.parametrize(
    "failure",
    (
        "validate:retained-envelope",
        "read:plan-full",
        "assemble_primary",
        "solve",
        "factor",
        "write:inverse/block_0004_4.npy",
        "write:numerical_index.json",
        "saved:produce",
        "write:saved_interface.npz",
        "composition:verify",
        "write:evidence_index.json",
    ),
)
def test_failures_leave_consumed_partial_evidence_without_terminal_files(
    tmp_path, monkeypatch, failure,
):
    harness = _harness(monkeypatch, tmp_path, fail_at=failure)
    with pytest.raises(RuntimeError, match=failure):
        producer.produce_case(tmp_path, harness.record, harness.records, SOURCE, DIGEST_A)
    assert (tmp_path / "start.json").is_file()
    assert not (tmp_path / "terminal.json").exists()
    assert not (tmp_path / "case_receipt.json").exists()
    assert not (tmp_path / "evidence_index.json").exists()


def test_source_or_plan_mismatch_occurs_after_start_and_before_model_work(
    tmp_path, monkeypatch,
):
    harness = _harness(monkeypatch, tmp_path, fail_at="validate:retained-envelope")
    with pytest.raises(RuntimeError, match="validate:retained-envelope"):
        producer.produce_case(tmp_path, harness.record, harness.records, "0" * 40, DIGEST_A)
    assert (tmp_path / "start.json").is_file()
    assert "compile:grid" not in harness.events
    assert "write:inverse/" not in harness.events


def test_plan_swap_after_start_is_rejected_before_budget_or_model_work(
    tmp_path, monkeypatch,
):
    harness = _harness(monkeypatch, tmp_path)
    payloads = iter((b"retained-plan", b"replacement-plan"))
    monkeypatch.setattr(producer.archive, "_payload", lambda value: next(payloads))
    with pytest.raises(ValueError, match="changed after start"):
        producer.produce_case(tmp_path, harness.record, harness.records, SOURCE, DIGEST_A)
    assert (tmp_path / "start.json").is_file()
    assert "budgets:make" not in harness.events
    assert "compile:grid" not in harness.events
    assert "write:inverse/" not in harness.events


@pytest.mark.parametrize(
    ("blocks", "message"),
    (
        (((0, np.zeros((8, 4))),), "incomplete"),
        (
            (
                (0, np.zeros((8, 4))),
                (3, np.zeros((8, 4))),
            ),
            "disagrees",
        ),
        (
            (
                (0, np.zeros((8, 4))),
                (4, np.zeros((8, 4))),
                (8, np.zeros((8, 1))),
            ),
            "extra",
        ),
    ),
)
def test_inverse_stream_rejects_missing_misaligned_and_extra_blocks(
    tmp_path, monkeypatch, blocks, message,
):
    plan = SimpleNamespace(
        inverse_blocks=(SimpleNamespace(start=0), SimpleNamespace(start=4)),
    )
    candidate = _Candidate(blocks)
    written = []
    monkeypatch.setattr(
        producer.inverse_storage, "write_block",
        lambda directory, plan, start, value: written.append(start),
    )
    with pytest.raises(ArithmeticError, match=message):
        producer._stream_inverse_blocks(tmp_path, plan, candidate)
    assert candidate.stream_calls == 1
    assert written == ([0] if message != "extra" else [0, 4])


def _scaled_system(stiffness, root, matrix, rhs, diagonal, root_scale):
    value = object.__new__(scaled_sparse.ScaledSystem)
    for name, item in (
        ("_stiffness", stiffness),
        ("_root", root),
        ("_matrix", matrix),
        ("_rhs", rhs),
        ("_diagonal", diagonal),
        ("_root_scale", root_scale),
        ("_metadata", MappingProxyType({})),
    ):
        object.__setattr__(value, name, item)
    return value


def test_scaled_evidence_uses_primary_state_and_independent_hz():
    k0 = sparse.eye(2, format="csr")
    c0 = sparse.csr_matrix(np.ones((3, 2)))
    h0 = sparse.eye(5, format="csc")
    k1 = sparse.csr_matrix(2 * np.eye(2))
    c1 = sparse.csr_matrix(2 * np.ones((3, 2)))
    h1 = sparse.csc_matrix(2 * np.eye(5))
    primary = _scaled_system(
        k0, c0, h0, np.arange(5.0), np.ones(2), np.ones(3),
    )
    alternate = _scaled_system(
        k1, c1, h1, np.arange(5.0) + 1, np.ones(2), np.ones(3),
    )
    candidate = object.__new__(scaled_sparse.SparseCandidate)
    candidate._z = np.arange(5.0)
    candidate._q = np.array([1.0, 2.0])
    candidate._eta = np.array([3.0, 4.0, 5.0])
    candidate._work = {}
    candidate._inverse_started = False
    candidate._system = primary
    candidate._factor = None
    candidate._budget = None

    value = producer._scaled_evidence(primary, alternate, candidate)
    np.testing.assert_array_equal(value.h_z, candidate.z)
    assert value.h_z.flags.c_contiguous
    assert not np.shares_memory(value.h_z, candidate.z)
    np.testing.assert_array_equal(value.d, primary.diagonal)
    np.testing.assert_array_equal(value.r, primary.root_scale)
    np.testing.assert_array_equal(value.b_alternate, alternate.rhs)


def test_positivity_evidence_persists_inverse_gather_semantics():
    value = object.__new__(factor_candidate.FactorCandidate)
    for name, item in (
        ("_matrix", sparse.eye(3, format="csr")),
        ("_lower", sparse.eye(3, format="csr")),
        ("_upper", sparse.eye(3, format="csr")),
        ("_diagonal", np.ones(3)),
        ("_row_map", np.array([1, 2, 0], dtype=np.int64)),
        ("_column_map", np.array([2, 0, 1], dtype=np.int64)),
        ("_permutation", (1, 2, 0)),
        ("_metadata", MappingProxyType({})),
    ):
        object.__setattr__(value, name, item)

    evidence = producer._positivity_evidence(value)
    np.testing.assert_array_equal(evidence.inverse_gather, [1, 2, 0])
    assert evidence.inverse_gather.dtype == np.int64
    assert evidence.inverse_gather.flags.c_contiguous


def test_producer_source_has_no_supervision_or_terminal_writer_calls():
    source = Path(producer.__file__).read_text("utf-8")
    for forbidden in (
        "_local_scientific_supervisor",
        "write_terminal(",
        "write_receipt(",
        "register(",
        "adjudicate(",
    ):
        assert forbidden not in source
