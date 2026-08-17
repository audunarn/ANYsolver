# E3 route-selection independent review

## Verdict

`ACCEPT_NO_P0_OR_P1` - the corrected E3 route-selection packet is internally
consistent, reproducible, fail-closed, and within its preregistered
non-production extent. No P0 or P1 finding remains.

This verdict accepts the evidence process and the reported route outcome. It
does not accept HW29 as a qualified element, promote MITC9i into the Q4 route,
register `candidate_e3_a`, or authorize production implementation. The
controlling component and route terminals remain:

```text
HW29:   BLOCKED_E3_P_HW29_PUBLIC_SOURCE
MITC9i: GO_REFERENCE_E3_Q9_MITC9I_PARTIAL_PACKET
Route:  UNCLASSIFIED_E3_Q4_FORMULATION_ROUTE
Next:   AUTHORIZE_E3_A_VARIATIONAL_CLOSURE_STUDY
Release:NO_GO_PRODUCTION_RESTRICTION_UNCHANGED
```

An initial review pass identified two P1 evidence defects: the new tests did
not directly assert every frozen tier identity, and the E3 environment record
did not bind the inherited runtime manifest and exact pinned `PYTHONPATH`.
Both were corrected before this single re-review. The current tests assert the
exact commits, trees, node-list hashes, and E2 files; the environment record
now binds the inherited 1,330-byte manifest at SHA-256
`F2DB5FF809FE0ED35ABE398FBFCECD133F2E8C36E96D1AB5C79354784F7216DE`
and records the five absolute `PYTHONPATH` roots in order.

## Authority and immutable history

The reviewed branch is `codex/s4-e3-hw29-mitc9i-route-selection`. Its
unchanged authority is commit
`2ac678a7f94c250fe433f66378a83508d86ee499`, tree
`f7382e2b88343ac29c9a9e3c424f618a3652cc01`.

The packet correctly preserves the historical test tiers as separate exact
executions, not one live 118-test suite:

* E0: commit `87b639499187736c59d87bc4aa8e6bd7f819d28b`, tree
  `c01fd5cab7b63325e6cb5b70000f4586d4788563`, 94 nodes, node-list SHA-256
  `29EF584E9B51E8420934A519B3C1E71BDD3082EFDC89DBADA4FCE0FFE8997B9F`.
* E1: commit `281ed90e148c125edbec27e7336a8f9f0df08edc`, tree
  `1ee60da4717055f5cc1b37ff9369877bb1867861`, 16 nodes, node-list SHA-256
  `9835FB4580C886B52BFF5961A30CD78E921B5CEED92A918312149032748A7F63`.
  The accepted report's historical statement of 15 tests remains unchanged.
* E2-A: the E3 authority commit/tree above, eight nodes in the three frozen
  E2-A test files. Its canonical output remains SHA-256
  `37C803C565602E1AF983AA8374C3DA090EFD1CC73F2B672F2C815CC6A56B623D`.

I independently ran the three tiers in their exact detached worktrees using
the pinned environment and obtained 94, 16, and eight passes respectively.
Every historical A/B/C/rank-four/E0/E1/E2 terminal and output remains
unchanged.

The attached 35,837-byte proposal is correctly bound at SHA-256
`7D86FE7A6D205BFEDDA4C884A2AFAD5C80EF0F3DE6BA350C48BBB2150BFC5108`
as superseded design input, not executable authority.

## Source-governance and copyright audit

The `P` / `D` / `B` statement boundary is enforced consistently. Printed
primary-source equations may close a source row; unique algebraic consequences
may be independently derived and certified; background sources cannot supply
missing coefficients, spaces, maps, thresholds, or outcomes.

The three supplied PDFs and public sources are recorded only by metadata,
hash, page mapping, and statement classification:

* The 2011 HW29 chapter is 310,978 bytes, 22 pages, SHA-256
  `E6AFAADE32B33D710D3C038635FE2AD2729E32FB952C5EC6706E68A93A3B1860`.
* The distinct degenerated-Q4 torsional-penalty paper is background only:
  1,235,559 bytes, 11 pages, SHA-256
  `B67AF5A43CB36FEC9E0D8CDAD745B391F9F5FC1861C842A249E2B982BDACD5E8`.
* The supplied MITC9i copy is byte-identical to the CC-BY-4.0 open primary:
  1,302,612 bytes, 25 pages, SHA-256
  `5C66A76D39682F71C13208E71AFFA585FD3CD1E284185360B825572DC8BA048B`.
* The six-page open HW29 summary is 1,196,627 bytes, SHA-256
  `4246170D4F4CE60C7C4DAB74CE4D778BC92F5C5FA3C91C975A6521FF34991329`.

No external PDF, page, figure, screenshot, table, or verbatim passage is
committed. The copyrighted supplied files are technical evidence only. The
open MITC9i paper is used for bounded theory extraction; the unavailable 2012
HW29 journal full text is not treated as if its missing equations were known.

## HW29 component audit

The source matrix has exactly 14 mandatory rows: nine
`CLOSED_PUBLIC_SOURCE` rows and five indispensable missing rows. The missing
rows are the shell-specific EADG2 transformation, the four-plus-four mixed
shear maps, the complete discrete functional and internal-field order, the
actual local-condensation/invertibility equations, and linear loads plus
physical-resultant recovery. These are identity-defining data, so the correct
terminal is `BLOCKED_E3_P_HW29_PUBLIC_SOURCE`, not a scientific NO-GO. Rank,
patch, material, recovery, and actual HW29 condensation outcomes are correctly
marked `NOT_RUN`.

The exact source-independent certificates close only what the printed material
supports:

* The flat drilling constraint expands in `1, xi, eta, xi*eta`; the last
  coefficient is the rotation-only alternating drill term. Deleting it leaves
  the alternating mode outside the retained multiplier moments.
* Pure common drill and translation-only rigid spin have opposite constant
  coefficients, while their combined physical rigid rotation is exactly null.
* The printed hourglass vector sums to zero and has unit action on the
  alternating mode. Its outer product is rank one, does not ground common
  drill, and contributes exactly `10^-3 G V Theta_2^2` for both the square and
  rational-trapezoid exact cases.
* The registered square vector is `(1,-1,1,-1)/4`; the rational-trapezoid
  vector is `(3/14,-3/14,2/7,-2/7)`. Both exact cases satisfy reversal and
  rigid-invariance checks.
* The 29-field arithmetic is exactly `7+9+2+3+4+4`. The generic Schur example
  is explicitly scoped as derived algebra only, not an asserted HW29 block.
* The E2-A interior bubble is nonzero inside and zero on the boundary, hence
  lies outside the frozen Q1 HW29 displacement space. No Allman enrichment or
  E2-A coefficient enters the HW29 identity.

This is sufficient to distinguish HW29 and certify the printed drill/hourglass
mechanics, but not to reconstruct the complete source-exact element.

## MITC9i reference audit

The MITC9i packet is correctly independent and non-gating. Its route field is
`NONE`, and no MITC9i status can select, block, or modify HW29.

The exact and outward-certified reference cases reproduce the bounded source
claims: the COVc common-centre transformation is identified as an
approximation rather than exact covariance; the corrected corner, midside,
and centre functions satisfy partition of unity, Kronecker interpolation, all
four edge restrictions, and Q2 reproduction; the straight shifted-node case
has exact parameter `-1/2`; and the curved case has a certified nonsingular
root bracket `[-53/200,-33/125]` containing the printed value.

The drilling expansion has nine monomials and the highest `xi^2 eta^2`
rotation-only row
`[1/4,1/4,1/4,1/4,-1/2,-1/2,-1/2,-1/2,1]`, with zero rigid row sum and
square integral factor `4/25`. The retained, deleted, and `10^-3`-scaled
alternatives are attributed without selecting one for HW29. Missing explicit
first/second variations, consistent tangent, mass, geometric stiffness, and
load-potential details are listed rather than invented. Therefore
`GO_REFERENCE_E3_Q9_MITC9I_PARTIAL_PACKET` is the supported reference status.

## Determinism and test audit

Both standard-library oracles reject duplicate JSON keys and nonfinite values,
verify caller-bound contract hashes, and were run twice in fresh processes.
Each pair produced byte-identical canonical UTF-8/LF output:

* HW29: 2,441 bytes, SHA-256
  `3D9E9C858CAD14CB3BDEBFC8866E971658F02E71B16573A320BAF0B08DFE9806`.
* MITC9i: 2,475 bytes, SHA-256
  `00A6603A7B163CBC4A25B7FDF74647DDC1BDA300D478598F1403E4582AF5B575`.

I ran the four focused E3 files and obtained `14 passed in 3.91s`:

```text
python -m pytest -q --basetemp .pytest_tmp_e3_final \
  tests/test_e3_baseline.py \
  tests/test_e3_hw29_identity.py \
  tests/test_e3_mitc9i_reference.py \
  tests/test_e3_route_selection.py
```

`git diff --check` passed. The route contract and output are caller-bound at
SHA-256 `B39EE05F48EB4D5CF4A1A09C0FF20891886BB388631756FD08328CEE4FB99BF9`
and `A2D3283C1F01A26EF01986A4C5396B6C07797C250B7D2BD3BDA21AD1E14C273E`.

## Frozen reviewed inputs

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `.gitattributes` | 1,769 | `FCE05E44B73DBC45CAF9D964E2FEE7E07492D2EF4320B122FE2152470E4739B2` |
| Governing plan | 6,092 | `F2572FED30BAA18EE66029207438E1C64F2D5B208B834B261EC585B25E70DFCC` |
| Baseline | 1,398 | `D080BCC53EE4C19BFB49551B46826B66328BC9E8581EB254BBF0D5504FF54A67` |
| Environment | 1,382 | `F8F3461E06AFDC7B6627501B1E85C91095A88BC07EC76F8B0054D8C352770F43` |
| Test inventory | 1,264 | `6FCBD5D28BCA20A3AF89469E426CF0F003CCA6C6E52B000D6A4A3B79FA95E9A0` |
| Material fixtures | 908 | `A9DAA9960E5B0FDC65653AC7E9BA88CBC39EE9B0A9FD786AB854D5965422266F` |
| Search log | 1,559 | `6A327A8120995CC52A943890E7C4EC6B7171C1F0F5F3C14300A82B5483C57495` |
| Source registry | 2,863 | `3F28EEF4E2E83EE82BE9487233694547F946154B39114A785D61D341296322C7` |
| HW29 report | 5,586 | `50A3A953E31758B301A28906AF677236C9959DB04DA0F99F2CF8C02A8B07550C` |
| HW29 source coverage | 5,509 | `5469057E9038ADDC904D4115B7C332B6E7D7488396A9C7C7DEB933D09D4D5AFE` |
| HW29 exact cases | 1,874 | `1A6A3960DEC3E9E806B24E4CEF9531EC45DD8858A22F684013D8A7F81097F2DE` |
| HW29 oracle | 21,342 | `CFDB4B762E641C3958D7B67373AABD745A591AFF5EE79FA27E0BD9EC8B53369F` |
| HW29 contract | 2,331 | `E07C60EDE72DDD6D19D686F79978C3F0D1826DA91B1D2552534063BD28C394A0` |
| HW29 output | 2,441 | `3D9E9C858CAD14CB3BDEBFC8866E971658F02E71B16573A320BAF0B08DFE9806` |
| MITC9i report | 6,539 | `F5115FB1EF1E41C6FA101E5C89918E15A1B8D493C5E377D21507BA1BBAF20CAA` |
| MITC9i source map | 3,655 | `7E3679EE0BD25245C26EF4D4C259CA3F8B838FD9ED98F6D053A1B3E4B35C039E` |
| MITC9i exact cases | 2,153 | `B25F0F7787DC8B56B08E4FAA0B1DE6E7AE6D34B80E9BE68E2B202BD4926D33E5` |
| MITC9i oracle | 24,718 | `1DB0E4C9A882E1250C596DA63118EBD835F57AC054104F8196BCE9F90F63ED6B` |
| MITC9i contract | 2,116 | `86824E91A460AEAC9F67B213048E471AF968C7AA9FE2C43E6B61B148A5C8FBED` |
| MITC9i output | 2,475 | `00A6603A7B163CBC4A25B7FDF74647DDC1BDA300D478598F1403E4582AF5B575` |
| Route report | 4,575 | `D76876A388BAEDBB2C1DF23C91D1E5E7A99BD365439902904B017D9A7A5B93B9` |
| Conditional E3-A study plan | 4,794 | `5903DFEC12D7F4331493CDFEFFB04ACBB22F94EA681993366D80957E403B09FA` |
| Route contract | 3,610 | `B39EE05F48EB4D5CF4A1A09C0FF20891886BB388631756FD08328CEE4FB99BF9` |
| Route output | 708 | `A2D3283C1F01A26EF01986A4C5396B6C07797C250B7D2BD3BDA21AD1E14C273E` |
| Baseline test | 5,792 | `0B8739519F1176C1E2D1AD8AA30835D568C79E580F15284D64108F90D14D0B85` |
| HW29 test | 9,882 | `A9A6BCA9FC07C618FBC06E2BAF5C5313ECFDAA5B3CF8962E7F556B84614A1D8E` |
| MITC9i test | 9,312 | `DA2ACE6005ADA2DE41D94C6BE0F328DD9ECD34A53BEB627FCD5516FABE6D2636` |
| Route-selection test | 7,989 | `25502F3306EFD3750C2D91C277DC28444C67AA64D573B60A6F80234629DEFAB5` |

## Scope and route boundary

The only modified tracked path relative to the authority commit is
`.gitattributes`, which adds LF rules for the preregistered E3 names. All other
E3 paths are new plans, reports, source maps, cases, independent oracles,
contracts, canonical outputs, status evidence, and tests listed in the route
contract. The index is empty. `src/`, `.github/`, and `pyproject.toml` have no
diff. The six inventoried historical untracked roots remain preserved and
unaltered.

There is no production/package/workflow, public API, selector, serialization,
export, dispatch, default, push, merge, publication, or cleanup change. The
conditional E3-A document is explicitly a variational-closure study only. It
does not register or implement `candidate_e3_a`; any complete functional and
discrete spaces must be frozen under a separately named plan.

Legacy `ShellElement` therefore remains the production default. The final E3
route status may close out the evidence run, but cannot change
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
