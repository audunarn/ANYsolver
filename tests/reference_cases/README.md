# FE solver reference cases

This directory is intentionally mostly empty in git.  It is used for local
CalculiX/PrePoMax reference cases during solver verification.

The discovery code looks for matching file pairs:

```text
<case-name>.inp
<case-name>.frd
```

Optional metadata may be added as:

```text
<case-name>.json
```

The shell convergence candidate from `calculix/CalculiX-Examples` can be fetched
with:

```powershell
python scripts/fetch_calculix_shell_reference.py
```

That script downloads the lightweight upstream sources only.  It does not run
CGX/CCX and does not create numerical results.  To generate actual comparison
cases, run the upstream CGX/CCX workflow locally and keep or copy the resulting
`.inp` / `.frd` files under this directory.

Then run:

```powershell
python -m pytest tests/test_fe_solver_reference_cases.py -q
```
