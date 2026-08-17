# E4-0 independent review

## Verdict

`ACCEPT_NO_P0_OR_P1` — the corrected E4-0 packet is internally consistent,
content-addressed, reproducible, and confined to its registered non-production
scope. No P0 or P1 finding remains.

This verdict accepts the evidence process and the bounded route result. It does
not register or qualify a shell element, approve a DNV product, authorize
production implementation, or establish non-affine, locking, nonlinear,
buckling, mass, dynamics, or performance behavior. The controlling terminals
are:

```text
Core:       GO_E4_OPEN_CORE_IDENTITY
WS:         NO_GO_E4_WS_LOCAL_CONDENSATION_AND_RANK
PL:         PROVISIONAL_GO_E4_PL_LINEAR_QUALIFICATION_PLAN
Next:       EXECUTE_ONLY_SEPARATELY_REVIEWED_E4_PL_LINEAR_QUALIFICATION_PLAN
Production: NO_GO_PRODUCTION_RESTRICTION_UNCHANGED
```

The WS terminal applies only to the frozen direct-additive functional
`Pi0(q)+lambda^T Cq`. A jointly coupled energetic/dual Hu-Washizu architecture
is not disproved; it remains an unclassified new identity requiring a separate
governing plan.

The first review pass found a P1 scientific defect: the core and PL
classification initially used a generic 35-variable identity/Gram witness
instead of the registered Wagner-Gruttmann stress/strain spaces. That witness
was removed. The corrected independent oracles assemble the actual source
`F`, `Gq`, `H`, `D`, `S`, and `K` operators. The review also required the WS
scope to be narrowed to the direct-additive identity, the public-author-upload
provenance of the copyrighted 2011 chapter to be recorded consistently, and
the successor plan to retain the concrete DNV, energy-non-intrusion, and load
boundaries. All corrections were completed before this acceptance.

## Authority and immutable history

The reviewed branch is `codex/s4-e4-variational-drill-closure`. Its authority
is commit `c55ad9e5f8e78b1749c4152e4ba66b6f9e20b198`, tree
`e7e35bb880a88a8f7d736d32652c80442d8b9ec1`, with sole parent
`2ac678a7f94c250fe433f66378a83508d86ee499`.

The 30,628-byte attachment is correctly treated as superseded long-range
design input at SHA-256
`EF02CDFD814F57704EA6CC1972340C09563B35123393645353371EFFC2BCBFC8`,
not as executable authority.

The accepted histories remain separate closed-world tiers rather than one live
successor suite:

- E0: 94 nodes at `87b639499187736c59d87bc4aa8e6bd7f819d28b`, tree
  `c01fd5cab7b63325e6cb5b70000f4586d4788563`.
- E1: 16 nodes at `281ed90e148c125edbec27e7336a8f9f0df08edc`, tree
  `1ee60da4717055f5cc1b37ff9369877bb1867861`; the historical report text
  saying 15 tests is preserved.
- E2-A: eight nodes at `2ac678a7f94c250fe433f66378a83508d86ee499`, tree
  `f7382e2b88343ac29c9a9e3c424f618a3652cc01`.
- E3: 14 scientific nodes plus its closeout leaf at the E4 authority.

The baseline manifest preserves every A/B/C/rank-four/E0/E1/E2-A/E3
terminal, including E1-RH as `DEFERRED_NOT_RUN`. The E3 status, review, and
completion identities remain byte-exact. Nothing in E4 reinterprets those
results.

## Source governance and copyright

The `P`/`D`/`B` boundary is applied consistently: printed primary statements
may close source rows, independently derived consequences require exact
evidence, and background material cannot determine an equation or outcome.

- Wagner-Gruttmann 2020 is the official open CC-BY-4.0 core source: 3,267,230
  bytes, SHA-256
  `DB68AD45455999D47D6152E736D7277F28AC1C0D85063790B15FE4089293A712`.
- The 2004 public official report supplies the linear MITC and isotropic
  resultant details: 878,871 bytes, SHA-256
  `8EBDBA969BB3E2A34288EA3B5D52014C68C0E30FD2A9B36B1F92EB3073AEE7A0`;
  no licence is asserted beyond its public official availability.
- The Wiśniewski-Turska 2011 chapter is recorded as a public author upload and
  a lawful user-supplied local copy: 310,978 bytes, SHA-256
  `E6AFAADE32B33D710D3C038635FE2AD2729E32FB952C5EC6706E68A93A3B1860`.
  Reuse remains copyright-restricted or unclear.
- The MITC9i primary source is CC-BY-4.0 and supplies only the shell-scalar
  perturbed-Lagrange normalization: 1,302,612 bytes, SHA-256
  `5C66A76D39682F71C13208E71AFFA585FD3CD1E284185360B825572DC8BA048B`.
- General quadrilateral weak-symmetry theory and the 2025 one-point shell are
  background/deferred references only.

No external PDF, page image, figure, screenshot, table, external code, or long
verbatim passage is committed. The packet contains bibliographic identities,
independent derivations, exact cases, oracles, and tests only.

## Open-core audit

The corrected core certificate uses the actual source-specific 14 stress and
21 independent-strain parameters. For both the normalized square and the
rational affine witness it proves

```text
rank(F)=14, rank(Gq)=14, rank(H)=21,
rank(D)=35, rank(K5)=14, nullity(K5)=6.
```

The exact LDL pivots of the condensed stress block are all positive, so the
physical material operator is PSD. The six recorded null vectors are exactly
the physical rigid modes. The `20+4` selector identities are exact, the
24-coordinate embedding has rank 14 and nullity ten, and the four additional
null directions are coordinate drills. The actual 35-field stationary and
condensed energy, residual, tangent, virtual work, load work, and physical
recovery agree. Direct drill moments remain excluded.

This supports `GO_E4_OPEN_CORE_IDENTITY` only for the bounded flat-affine,
linear, homogeneous-isotropic, positive-thickness reference. It is not a
six-DOF drill completion by itself.

## Weak-symmetry audit

For the exact functional `Pi0(q)+lambda^T Cq`, multiplier stationarity is
`Cq=0` and the multiplier diagonal block is zero. The multiplier therefore
cannot be uniquely solved and Schur-condensed at fixed 24-coordinate `q`.
The exhaustive algebraic exits either retain a saddle unknown, reduce the
external coordinate space, introduce compliance/regularization, or add
primal energy. Setting `C=0` cannot lift the rank-14 core.

The exact witness records `rank(C)=4`, zero multiplier-block rank, KKT rank
22, and the prohibited `C^T C` completion rank 18. The resulting
`NO_GO_E4_WS_LOCAL_CONDENSATION_AND_RANK` is a necessary theorem for the five
simultaneous frozen requirements, not a theorem against weak-symmetry methods
in general. Stopping the macroelement and inf-sup campaign was therefore
correct for this identity.

## Perturbed-Lagrange audit

The PL identity retains the `1,r,s` coefficients of
`c=theta_D-(v_x-u_y)/2`, deletes only the rotation-only `r*s` coefficient,
and controls that residual mode separately at the fixed printed scale
`epsilon_hg=10^-3`. The thickness-explicit scalar functional

```text
integral_A h [T*c - T^2/(2G)] dA
```

is dimensionally closed; MITC9i equations (18)-(19) independently anchor this
scalar normalization, and `gamma_PL=G` requires no new public material field.

The corrected oracle combines the actual 35-variable WG block with the three
multiplier parameters in one 38-variable functional. It proves the local
block invertible, mixed/condensed stationary parity, retained-constraint rank
three, independent residual-row rank one, total stiffness rank 18, nullity
six, symmetry, and PSD energy on both affine witnesses. Pure common drill and
translation-only spin are separately energetic, their matching rigid
combination is exactly null, and alternating drill is hourglass-only. The
registered patch fields, rigid images, D4/frame/reversal/origin/unit actions,
and decade parameter diagnostics pass exactly.

Multiplier and hourglass quantities remain numerical diagnostics. They do not
enter physical `N/M/Q`, stress, yielding, fatigue, or code-check recovery.
These fatal screens support only
`PROVISIONAL_GO_E4_PL_LINEAR_QUALIFICATION_PLAN`.

## Route and successor boundary

The only immediately executable successor is the separately reviewed E4-PL
linear qualification plan. That plan now requires:

- a preregistered admissible non-affine geometry class, source-covariant
  residual vector, element rank/rigid closure, assembled stability, patch,
  distortion, and thickness/locking gates;
- existing S235/S275/S355/S420/S460 records with zero new inputs, separate
  RP-C208 material provenance and July-2025 RU-SHIP project-edition metadata,
  and the wording “compatible with DNV analysis workflows,” never DNV-approved;
- fixed `gamma_PL=G` and `epsilon_hg=10^-3`, with outcome-independent
  numerical-energy and drill-participation limits rather than tuning;
- physical loads restricted to `range(T5)`, with direct drill/normal moments,
  coupling, and moment-transfer claims deferred; and
- density recorded but unused, with no drill inertia or dynamic claim.

This is a qualification plan, not a candidate registration or implementation
authorization. A broader coupled weak-symmetry identity remains unclassified
and is not authorized within E4-0.

## Determinism and tests

All three oracles use exact rational arithmetic and the Python standard
library only. They reject duplicate keys and nonfinite JSON, validate
caller-bound contract hashes, and produce canonical UTF-8/LF JSON. Each
artifact test ran its oracle twice in fresh processes and required byte
identity.

I ran the five pre-review E4 files and obtained `17 passed in 7.20s`:

```text
python -m pytest -q -p no:cacheprovider \
  tests/test_e4_baseline.py \
  tests/test_e4_core_identity.py \
  tests/test_e4_ws_feasibility.py \
  tests/test_e4_pl_identity.py \
  tests/test_e4_route.py
```

`git diff --check` passes. The index is empty. Relative to the authority,
`src/`, `.github/`, and `pyproject.toml` have no diff.

## Frozen reviewed artifacts

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `.gitattributes` | 1,894 | `60425638D89A10E0EFFEE7C6CF2D40C7A0A9538453779B3C140FCACBD8C35886` |
| Governing plan | 5,570 | `BE515556E2019CDE69E4E7489FD9200F16CDE8D82C032131776EA0520DEB59A1` |
| Baseline manifest | 3,309 | `7A404185E3F15FA56B589264FA5C816031B3BF25BA8003D081844B517EABB793` |
| Environment | 1,235 | `EC3FE4B95C556F8CF6983083FD29EBA974D9FB953E33017CA3C37CBDC37B3B6F` |
| Test inventory | 3,581 | `9B6F67242586BFC5A661D2790AFA8774254D68116871D8ACA4E3D1F126D220DA` |
| Source registry | 3,421 | `66C395568FB4BCC90BCD57D9B8167E204C92A4390BBA643F3FA8516470CA4FA3` |
| Core derivation | 6,688 | `BAFC21DC85C0CD9101C30ACC5D84F4BC57F3394EA4C0AEFB31CCFA7E43655E5D` |
| Core source map | 2,758 | `594C74AD59486AE6A23074079E610ED9E1625DA15B626A97BB98E31ED55F1EC1` |
| Core cases | 5,435 | `FE08E59D9E01073E04251C52544EDF10C4CC86861EA8B98FC6CB1A645427FEF2` |
| Core oracle | 30,906 | `C829DD61CEF0D42369995DE74EF1630C64AF94368300D154933D87B5EE885E9F` |
| Core contract | 2,284 | `8768ABDC5D77B5FCC1643AF69920EFEB83F27DDFBDE17525F06EE2B53A5C1678` |
| Core output | 2,832 | `F9C39E4E92D690F6FDECB756E114A30B579E4526FBDB84E73A260938E069BC14` |
| WS theorem | 3,839 | `80E02F2564D6DE6D5E1A66857A78D97FCA83C828AEAB20BFE4707408EAD7BF19` |
| WS source map | 1,204 | `F421572687A814108C92F756DCCB7483429D0E67AA35268E4D6014F1BA9848E4` |
| WS cases | 1,224 | `07C6ADC51095CF318EAECABECFF193FBB0CE2A2E2B604A9692F111BEBB8892E0` |
| WS oracle | 12,042 | `10FA79C24BEE43E30653D69207E9A6F78C1F4D86238BABAD2B81266EFDC37985` |
| WS contract | 3,033 | `AAB8E8ECC846FE652F9FAC1A2F02FC50B0AB8E179D808132AB3AF758BC7F82B8` |
| WS output | 1,327 | `9BBAF85E85734A36DA22B4780F450A5957CCF4ABE358BB24AEDAAB977C77057E` |
| PL derivation | 8,302 | `14BDA35109FE8C653B85BF890C36CC454CDE938BCDC3820CA39479EC620EFB4D` |
| PL source map | 3,460 | `8919A38DB727D5E863DA70161209C80F2A0F01851392A13A3080354F849B6B66` |
| PL cases | 4,064 | `37D0BA2197246A8D752916EDF40BBDF8E946946E93756C1B042FE374DFF53B59` |
| PL oracle | 44,814 | `789B7DB6906ADD454B2C65001EDBA28F5AC9DBC3FB2AB598D3EE2F95D3F0D447` |
| PL contract | 3,165 | `9B3B2C151B2A910862F2D61ADBFACC8AEB72E7214E6A096B0C53BF2CF447A547` |
| PL output | 4,920 | `D6E0DA7E3300BCF691C87875B1FD3F215A6C70F611C52BB74A6579F20772E62D` |
| Route report | 5,696 | `0DA0B9ED4F604BD8D476E289102B0D44779EFB73F3F1BDD2BA26AB21CED9FF2D` |
| Conditional PL plan | 4,670 | `912322A8158255F17DDA44A3BB8FD59EFF1FC3B6B1E9D6BBB22B4E49A72BD193` |
| Route contract | 2,374 | `BD8F7C0FF49377224E9B2E9BE804B3423D6299898F66B5C117B0A744FC07A453` |
| Route output | 1,371 | `796A33AC0C01645A72E28A94C43688126B2D14EBAAB2A0C40ABB3CAC05582461` |
| Baseline test | 9,222 | `0B7B4C6359517A966833BB441D57F610D3527F996923290BA9559BBE1EADA864` |
| Core test | 7,937 | `021A32350DDE166853A8D7BE85F98CF80A822D00C9C4EE774BFB995DED67691E` |
| WS test | 6,383 | `C42A69CDFCD766468485B53E600BE83B4373A399C09164A86168765F5CE0A1C4` |
| PL test | 8,572 | `667FE0E3676746776B1706FCE7903EB2BFEA6BE19625D4097BC420543672370B` |
| Route test | 8,516 | `59A3DE6B6684B0808AF18FD1B68C07E9D3696437C2F1238C84B5133ED02003F7` |

## Repository boundary

The only modified tracked path is `.gitattributes`, which adds LF rules for
the registered E4 path families. All other E4 paths are new evidence,
derivation, contract, report, plan, review, or test paths allowed by the
extent manifest. The six inventoried historical untracked roots remain
preserved.

No production/package/workflow source, public API, selector, serialization,
export, dispatch, default, push, merge, publication, or cleanup change is part
of this acceptance. Legacy `ShellElement` remains the production default.
