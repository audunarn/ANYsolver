# Direct retained-state ownership boundary

Base470b5ef2f2002cb0742cfa0ad89a722fd6ec21a4 has passing restart/cancellation
development evidence. Direct Context.recover currently checks type/model ID
and material history but not issuance of the State object. State dataclasses
can be copied or constructed independently. Stage/checkpoint entry points also
need explicit issued-state/record-chain checks before mechanical evaluation.

Freeze adversarial tests first. Reject copied, foreign, altered or mutated
objects before calling operator evaluation/recovery. Require issued ordered
record chains for checkpoint generation and matching predecessor state for
staging. Legitimate initial, controller-created and authenticated-restored states
must continue to work and retain identical capsule bytes.

Implement context-local strong issuance references and immutable content hashes;
these protect API ownership, not execution against hostile Python code that can
modify private internals. Internal recovery used to construct a validated record
must remain separate from the externally callable recovery boundary. No change
to mechanical equations, section histories, scientific tolerances or serialized
schemas is authorized. Preserve the old evidence and any red-test outcomes.

Run the narrow red/green boundary tests under one thread/24GiB/600seconds,
followed by bounded existing state guards and port checks. Keep qualification
incomplete until wider requirements and independent review pass.
