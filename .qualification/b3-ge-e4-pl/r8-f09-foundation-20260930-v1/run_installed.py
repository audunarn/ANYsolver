from pathlib import Path
import hashlib, json, os, sys, zipfile
import importlib.metadata as metadata
import anysolver, anyfem, pytest, threadpoolctl
from anysolver import stiffened_shell

root = Path(__file__).resolve().parent
site = Path('C:\\Users\\AudunArnesenNyhus\\AppData\\Local\\Temp\\r8-b2-output-guard-installed-v1\\site').resolve()
solver_root = Path("C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling")
consumer_root = Path("C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer")
solver_wheel = Path('C:\\Users\\AudunArnesenNyhus\\AppData\\Local\\Temp\\r8-b2-output-guard-installed-v1\\wheels\\anysolver-0.4.7-py3-none-any.whl')
consumer_wheel = Path('C:\\Users\\AudunArnesenNyhus\\AppData\\Local\\Temp\\r8-b2-output-guard-installed-v1\\wheels\\anyfem-0.4.1-py3-none-any.whl')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(solver_wheel) == "19e3235a35b69e14f322867bf224b164789163c6cc7e2e808c0bba584c3c441e"
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
selected = ['test_generalized_beam_sections.py::test_beam2_diagonal_generalized_section_matches_legacy_timoshenko', 'test_generalized_beam_sections.py::test_generalized_section_mass_matrix_overrides_material_geometry', 'test_generalized_beam_sections.py::test_generalized_von_karman_tangent_matches_central_difference', 'test_generalized_beam_sections.py::test_generalized_beam2_corotational_response_routes_section_coupling', 'test_generalized_beam_sections.py::test_generalized_geometric_stiffness_ignores_legacy_section_geometry', 'test_generalized_beam_sections.py::test_generalized_wagner_term_requires_explicit_geometric_metadata', 'test_constraint_audit.py::test_valid_eccentric_beam_shell_coupling_is_feasible', 'test_analysis_session.py::test_repeated_static_session_matches_legacy_and_reuses_plans', 'test_analysis_session.py::test_prescribed_value_refresh_reuses_structure_and_factorization', 'test_analysis_session.py::test_mpc_structure_change_invalidates_constraint_and_factorization_plans']
(root / "identity.json").write_text(json.dumps(
    {"artifacts": artifacts, "environment": environment,
     "test_sha256": {p.name: sha(p) for p in (root / "tests").glob("*.py")},
     "selected": selected}, indent=2))
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
