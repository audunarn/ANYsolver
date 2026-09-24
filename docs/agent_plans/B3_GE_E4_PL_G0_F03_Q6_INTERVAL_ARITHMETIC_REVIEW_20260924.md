# F03 Q6 compiled interval arithmetic: independent conditional review

**24 September 2026. Read-only review of an experimental certificate kernel;
not an installed scientific acceptance.** The reviewed source is
`scripts/_b3_e4_f03_q6_interval_kernel.py` on integration commit `af5ba8d3`.
The review did not edit source or execute a long Q6 case.

For finite binary64 CSR values and block entries under correctly rounded
IEEE operations with gradual underflow, the reviewer found an induction
argument for each CSR row: the exact product lies between the adjacent
floating-point values around the computed product; adding each lower and
upper endpoint and stepping outward preserves inclusion of the exact partial
sum. Stored zero terms contribute exactly zero. Any nonfinite returned
endpoint is rejected rather than used as a certificate.

The reviewer inspected the local int32-index/float64-data Numba specialization
on AMD64 Family 25 Model 97 with NumPy 2.4.6 and Numba 0.65.1. Generated
LLVM used ordinary `fmul`/`fadd` without fast-math flags and called
`numba_nextafter` between operations; inspected assembly used scalar
`vmulsd`/`vaddsd`, without FMA. In a separate short process, the runtime
arithmetic signature passed the original MXCSR mode (`0x1fb2`) and rejected
FTZ (`0x9fb2`), DAZ (`0x1ff2`) and both (`0x9ff2`); the original mode was
restored. No finite-float64 counterexample was found for this inspected path.

This is a **conditional local arithmetic argument**. It is not a proof for
other compiled specializations or installed package identities, and it does
not make the X0 saved-input replay an independent implementation. Before a
formal one-use run, bind the actual installed CPU/Numba/binary specialization
and runtime mode, independently review its compiled operations and
exponent-boundary rational tests, and close physical-observable error
propagation and the remaining G0 mechanics gates.
