# Physical-fibre retained contact development slice — 5 October 2026

The existing native material/S3 owner now composes the physical-fibre family
through its real retained operator, return map and history store. All native
internal coordinates remain coupled, with the complete spatial tangent correction
applied once. Generalized-family identities and defaults remain unchanged.

Independent axial/biaxial sectional elasticity gives
`diag(1000,400,350,.8,1.,1.2)` for the declared four fibres plus background.
Production residual difference is zero; maximum tangent difference is
5.551115123125783e-17. Directional errors are 4.98069680341179e-10 and
6.315530262097181e-9. The coupled first-contact check passed in 105.6784 seconds,
peak182566912 bytes, with37candidate/37pair evaluations and actual family-bound
restart. It includes one rejected axial-front trial; that diagnostic is retained.

Raw records: `C:/ANYworkspaceWork/contact_native_fibre_s3_20261005/candidate01`.

| Batch | Result and interpretation |
|---|---|
| source_fibre_local | NONPASS: support bytes were not JSON serializable; fixed with explicit SHA binding |
| source_fibre_local_support_hash | 5 passed, 3.3895s/183193600B |
| source_fibre_coupled | 1 passed, 105.6784s/182566912B; precedes final captured-cache hardening |
| source_fibre_cache_guards | NONPASS:12passed/1failed; expiry test tried serializing an entire owner state |
| source_fibre_cache_guards_fixed | 13 passed,4.0336s/188329984B; material derivatives, cache/probe/deadline mutation guards, cancellation/exception and expiry |
| source_fibre_shared_driver_regression | 3 passed,2.7420s/180498432B; historical cancellation, path columns and subclass dispatch |
| installed_fibre_guarded_coupled | 1 passed,105.9044s/181051392B; final guarded coupled first contact and byte-exact family-bound replay |
| installed_fibre_guarded_local | 13 passed,3.8406s/187940864B; final installed local guards, work and rollback |

The expiry test defect was repaired without changing the production deadline.
Each native owner retains its existing120-second construction-to-expiry lifetime.
No clock reset, enforcement/integration relaxation or ignored contact is introduced.

Supporting source review identified unbound consumed caches and unclear expiry
semantics. The adapter now binds force, reference arrays, node maps, initial states,
program data and exact probe ownership. The construction clock cannot be rebound.
The documented expiry is an explicit resource preflight error, preserving the
existing limit. Review found the once-spatial correction includes the compensated
Hessian low part. This is same-family supporting scrutiny, not independent
engineering acceptance. Optional Mistral remains unavailable from retained evidence;
its broader authorization does not establish renewed availability.

New wheel SHA256:
`813b08560894ae4b68f84b8e4eb55c91da845c91bca5ae9ff9a093d273c3f6a1`.
All524production Python files match the installed wheel. Runtime records bind
219installed imports, JIT disabled and both effective BLAS pools at1thread, with
no runtime-admission errors. Actual final active checkpoint SHA256:
`bfd2b7680230ee24bce1ba9532171869ed376c1f7c3d177f4f2c2d44275e2f88`.

Implemented and development-tested only. Plastic contact history, full cycle,
section/material admission, enforcement convergence and independent engineering
acceptance remain open. FullC0–C9 is incomplete; no release or speedup claim.
