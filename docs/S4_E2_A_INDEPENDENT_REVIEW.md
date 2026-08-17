# Candidate E2-A independent review

## Verdict

`ACCEPT` - no P0 or P1 defect remains in the source-identity and kinematic
feasibility packet.

This accepts the evidence and its fail-closed terminal.  It does not accept a
Candidate E2-A element, authorize a linear reference implementation, or change
production.  The controlling scientific terminal is
`BLOCKED_E2_A_SOURCE_OR_FORMULATION_IDENTITY`, reason
`RANK_SUFFICIENT_DISPLACEMENT_ENRICHMENT_NONUNIQUE`.

An earlier review pass found that the first witness was proved only on the
reference square.  The packet was corrected before this verdict.  It now uses
the physical center curl and the orientation-corrected map

```text
C_A = chi sqrt(det(A^T A)) A (A^T A)^-1,
```

which is `chi |det(A)| A^-T` in an oriented two-dimensional frame.  The exact
oracle now covers both the square and a rational skew affine map under every
registered covariance operation.  I independently inspected the corrected
derivation, oracle algebra, emitted output, and tests.

## Authority and immutable baseline

The working branch is `codex/s4-e2-a-source-kinematics`.  Its unchanged
authority commit is `281ed90e148c125edbec27e7336a8f9f0df08edc`, tree
`1ee60da4717055f5cc1b37ff9369877bb1867861`.  Its parent E0 authority is
`87b639499187736c59d87bc4aa8e6bd7f819d28b`, tree
`c01fd5cab7b63325e6cb5b70000f4586d4788563`.

The baseline is correctly represented as two immutable tiers, not one live
110-test successor suite:

* E0: 94 ordered nodes, 9,842 canonical LF bytes, SHA-256
  `29EF584E9B51E8420934A519B3C1E71BDD3082EFDC89DBADA4FCE0FFE8997B9F`.
* E1: 16 ordered nodes, 1,692 canonical LF bytes, SHA-256
  `9835FB4580C886B52BFF5961A30CD78E921B5CEED92A918312149032748A7F63`.

The accepted E1 report remains 5,586 bytes with SHA-256
`72DCCDDA0374946FB41DD3A47967196E025EAB9157959D1472D2EE488A0A30AA`;
its historical statement that 15 focused tests ran was not edited.  The
committed five E1 test files independently collect 16 nodes.  The immutable
E1-A and E1-R outputs remain respectively 2,397 bytes / SHA-256
`8022ECC3FB9D78637851EAF751044ABEE3C7E09D428160302450B726BD710788`
and 5,041 bytes / SHA-256
`ED26CF65363AD97BFA57234EA6CC7C708D8E94B4D477AAC64F5C6BAFB44B749B`.
The qualification test also rechecked every A, B, C, rank-four, E0, and E1
terminal and each frozen production-source identity.

The long-horizon design input was independently checked at 30,935 bytes and
SHA-256
`5BF221C0B75425E292D80EF59CA4B6613445DD0621664F9350043E3B5B9B3C68`.
It is correctly treated as design input, not executable authority.

## Source and formulation audit

The statement-level `P` / `D` / `B` boundary is sound:

* Wagner-Gruttmann 2020 fixes the `n=7`, `k=0` Hu-Washizu spaces, local
  elimination, and positive `2 x 2` rule.  Its local PDF is 3,267,230 bytes,
  SHA-256
  `DB68AD45455999D47D6152E736D7277F28AC1C0D85063790B15FE4089293A712`.
* Wagner-Gruttmann 2004 fixes the MITC4 shear tying and the five-coordinate
  ordinary-node boundary.  Its report is 878,871 bytes, SHA-256
  `8EBDBA969BB3E2A34288EA3B5D52014C68C0E30FD2A9B36B1F92EB3073AEE7A0`.
* The public MITC4/D paper prints the quadratic Allman/Cook endpoint-difference
  connector.  Its PDF is 9,046,388 bytes, SHA-256
  `89C10DE1FB13056EB967111C2DBB28FE2D18179090814141455F4E8901D919EA`.
* The original Allman quadrilateral and 1992 drilling papers are metadata-only
  background in this wave.  They are not used to supply missing equations.
* The Sestra 8.6 and installed current manuals were checked at 3,937,204 bytes /
  SHA-256
  `68E904E8E1B6800BC04FAA60299E17DEB29E3AB79B1823E09A7DD2F1C02FB1F3`
  and 4,353,645 bytes / SHA-256
  `A7F0D3C4135B9ADC025229F3A91C1FB60E755F3CE3F176EA0EF4B6D7555A6334`.
  They remain `B` evidence only; no page, figure, copied passage, equation,
  threshold, or outcome from them is committed.

The fixed core, node and edge orders, frame/director conventions,
strain/resultant orders, mixed spaces, shear tying, quadrature, local
condensation boundary, and load-work requirement are internally consistent.
No complete displacement operator `H` or strain operator `B` is selected.

## Exact certificate audit

The corrected independent standard-library oracle does not import candidate
or production code.  Its exact checks support the identity block:

* `eta = mean(theta_D) - omega_D(center)` gives `+1` for pure common drill,
  `-1` for translation-only physical spin, and zero for their matching rigid
  combination.
* For the skew map `A=[[3,5],[4,12]]`, the physical-normal map is exactly
  `C=[[12,-4],[-5,3]]` and `A^T C=16 I`.
* Both displacement lifts preserve vertices and their complete boundary trace,
  annihilate every registered affine patch, and differ by a nonzero interior
  physical strain.  Their difference energies are exactly `128/35` on the
  square and `305584/175` on the skew map.
* All eight D4 operations distinguish the reflected director sign
  `a3_sign=-1` from the unchanged oriented-cofactor sign `chi=+1`.  The
  physical lift is invariant.  Normal reversal, rational frame rotation,
  origin shift, and unit scaling also close exactly.
* The hostile E1-A control remains a cyclic edge-difference map of rank three,
  annihilates common drill, and retains the exact full-rank upper bound 17.

These two admissible, affine-covariant displacement lifts are inequivalent,
and no public primary source selects the free interior coefficient or even the
mean-spin trace normalization.  Selecting one by rank or a benchmark would
violate the preregistered source gate.  It is therefore correct to stop before
membrane rank 9, full rank 18, patch, mixed/condensed, extension, or other
mechanics outcomes.

## Reproduction and frozen identities

I ran

```text
python -m pytest -p no:cacheprovider \
  tests/test_s4_e2_a_exact_kinematics.py \
  tests/test_s4_e2_a_qualification.py -q
```

and obtained `7 passed in 0.54s`.  I then launched the oracle twice in fresh
processes using the caller-bound contract.  Both runs returned byte-identical
5,821-byte canonical UTF-8/LF output with SHA-256
`37C803C565602E1AF983AA8374C3DA090EFD1CC73F2B672F2C815CC6A56B623D`.
`git diff --check` also passed.

The final reviewed inputs are:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `.gitattributes` | 1,644 | `CFA148F1B78C01C2C6E89DEBD6600458380C64097DBB7FCF54BA0C6B105A600A` |
| Governing plan | 5,679 | `D8F39F3C75D19AF3C26A69845216AF9A7C948EE1F6CCB3E3BBFCF0A21C8131F4` |
| Baseline | 1,891 | `EF62A7F2F40089A47237A17C03A1FC3C7D3BA5A9AA696D4C326CA4DB2A994A92` |
| Environment | 912 | `2A0E7D3B568F5ACC912A7897E3B4787F7AC9BBA57739BFD346A1D5DB68B82C99` |
| Test inventory | 1,582 | `8DD67A8940FB65601CFA43455558724E507014F327C047AF1E56A21D21A2CBA9` |
| Source registry | 5,509 | `15AFFE358D5551EB08359267B6B0FD3FAAF6F15198C22475B37DF8AD4C014D2E` |
| Formulation identity | 4,111 | `1D68C16149F0368E883CCD1611107068DF662C794A6D58541665A5F99472421D` |
| Formulation derivation | 10,061 | `E7CE3A36E895238E1E31734E81CEB99A1A804E8D6B08101DBC2EA5452DE3B16F` |
| Extension audit | 2,351 | `F6CC6AD38AEA8FCC6C402301F58CA47AFF03B738CFC2E44E1F23A6F8CD19BACA` |
| Exact cases | 2,352 | `61ED18EDB32B0DAF288E3EB66FEA522D5D4588542F11D8881B5B7762FCAC3729` |
| Exact oracle | 42,587 | `A1796D466DF6DDCDB420987F8FAFC3787B563C16F0B8AEC58C716C0EF194D151` |
| Emitted contract | 3,433 | `E3AA3BC6AD8FAD7EB64564851FC558B0D1B2ACB533B292EEBA580EBA47B02D3E` |
| Canonical output | 5,821 | `37C803C565602E1AF983AA8374C3DA090EFD1CC73F2B672F2C815CC6A56B623D` |
| Qualification report | 5,579 | `28FA4039DA2E47D9B91CD6C21620685E7DD710C6EE79AF7745022242429CE074` |
| Exact test | 10,443 | `64862C2FAA4B96C99358B21ADFCABD16BA26CBEDB06E1E4CDBBD1EE5254D6E6D` |
| Qualification test | 10,984 | `F8F3676E224D43E507CB0B7189FCC36130BAEA60836E43BA3FA67C1B338549A8` |

## Scope and terminal boundary

The only tracked modification relative to the authority commit is the LF rule
addition in `.gitattributes`; the remaining E2-A paths are new evidence,
oracle, report, and test paths allowed by the contract.  `src/` has no diff.
There is no public import, export, API, selector, serialization, dispatch,
default, production, push, publication, or cleanup change.  The six preserved
untracked evidence roots remain outside the packet.

E1-RH remains `DEFERRED_NOT_RUN`.  All downstream E2-A mechanics and extension
rows remain `NOT_RUN_IDENTITY_AMBIGUOUS`.  The overall release terminal remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`, and legacy `ShellElement` remains the
production default.  Any future interpolation choice must use a separately
preregistered successor identity.
