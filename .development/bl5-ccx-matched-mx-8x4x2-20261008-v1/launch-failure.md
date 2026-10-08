# First pinned CalculiX launch attempt

The prepared deck and metadata passed the 40-row reduction and load checks.
The first `run_ccx.py` invocation did **not** create a CalculiX process.
`subprocess.Popen` raised Windows `OSError [WinError 623]` during
`CreateProcess`: illegal system DLL relocation. The Python command exited 1;
the command tool observed `0.5333671 s` wall time. No process-wall duration,
solver output, accepted increment or numerical result exists for this attempt.
The `ccx.stdout.txt` and `ccx.stderr.txt` files were created empty before the
launch error; `weak.frd` and `ccx.receipt.json` were absent afterward. The
attempted launcher source SHA-256 is
`0289bb4c87376505033938bb6820e19c3be4e4e9ac8cd5292fefc0a0b7d00e58`.
The pinned binary SHA-256 was independently checked as
`27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f`.
This is a launch failure, not a mechanics result. Preserve this directory;
any retry uses a new versioned directory and robust launch receipt.
