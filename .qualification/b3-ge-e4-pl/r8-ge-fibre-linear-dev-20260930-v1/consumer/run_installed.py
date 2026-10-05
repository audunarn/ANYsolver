from pathlib import Path
import hashlib, json, os, sys, zipfile
import importlib.metadata as metadata
import anysolver, anyfem, pytest, threadpoolctl
from anysolver import stiffened_shell

root = Path(__file__).resolve().parent
site = Path('C:\\Users\\AudunArnesenNyhus\\AppData\\Local\\Temp\\r8-ge-fibre-linear-installed-v1\\site').resolve()
solver_root = Path("C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling")
consumer_root = Path("C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer")
solver_wheel = Path('C:\\Users\\AudunArnesenNyhus\\AppData\\Local\\Temp\\r8-ge-fibre-linear-installed-v1\\wheels\\anysolver-0.4.7-py3-none-any.whl')
consumer_wheel = Path('C:\\Users\\AudunArnesenNyhus\\AppData\\Local\\Temp\\r8-b2-output-guard-installed-v1\\wheels\\anyfem-0.4.1-py3-none-any.whl')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(root / "frozen-inputs.json") == "22babada390f15473c2537077a344515715a5e17cd93ee5a25c548b08c5ba6a5"
frozen_inputs = json.loads((root / "frozen-inputs.json").read_text())
assert all(sha(root / path) == digest for path, digest in frozen_inputs.items())

assert sha(solver_wheel) == "56deb65e27dd29abe94aec44e514276b10e1fef78ba91078dfe3df8d68358add"
artifacts = {}
for name, source_root, wheel in (
    ("anysolver", solver_root, solver_wheel),
    ("anyfem", consumer_root, consumer_wheel),
):
    source = source_root / "src" / name
    sources = {f"{name}/" + p.relative_to(source).as_posix(): p for p in source.rglob("*.py")}
    with zipfile.ZipFile(wheel) as archive:
        modules = {n for n in archive.namelist() if n.startswith(name + "/") and n.endswith(".py")}
        assert modules == set(sources), (name, modules ^ set(sources))
        for path, source_file in sources.items():
            assert archive.read(path) == source_file.read_bytes(), path
            assert (site / path).read_bytes() == source_file.read_bytes(), path
    artifacts[name] = {"wheel": str(wheel), "sha256": sha(wheel),
                       "matching_python_modules": len(sources),
                       "module_sha256": {p: sha(f) for p, f in sources.items()}}
for module in (anysolver, anyfem):
    assert Path(module.__file__).resolve().is_relative_to(site), module.__file__
pools = threadpoolctl.threadpool_info()
assert pools and all(p["num_threads"] == 1 for p in pools), pools
assert os.environ["NUMBA_DISABLE_JIT"] == "1"
environment = {"python": sys.version, "threadpools": pools,
               "numba_disable_jit": os.environ["NUMBA_DISABLE_JIT"],
               "dependencies": {n: metadata.version(n) for n in
                                ("numpy", "scipy", "numba", "pytest", "ANYmaterial", "ANYmesher", "ANYfileio")}}
selected = ['test_experimental_stiffened_shell_consumer.py::test_physical_fibre_reference_linear_inputs_reopen_and_restart']
(root / "identity.json").write_text(json.dumps(
    {"artifacts": artifacts, "environment": environment,
     "test_sha256": {p.name: sha(p) for p in (root / "tests").glob("*.py")},
     "selected": selected, "fixture_sha256": {p.relative_to(root).as_posix(): sha(p) for p in (root/"scripts").glob("*.py")}}, indent=2))
print(json.dumps(environment), flush=True)
code = pytest.main(["--junitxml", str(root/"inventory.xml"), "-q", "-c", str(root / "pytest.ini"),
                    "--basetemp", str(root / "pytest-tmp")] +
                   [str(root / "tests" / p) for p in selected])
loaded = {name: str(Path(module.__file__).resolve())
          for name, module in list(sys.modules.items())
          if name.split(".")[0] in ("anysolver", "anyfem")
          and getattr(module, "__file__", None)}
assert all(Path(p).is_relative_to(site) for p in loaded.values()), loaded
(root / "imports.json").write_text(json.dumps(loaded, indent=2))
print(json.dumps({"loaded_modules": len(loaded)}), flush=True)
sys.exit(code)
