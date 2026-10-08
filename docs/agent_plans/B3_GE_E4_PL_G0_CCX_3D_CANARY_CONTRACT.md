# Stock CalculiX B31/S4 footprint compatibility canary

22 September 2026. This is a single-case, exploratory execution prerequisite
for the independent E01/E02 programme, not either mandatory comparison. It
uses the committed inert deck generator and the separately tested parser.
Execution needs an exact source and executable registration before one
exclusive run. Preserve its output even if preprocessing, factorization,
parsing, or the resource limit fails; never reinterpret an exit code alone
as physical agreement.

The fixed input is the `+0.1 m` eccentric B31/S4 rigid-footprint deck with
`+1000 N` transverse `y` tip force. It has 32 S4 and two B31 elements,
four noncollinear shell footprint nodes, 12 translational point equations,
and a fixed beam root plus both shell outer columns. This is a *strong,
finite footprint* model. It differs from the exact weak nonmatching line,
native B3-GE section, native physical B2 section, and E4-PL shell.

The canary's terminal question is narrow: does the pinned stock CalculiX
executable accept the mixed input, finish one full linear increment, and
print a finite nonzero 48-node translational response? The parser rejects
missing, duplicate, nonfinite and partial results. It does not infer
reactions from nodal `RF` under MPCs; those values require an independently
reviewed work and balance recovery. Printed DAT precision is not adequate
for the final connection-gap tolerance.

The prospective execution record must bind source HEAD and hashes, exact
LF deck bytes, executable SHA-256, one thread, command `ccx.exe -i canary`,
fresh case directory, a 120 s process timeout, output inventory, stdout,
stderr, `.sta`, `.dat`, `.frd`, and a parsed result. A timeout or a solver
failure is retained as a failed canary. No retries on the same registration.
After a successful canary, E01/E02 still need matched section/offset,
independent reaction and moment balance, energies, force-couple torque,
drilling/thickness/refinement sensitivity and at least three refinement
levels with frozen numerical thresholds. A canary failure triggers review
of the external idealization or solver support before any comparison.
