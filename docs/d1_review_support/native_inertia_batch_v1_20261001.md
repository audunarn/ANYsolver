# Prepared finite-inertia column batching candidate

Question: can the measured8064 scalar derivative contractions be replaced by columnwise NumPy contractions without altering any discrete finite work? Own one NEW kernel and this prefix only. No dispatch, centered owner, p5 scalar owner, midpoint, codec, API or managed-tree changes. Source is UTF-8/LF. Prepared section_mass/stations come from the unchanged centered geometry/quad owner; no geometry, centroid, measure or frame reconstruction. Existing centered owner still owns compensated momentum pairs and42 extension.

## Same product rules in column form

At a station Q=U R0,d=U d0,B maps24 spatial velocities. Base body work is unchanged: (u,w)=(Qᵀv,Qᵀomega), body a=(Qᵀa−w×u,Qᵀalpha), (p,h)=J(u,w), physical f/n use the original momentum cross terms. Same station order accumulates T,M,p_generalized,I,P,H. Batch C active velocity columns and3 configuration columns into3×(C+3) arrays. For a generic column(eta,dd,delta_v,delta_omega,delta_a,delta_alpha):

- du=Qᵀ(delta_v−eta×v), dw=Qᵀ(delta_omega−eta×omega).
- da=Qᵀ(delta_a−eta×a)−dw×u−w×du; dalpha=Qᵀ(delta_alpha−eta×alpha).
- (dp,dh)=J(du,dw), (df,dn)=J(da,dalpha); df+=dw×p+w×dp; dn+=dw×h+w×dh+du×p+u×dp.
- changed=Bᵀ(Qdf+eta×f,Qdn+eta×n); changed[cell_spin]+=dd×f.

Velocity columns use eta=dd=delta_alpha=0, delta_v/delta_omega=Bcolumn, delta_a=delta_omega×(omega×d)+omega×(delta_omega×d). Configuration columns use eta=e_k,dd=eta×d,delta_v=omega×dd,delta_omega=delta_alpha=0,delta_a=alpha×dd+omega×(omega×dd). These are nonsymmetric force derivatives at fixed supplied spatial v/a; no potential pullback. Column orientation is explicit; row-transpose equivalents are du=(delta_v−eta×v)Q and world df Qᵀ. All nodal algebraic columns remain exact zero.

## Frozen local check

One integrated pytest case under180s/1GiB, threads1, freshcache/tmp: four declared rest/finite off-axis/fast finite/translation poses with anisotropic nonzero-centroid section and original48 prepared stations(order24). Compare complete original scalar response to candidate with fieldwise norm-scaled1e-13, literal independent station virtual work1e-13, velocity/configuration FD at1e-5 and2e-6 with1e-5 limit, readonlyness, exact42 algebraic zeros and finite/positive input negatives. Kernel-only timing order scalar,batch,batch,scalar on the declared fast pose, preparation outside both. No new native state/trajectory/accuracy qualification or whole-route savings claim. First genuine gate failure stops; raw retained.

Module SHA256 9ee021df59f5974092e94a002ed6da8b8143e0a9ed891982992a60e50d194682; test 184c3a0d42cadbfba7a2e1f8530e92c8fb8c6e87ff0aea4f90605a149cca1a8b; inputs aa82033132eecab24554534c5df7dbb7ae54966e57763a58d712f9c6e9e0c111; 451 source bindings. Subsequent integration/cost checks belong to lead; independent source/math review is separate.

## V1 first-failure disposition

Retained NONPASS after four case evaluations, 4.0753270s/196.435968MB,451/451 source bindings unchanged. Rest/base energy,M,p,I,P,H are exact; resolved finite/fast dv,dq differences at most 2.357459958e-16. Fourth pure-translation dv scalar norm 8.991548771e-17, batch norm 8.987064088e-17, difference 4.690969419e-18, max entry 2.504925638e-18; division by scalar signal yields5.217% and fails the frozen1e-13 relative gate. Original failure/raw/XML/log/input/source retained; no gate regrade. Virtual work, FD and kernel timings remain unissued. Raw SHA256 183f01c7b193863bb46eb97869843a92b6209cf74f801b64738c24e8b969bbc0.

Analytic branch: with omega=alpha=a=0 and translational section block rhoI, p=rho*u and h=rho*c×u. For arbitrary delta_v/delta_omega, df=−rho*delta_w×u+delta_w×p=0. The moment derivative is −rho*c×(delta_w×u)+delta_w×(rho*c×u)+rho*delta_u×u+u×(rho*delta_u−rho*c×delta_w)=0 by the triple-product identity. Thus physical dv is zero; the scalar residual is a finite-precision cancellation signal, not a resolved derivative reference. The batch difference is much smaller in absolute magnitude. This diagnoses the chosen denominator, not a relaxed or accepted gate.

Concrete next source question: choose a prospective, dimensionally declared positive derivative scale from original section/station/velocity contractions for this exact-zero branch, retaining1e-13 multiplier and all resolved-field gates. Do not widen tolerances or omit this case. No additional numerical work is launched by this disposition.
