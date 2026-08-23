# E4-PL-Q1Z: Bounded Support/KKT and Reaction Closure

Q1Z is a research-only successor to merged Q1Y3 commit
`795ae1b44748cd6896a49079f82c947b96260aea`. It consumes the seven accepted
Q1Y3 stiffness proofs and never reassembles the 38-field stationary system.

For every registered geometry, Q1Z reconstructs the equation-7 frame,
physical/drill embeddings, frozen physical load, full physical-zero support,
four-coordinate drill block, registered KKT solution, reaction, and virtual
work. The seven base certificates extend to all eight D4 numberings by exact
operator transport. The transformed Q3 case additionally proves proper-global
support and reaction covariance.

Seven producers run concurrently. Each completed proof is checked by two
independent SymPy processes; at most four checkers and eight weighted child
slots run concurrently. Every child has one numerical-library thread, an
8-GiB memory limit, and a 180-second wall limit. The complete formal cycle has
a 300-second deadline and is run exactly once after noncanonical Q0/Q5 smokes.

Q1Z closes only the registered support/KKT boundary. It does not establish
full local qualification, production readiness, or Q1B authority. Production
remains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED` and Q1B remains unauthorized.
