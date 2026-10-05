# Experimental generalized material BL5 — 2 October 2026

Explicit `BL5_GENERALIZED_MATERIAL_V1` enables generalized beam yielding with
elastic objective Q4 BL5. The default remains elastic. S3, shell J2 and physical
fibre line material combinations remain excluded. This is implementation evidence,
not physical BL5 qualification or aggregate gate acceptance.

Distinct binary/chart schemas retain both accepted and predecessor histories.
Restore re-evaluates from the predecessor before atomic publication. Pre-yield
snapshots, rejection, cancellation, chart rebase and signed reversal are covered.
Independent OpenAI source review identified pre-yield, predecessor and rebase
issues; these were corrected. It is not cross-family scientific acceptance.

Installed wheel SHA256:
`76f18db25d1ad3df88308139bfe8e1593f11ad3f07dfbe9f880bc64b757a5153`.
All 398 source/wheel/site modules match. Eight installed checks passed in 197.76s
(supervised 199.672s; peak tree 183197696 bytes), with one numerical thread and
JIT disabled. They cover two line bases, smooth yielded tangent, distributed
loads, legacy elastic BL5 and existing point-material restart. Version unchanged.

Source final runs: two lifecycle cases passed (122.615s supervised); distributed
and pre-yield cases passed (24.850s). Earlier failed source runs v1–v4 are retained.
The first low-hardening 1e6 fixture still exhausts backtracking/cutbacks. A temporary
work-merit modification failed and was removed. The 1e8 hardening control, matching
an existing generalized-history fixture, passes actual yielding and reversal.
This does not resolve or exclude the low-hardening failure. No globalisation,
physical tolerance, pressure-assessment or constitutive law was changed.

Four bounded diagnostics are retained. Random-direction derivatives in the first
case were accurate, but Newton-direction checks near first yield were branch
sensitive; they are not blanket tangent acceptance. The passing lifecycle checks
use an explicit smooth yielded direction and the saved accepted predecessor.
No further automatic diagnostic sweep is authorized by this result.

`evidence-v1.zip` SHA256:
`622526e72106c0cdf3ab496ba85b389868e9e12166e7e0b4da907f14e367d632`.
Includes failed and successful runs, diagnostics, exact installed fixtures, artifact
identity, runtime imports and safe execution metadata. Full environment mappings
are intentionally excluded. Consumer verification is recorded separately.
