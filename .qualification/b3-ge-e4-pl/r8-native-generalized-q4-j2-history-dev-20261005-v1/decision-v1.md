# Required generalized/Q4-J2 accepted-history slice
Reuse EXACT existing _definition(plastic=True,mixed=False): generalized strength4000/hardening1e8, shellJ2 strength1e6, supports/geometry/three point identities unchanged.
Question: does a zero-force/reference1000N-seeded native adaptive displacement history accept simultaneous generalized and Q4J2 flow, and support exact continued restart?
One declared nominal target at105z; direction100N. Existing6cuts24attempts20iterations12backtracks;600s/2GiB/affinity1/pools1/JIToff. No sweep.
Only if nominal completion AND same accepted-update both-domain flow, proceed quarter-unload/negative/1.1reload. Otherwise preserve accepted prefix andSTOP. Existing force history evidence remains separate; no model or criterion change.
