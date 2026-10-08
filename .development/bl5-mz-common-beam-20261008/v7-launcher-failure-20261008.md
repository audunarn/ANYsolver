# V7 launcher failure before numerical execution

The first launcher invocation used the workstation default `python` at
`C:/Users/AudunArnesenNyhus/AppData/Local/Programs/Python/Python311/python.exe`.
It exited 1 before the guarded runner's `main()` and before any numerical child
was started: `ModuleNotFoundError: No module named 'psutil'` at the runner import.
The command was `python .development/bl5-mz-common-beam-20261008/run-v7-nodal-port.py`;
the command tool reported 0.4638541 s wall. No V7 output directory or receipt
was created. This is a launcher/environment failure, not a V7 numerical attempt.
The already-used V6 receipt identifies `C:/Python/Python314/python.exe`; an
explicit import check of `psutil`, NumPy, Numba, threadpoolctl and SciPy there
passed. Retain this failure when executing the one approved numerical attempt.
