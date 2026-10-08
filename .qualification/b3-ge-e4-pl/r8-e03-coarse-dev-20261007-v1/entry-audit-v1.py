"""Root-launched E03 adapter; execution is deferred until the outer PS grant."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import threading
import time

RAW = Path(__file__).resolve().parent
REPO = RAW.parents[2]
mode, attempt, phase_attempt = sys.argv[1:4]
folder = RAW/attempt
manifest = json.loads((RAW/"inputs-manifest-audit-v1.json").read_text())
authority = json.loads((RAW/"authority-v1.json").read_text())
assert authority["status"] == "APPROVED" and authority["approval_evidence"]
assert authority["total_seconds"] == 240 and authority["reserve_seconds"] == 60
assert mode == "controls" and mode in authority["allowed_modes"]
sys.path.insert(0, manifest["ci_site"])
import psutil


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, value):
    target = folder/name
    temporary = target.with_suffix(target.suffix+".part")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, target)


process = psutil.Process()
process.cpu_affinity([0])
assert process.cpu_affinity() == [0]
samples, affinity_events, child_samples = [], [], []
ready, stop = threading.Event(), threading.Event()
started = time.perf_counter()


def monitor():
    # Reused E03 source-entry monitor; parent PS owns process-wall accounting.
    while not stop.is_set():
        try:
            tree = [process]+process.children(recursive=True)
            rss = sum(p.memory_info().rss for p in tree if p.is_running())
            samples.append(dict(seconds=time.perf_counter()-started, rss=rss))
            if len(samples) % 50 == 0:
                write("rss-partial.json", samples)
            for child in tree:
                if not child.is_running():
                    continue
                affinity = child.cpu_affinity()
                if child.name().lower() == "ccx.exe":
                    child_samples.append(dict(pid=child.pid, affinity=affinity, threads=child.num_threads()))
                if affinity != [0]:
                    event = dict(pid=child.pid, name=child.name(), before=affinity, numerical_ready=ready.is_set())
                    affinity_events.append(event)
                    if ready.is_set() and child.name().lower() != "conhost.exe":
                        write("affinity-failure.json", event)
                        for target in reversed(tree):
                            target.kill()
                    child.cpu_affinity([0])
            if rss > 2147483648:
                write("resource-failure.json", samples[-1])
                for target in reversed(tree):
                    target.kill()
        except psutil.NoSuchProcess:
            pass
        except Exception as error:
            write("monitor-failure.json", dict(type=type(error).__name__, reason=str(error)))
            process.kill()
        stop.wait(.02)


thread = threading.Thread(target=monitor, daemon=True)
thread.start()
try:
    inputs = RAW/"input-snapshots-audit-v1"
    assert sys.dont_write_bytecode and sys.pycache_prefix == str(folder/"pycache")
    assert all(sha(REPO/name) == digest == sha(inputs/name) for name, digest in manifest["inputs"].items())
    assert sha(__file__) == manifest["entry_sha256"]
    assert sha(RAW/"supervise-audit-v1.ps1") == manifest["supervisor_sha256"]
    artifact = json.loads(Path(manifest["artifact_path"]).read_text())
    assert sha(manifest["artifact_path"]) == manifest["artifact_sha256"]
    provider = Path(artifact["site"])
    sys.path[:0] = [str(provider), str(REPO)]
    import numpy
    import scipy
    import numba
    import llvmlite
    import anymaterial
    import anysolver
    from threadpoolctl import threadpool_info
    from scripts import r8_e03_coarse_screen as screen
    from scripts import r8_e03_curved_reference as reference
    from scripts import r8_e03_native_reference as native

    def runtime():
        return dict(executable=sys.executable, affinity=process.cpu_affinity(), pools=threadpool_info(),
            numba_threads=numba.get_num_threads(), jit_off=bool(numba.config.DISABLE_JIT),
            environment={key: os.environ.get(key) for key in manifest["thread_environment"]},
            versions={module.__name__:module.__version__ for module in (numpy, scipy, numba, llvmlite)},
            imports={module.__name__:module.__file__ for module in (numpy, scipy, numba, llvmlite, anymaterial, anysolver)})

    def validate_runtime(value):
        assert value["affinity"] == [0] and value["numba_threads"] == 1 and value["jit_off"]
        assert all(pool["num_threads"] == 1 for pool in value["pools"])
        assert value["environment"] == manifest["thread_environment"]
        assert os.environ.get("OPENBLAS_CORETYPE") is None
        assert value["versions"] == manifest["runtime_versions"]
        for module in (numpy, scipy, numba, llvmlite):
            assert Path(module.__file__).resolve().is_relative_to(Path(manifest["ci_site"]).resolve())
        assert Path(anymaterial.__file__).resolve() == Path(manifest["anymaterial_source"]).resolve()
        assert sha(anymaterial.__file__) == manifest["anymaterial_sha256"]
        assert Path(anysolver.__file__).resolve() == (provider/"anysolver/__init__.py").resolve()

    before = runtime()
    write("runtime-before.json", before)
    validate_runtime(before)
    write("python-launch.json", dict(command=list(sys.orig_argv), executable=sys.executable, cwd=str(Path.cwd())))
    case = reference.build_case(0, 1)
    phase = "native" if mode in ("controls", "native", "finalize-native") else "external"
    bindings = dict(phase=phase, case_id=case["case_id"], source_root=str(REPO),
        source_sha256={name:manifest["inputs"][name] for name in screen.SOURCE_FILES},
        wheel_path=artifact["wheel"], wheel_sha256=artifact["wheel_sha256"],
        installed_provider_root=str(provider),
        module_manifest_sha256=manifest["reused_module_manifest_sha256"],
        supervisor_id=manifest["supervisor_sha256"], execution_scope=authority["scope"],
        command=list(sys.orig_argv), native_capability_law=authority["native_capability_law"])
    if phase == "external":
        bindings.update(executable_path=str(screen.CCX_PATH), command=[str(screen.CCX_PATH), "-i", "e03"])
    # Same exact source/wheel/site parity applies to controls and physical phases.
    screen._bindings(bindings, phase)
    ready.set()
    code = 0
    try:
        if mode == "controls":
            import pytest
            class Reports:
                def pytest_runtest_logreport(self, report):
                    with (folder/"case-reports.jsonl").open("a", encoding="utf-8") as stream:
                        stream.write(json.dumps(dict(nodeid=report.nodeid, when=report.when,
                            outcome=report.outcome, duration=report.duration,
                            detail=str(report.longrepr) if report.failed else None))+"\n")
            args = ["-q", "-c", str(inputs/"pyproject.toml"), "-o", "pythonpath=",
                "--basetemp", str(folder/"temp"), "--junitxml="+str(folder/"junit.xml"),
                str(inputs/"tests/test_stiffened_shell_e03_equation_force_audit.py")]
            write("pytest-command.json", args)
            code = pytest.main(args, plugins=[Reports()])
        elif mode in ("native", "external"):
            prepared = screen.prepare_screen(phase, folder/"phase", bindings=bindings)
            write("phase-context.json", dict(phase=phase, prepared=str(prepared), bindings=bindings,
                anysolver_origin=anysolver.__file__, anysolver_origin_sha256=sha(anysolver.__file__)))
            if mode == "native":
                result = native.execute_b2(case)
                write("native-result.json", result)
            else:
                command = bindings["command"]
                env = os.environ.copy()
                child_started = time.perf_counter()
                child = None
                with (folder/"ccx-stdout.log").open("wb") as stdout, (folder/"ccx-stderr.log").open("wb") as stderr:
                    try:
                        child = subprocess.Popen(command, cwd=prepared, env=env, stdout=stdout, stderr=stderr)
                        actual = psutil.Process(child.pid)
                        write("ccx-launch.json", dict(command=command, cwd=str(prepared),
                            pid=child.pid, affinity=actual.cpu_affinity(), environment={key:env[key] for key in manifest["thread_environment"]}))
                        assert actual.cpu_affinity() == [0], "CCX CPU0 inheritance must be observed"
                        child_code = child.wait()
                    finally:
                        write("ccx-process.json", dict(command=command, cwd=str(prepared),
                            exit_code=child.poll() if child else None,
                            process_wall_seconds=time.perf_counter()-child_started,
                            executable_sha256=sha(screen.CCX_PATH)))
                if child_code != 0:
                    raise RuntimeError("CCX failed: "+str(child_code))
        else:
            # This is a separately supervised invocation AFTER outer execution.json exists.
            prior = RAW/phase_attempt
            context = json.loads((prior/"phase-context.json").read_text())
            outer_path = prior/"execution.json"
            outer = json.loads(outer_path.read_text())
            assert outer["mode"] == phase and outer["owned_child_exited"]
            assert outer["input_manifest_sha256"] == sha(RAW/"inputs-manifest-audit-v1.json")
            assert outer["entry_sha256"] == sha(__file__) and outer["supervisor_sha256"] == manifest["supervisor_sha256"]
            assert outer["authority_sha256"] == sha(RAW/"authority-v1.json")
            prior_bindings = context["bindings"]
            receipt = {key:prior_bindings[key] for key in ("phase", "case_id", "supervisor_id", "execution_scope", "command",
                "wheel_sha256", "source_sha256", "module_manifest_sha256")}
            prepared = Path(context["prepared"])
            metadata = json.loads((prepared/"metadata.json").read_text())
            receipt.update(deck_sha256=metadata["deck_sha256"], exit_code=outer["exit_code"],
                timed_out=outer["status"] == "timeout", process_wall_seconds=outer["process_wall_seconds"],
                resource_receipt_path=str(outer_path), resource_receipt_sha256=sha(outer_path),
                anysolver_origin=context["anysolver_origin"], anysolver_origin_sha256=context["anysolver_origin_sha256"])
            def raw_bytes(path):
                return path.read_bytes() if path.is_file() else b""
            if phase == "native":
                assert outer["command"] == prior_bindings["command"]
                raw = dict(stdout=raw_bytes(prior/"stdout.log"), stderr=raw_bytes(prior/"stderr.log"),
                    native_result=raw_bytes(prior/"native-result.json"))
            else:
                raw = dict(stdout=raw_bytes(prior/"ccx-stdout.log"), stderr=raw_bytes(prior/"ccx-stderr.log"),
                    frd=raw_bytes(prepared/"e03.frd"), sta=raw_bytes(prepared/"e03.sta"))
                inner_path = prior/"ccx-process.json"
                inner = json.loads(inner_path.read_text()) if inner_path.is_file() else {}
                receipt.update(executable_path=str(screen.CCX_PATH), executable_sha256=inner.get("executable_sha256"),
                    exit_code=inner.get("exit_code") if outer["status"] == "completed" else outer["exit_code"],
                    process_wall_seconds=inner.get("process_wall_seconds", outer["process_wall_seconds"]))
                versions = screen.re.findall(rb"\b(?:CalculiX\s+)?Version\s+([0-9]+\.[0-9]+)(?![.0-9])", raw["stdout"], screen.re.I)
                receipt["version"] = versions[0].decode("ascii") if versions else None
            for name, data in raw.items():
                receipt[name+"_sha256"] = hashlib.sha256(data).hexdigest()
            # Raw files already exist in prior. Validate actual supervision before
            # allowing finish_screen to write any provisional-success outcome.
            assert outer["status"] == "completed" and outer["exit_code"] == 0
            validate_runtime(json.loads((prior/"runtime-before.json").read_text()))
            validate_runtime(json.loads((prior/"runtime-after.json").read_text()))
            prior_loaded = json.loads((prior/"loaded-modules.json").read_text())
            assert prior_loaded["anysolver"]["path"] == context["anysolver_origin"]
            assert prior_loaded["anysolver"]["sha256"] == context["anysolver_origin_sha256"]
            for name, row in prior_loaded.items():
                loaded_path = Path(row["path"]).resolve()
                assert sha(loaded_path) == row["sha256"], "Physical loaded payload changed"
                if name.startswith("anysolver"):
                    assert loaded_path.is_relative_to(provider.resolve())
                    assert row["sha256"] == manifest["source_modules"][loaded_path.relative_to(provider.resolve()).as_posix()]
                elif name.startswith(("scripts.r8_e03", "scripts.r8_e02")):
                    assert loaded_path.is_relative_to(REPO.resolve())
                    assert row["sha256"] == manifest["inputs"][loaded_path.relative_to(REPO.resolve()).as_posix()]
            assert not (prior/"affinity-failure.json").exists() and not (prior/"resource-failure.json").exists()
            assert not (prior/"monitor-failure.json").exists()
            summary = json.loads((prior/"resource-summary.json").read_text())
            assert summary["samples"] > 0 and summary["peak_tree_rss"] <= 2147483648
            if phase == "external":
                launch = json.loads((prior/"ccx-launch.json").read_text())
                observations = json.loads((prior/"ccx-observations.json").read_text())
                assert launch["affinity"] == [0] and launch["environment"] == manifest["thread_environment"]
                assert launch["command"] == prior_bindings["command"] and Path(launch["cwd"]).resolve() == prepared.resolve()
                assert observations and all(row["affinity"] == [0] for row in observations)
                # OS-thread count is diagnostic, not numerical-thread configuration.
                declarations = screen.re.findall(rb"Using\s+up\s+to\s+(\d+)\s+cpu\(s\)", raw["stdout"], screen.re.I)
                assert declarations and all(int(value) == 1 for value in declarations), "CCX numerical CPU declarations missing/conflicting"
                assert inner["command"] == prior_bindings["command"] and Path(inner["cwd"]).resolve() == prepared.resolve()
                assert inner["exit_code"] == 0 and inner["executable_sha256"] == screen.CCX_SHA256
            result = screen.finish_screen(prepared, receipt=receipt, raw=raw)
            write("finalization.json", dict(status="PROVISIONAL_COARSE_PHASE_COMPLETED", phase=phase,
                prior_attempt=phase_attempt, physical_receipt_sha256=sha(outer_path), production_qualified=False))
    finally:
        loaded = {name:dict(path=module.__file__, sha256=sha(module.__file__)) for name, module in sys.modules.items()
            if getattr(module, "__file__", None) and Path(module.__file__).is_file()
            and name.startswith(("anysolver", "anymaterial", "numpy", "scipy", "numba", "llvmlite", "scripts.r8_e03", "scripts.r8_e02", "test_stiffened_shell"))}
        write("loaded-modules.json", loaded)
        for name, row in loaded.items():
            path = Path(row["path"]).resolve()
            if name.startswith("anysolver"):
                assert path.is_relative_to(provider.resolve())
                assert row["sha256"] == manifest["source_modules"][path.relative_to(provider.resolve()).as_posix()]
            elif name.startswith(("scripts.r8_e03", "scripts.r8_e02")):
                assert path.is_relative_to(REPO.resolve())
                assert row["sha256"] == manifest["inputs"][path.relative_to(REPO.resolve()).as_posix()]
            elif name.startswith("test_stiffened_shell"):
                assert path.is_relative_to(inputs.resolve())
                assert row["sha256"] == manifest["inputs"][path.relative_to(inputs.resolve()).as_posix()]
        after = runtime()
        write("runtime-after.json", after)
        validate_runtime(after)
        assert all(sha(REPO/name) == digest == sha(inputs/name) for name, digest in manifest["inputs"].items())
    raise SystemExit(code)
except Exception as error:
    write("entry-failure.json", dict(type=type(error).__name__, reason=str(error)))
    if mode.startswith("finalize-"):
        write("finalization-failure.json", dict(type=type(error).__name__, reason=str(error),
            prior_attempt=phase_attempt, raw_preserved_at=str(RAW/phase_attempt), production_qualified=False))
    raise
finally:
    stop.set()
    thread.join(timeout=1)
    write("rss-samples.json", samples)
    write("ccx-observations.json", child_samples)
    write("resource-summary.json", dict(peak_tree_rss=max((row["rss"] for row in samples), default=0),
        samples=len(samples), affinity_setup_events=affinity_events))
