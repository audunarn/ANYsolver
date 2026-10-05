# Q6 diagnostic evidence byte preservation

**24 September 2026. Evidence packaging correction only.** The retained Q6
source-process diagnostics include JSON and log files written with Windows
CRLF. Ordinary Git text normalization stored LF versions of some files,
which would break SHA-256 links after checkout. A `.gitattributes` rule now
marks files inside all `B3_GE_E4_PL_G0_F03_Q6_*` evidence directories as
exact-byte data. The large inverse archives remain locally retained and
Git-ignored with their committed sizes and SHA-256 values.

All **84 tracked Q6 evidence files** have index blob IDs matching their raw
working-file bytes. The **26 previously tracked files** restaged by this
change differ from their prior committed versions only by CRLF/LF encoding;
parsed content and numerical values are unchanged. Recomputed certificate,
physical and spatial file hashes match all three completed X2 integrated
measurements (V2, bound-state and KKT-bound).

This correction does not alter any run, receipt, acceptance threshold or gate
status. The diagnostics remain unregistered; F03/G0B are open and G1 barred.
