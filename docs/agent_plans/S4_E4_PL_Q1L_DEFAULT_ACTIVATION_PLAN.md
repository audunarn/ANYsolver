# E4-PL Q1L: Production Default Activation

## Purpose

Activate the parity-closed E4-PL implementation for production four-node
shell creation.  Q1L changes selection only; it does not change the Q1J/Q1K
mechanics, tolerances, material laws, recovery, or state algorithms.

## Selection contract

- `create_element("shell", ..., four_nodes)` and
  `create_shell_element(..., four_nodes)` create
  `QualifiedE4PLShellElement`.
- TRI3, TRI6, Q8, and Q8R remain `LegacyShellElement`.
- `create_element("legacy-shell", ..., four_nodes)` and
  `create_shell_element(..., formulation="legacy")` are explicit rollback
  routes.
- The primary panel-mesh, generated-geometry, cylinder, and SESAM builders use
  `create_shell_element`; they do not carry independent formulation switches.
- Direct construction of the compatibility class `LegacyShellElement` remains
  available, but it is not the production Q4 default.

## Release gates

1. every required row in the maintained parity matrix is closed;
2. topology dispatch and rollback are tested;
3. all primary builders select E4-PL for Q4 and legacy for non-Q4;
4. serialized Q1J and Q1K records remain reconstructible;
5. focused parity, complete solver regressions, and package tests pass;
6. cold/warm performance remains within the Q1J accepted path;
7. the activation is reviewed and merged through the protected path.
