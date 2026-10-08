from pathlib import Path
import hashlib, json, os, sys, zipfile
import importlib.metadata as metadata
import anysolver, anyfem, pytest, threadpoolctl

root = Path(__file__).resolve().parent
site = (root / "site").resolve()
solver_root = Path("C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling")
consumer_root = Path("C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer")
solver_wheel = root.parent / "r8-q4-pullback-installed-v1/anysolver-wheels/anysolver-0.4.7-py3-none-any.whl"
consumer_wheel = root / "wheels/anyfem-0.4.1-py3-none-any.whl"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(solver_wheel) == "314ea0dffd9c5fa7f70b80538373e42ffd10b5083f231b69a8bd4784773b1a2d"
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
selected = [
    "test_experimental_b2_stiffened_shell_consumer.py",
    "test_experimental_stiffened_shell_consumer.py",
    "test_stiffened_shell_b2_reference_modes.py",
]
(root / "identity.json").write_text(json.dumps(
    {"artifacts": artifacts, "environment": environment,
     "test_sha256": {p.name: sha(p) for p in (root / "tests").glob("*.py")},
     "selected": selected}, indent=2))
print(json.dumps(environment), flush=True)
code = pytest.main(["-q", "-c", str(root / "pytest.ini"),
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
