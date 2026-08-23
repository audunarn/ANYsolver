# E4-PL-Q1Z2: Targeted Q3-star support closure

Q1Z2 is a research-only successor to merged Q1Z commit
`d325ea8f787509a056b51aa21b07107a40bdfae0`. It does not rerun any producer
or any of the six completed Q1Z checker pairs. It binds those accepted 48
numbered cases and runs only two fresh copies of the frozen Q1Z checker on the
preserved `Q3_TAPERED_SKEW_RSTAR_TRANSLATED` proof.

Both replicas run concurrently in distinct fresh directories with one
numerical-library thread, 8 GiB each, a 180-second child limit, and a
210-second global deadline. Their canonical bytes must agree. The cycle is
run exactly once and is never retried automatically.

Successful composition establishes only the registered 56-case
support/KKT/reaction boundary. It does not establish full local qualification,
production readiness, or Q1B authority. Production remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED` and Q1B remains unauthorized.
