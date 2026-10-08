# F03 bounded axial patch: exploratory six-case result

22 September 2026. **Six of six small classical patch cases completed; no
G0B admission or multiplier policy selection.** This is a separate source-
frozen exploratory record. The earlier four-case Nm128 registration remains
terminally no-go; its failed CST-CB case was not rerun.

- Source commit `de4b54274cf7d1f31f28b585590a5249231f7aff`.
- Registration `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-axial-patch-registration-v1/registration.json`, SHA-256 `3f72a62a7c841a5429464b60740cb39b86ffc1f4282b13adc49fb5b2aab96f72`.
- Six raw case JSON files and receipt at `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-axial-patch-cases-v1/`, receipt SHA-256 `204513c44a06617e2efdbe85bf912aded4a2af750c5a40113c3337b95ce4d291`.
- Read-only field/receipt adjudication at `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-axial-patch-adjudication-v1/adjudication.json`, SHA-256 `290621987a79011f0607d7b771f8f323b7cce9d0a04090077ac35ca43ac0436f`.
- Independent read-only mechanics review verified registration, exact cases,
  receipt hashes, numerical fields and the limited interpretation. It did not
  rerun cases. Twenty-seven related bounded focused tests passed at the
  source freeze.

All cases fix `(Ns,Ny,Nb)=(16,8,64)`, use P1 exact segmented weak coupling,
and vary Nm8/16/32. Nm16 has beam:mortar 4:1 and longitudinal shell:mortar
1:1; Nm32 adds multiplier rows without changing the primal mesh.

| Host | Nm8 axial beta | Nm16 axial beta | Nm32 axial beta | Nm32 shell action fraction on the changing lowest vector |
|---|---:|---:|---:|---:|
| Q4 | 0.39903169 | 0.32976602 | 0.26001641 | 0.3067 |
| CST-CB | 0.39057949 | 0.31995578 | 0.25827958 | 0.3708 |

All six bounded outputs were finite. Maximum side stiffness solve residual
was `9.70e-11`; maximum axial generalized eigen residual `2.66e-14`;
primal cross block was zero. Maximum observed case time was about 0.375 s
and end-of-case RSS 67,383,296 bytes. The registration's 60 s and 1 GiB
values are *post-case observation limits*, not a hard wall-time or RSS cap.

The shell and beam Schur contributions add for the uncoupled supported
primal energy. Side fractions describe work on each case's **different**
lowest axial eigenvector; their change does not isolate a causal shell or
beam trace. Q4's shell-alone Nm32 generalized minimum is about
`-3.06e-15`, classified as near-zero/unresolved relative to its spectral
scale, not physical negative energy. The separately derived supported
element energy is mathematically positive for the admitted regular mesh
and supports; a positive sparse-eigen screen alone is not a certified
floating-point lower bound.

This bounded trend and the saved full-size Q4 post-hoc axial mode support
an axial interface-resolution hypothesis for **both** classical shell
hosts. They do not show that P0, P1 or a dual-space candidate transfers
physical load correctly, satisfy the nonmatching interface stability gate,
or qualify the native six-channel B3-GE/E4-PL connection. Next isolate the
axial host and trace with common physical traction and resolved loading,
compare genuinely distinct multiplier spaces, and freeze a physical floor
and holdout before another full-size registration. G0B and all later gates
remain open.
