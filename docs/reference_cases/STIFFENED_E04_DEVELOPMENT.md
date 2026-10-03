# Experimental E04 material roof

This is a runnable development application of the installed GE curved-Q4 point
profile, with synthetic strengths. It is not a qualified roof-capacity example.
Use the paired ANYsolver/ANYfem artifacts identified in the
[results](../agent_plans/development/r8-e04-material-roof-20261003/results.md),
and run from this checkout so the reference fixture and scripts are available.
The scripts use public package interfaces; the consumer script requires ANYfem.

Use a serial, supervised process with the recorded 600 s / 1 GiB ceiling.
The script asserts one numerical thread and disabled JIT. In PowerShell, prepare
the child environment:

```powershell
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:NUMBA_NUM_THREADS = '1'
$env:NUMBA_DISABLE_JIT = '1'
```

Choose fresh output directories. The executed application arguments are:

```powershell
python scripts/r8_e04_native_roof.py `
    --output material-roof --size 4 --density 1 `
    --seed-force 100 --radius .003 --steps 20 --restart-after 5 `
    --shell-proportional-limit-pa 3102750 `
    --beam-resultant-limits 500,300,300,1,2,.5 --beam-hardening-n 25000
```

This writes the accepted snapshots and full sampled path. `accepted.bin` is the
final accepted checkpoint on completion; failed runs retain their accepted prefix.
The reported status must be inspected before interpreting an output as complete.
Prefix-five restoration repeats fifteen steps and checks their exact snapshots
and detailed material recovery.

The separate native consumer route uses that same definition and snapshot:

```powershell
python scripts/r8_e04_material_consumer.py `
    --output material-roof-consumer --checkpoint material-roof/accepted.bin `
    --size 4 --density 1 --seed-force 100 --radius .003 --steps 2 `
    --shell-proportional-limit-pa 3102750 `
    --beam-resultant-limits 500,300,300,1,2,.5 --beam-hardening-n 25000
```

It writes standalone and native Project definitions, verifies their identity,
restores both material histories and compares two continued steps with a fresh
solver owner. Unsupported or wrong-model snapshots fail explicitly.

For the combined stress-free imperfection/material application, add
`--imperfection-m .0001` to **both** commands and choose new output directories.
This creates a virgin reference with a 0.1 mm downward crown change, transports
the physical point offsets/frames once and then applies the same declared laws
and loading. Native Project persistence stores the resulting reference definition;
the separate run record retains its construction amplitude, operation policy and
source/target identities. It does not transport loaded material history into the
new reference. The supplied checkpoint must belong to that changed definition.

The 16-shell/four-beam case uses eccentric, full-pose nodal point bonds. Its
generalized beam ellipsoid is not physical fibre plasticity. Density is declared
static bookkeeping; curved spectra are excluded. The sampled peak and descending
path are not independently converged limit-load predictions. The published bare
roof geometry source does not supply an oracle for this stiffened material model.
