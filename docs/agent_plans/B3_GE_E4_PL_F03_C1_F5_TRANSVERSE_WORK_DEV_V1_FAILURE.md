# F5 transverse-work V1 diagnostic failure

The first bounded local invocation produced no result file. It tried to
reassemble forces from rounded saved FRD displacements using the independent
`element_forces` implementation, then compared them to the separately
validated action integrated from the CalculiX printed Gauss stresses. The
force and sign conventions differed, so the source guard stopped with
`ArithmeticError: bond action does not reproduce validated F5 recovery`.

The local comparison found `-0.0156205535 J` and a first wrench component
`+5974.7758 N` from that route, versus the validated stress action
`+0.0152174641 J` and `-5974.9837 N`. No mechanical interpretation is
drawn from the failed V1 route. V2 uses the exact saved-stress reconstruction
and checks it against the existing source-bound recovery before decomposing
work. The underlying F5 files and validated recovery were not modified.
