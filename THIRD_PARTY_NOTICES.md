# Third-party notices

ANYsolver does not vendor or bundle these packages in its source distribution
or pure-Python wheel. They are installed separately by packaging tools and
remain governed by their own upstream licences. The machine-readable release
inventory is `dependency-licenses.json`.

| Dependency | Requirement | Licence | Distribution status |
| --- | --- | --- | --- |
| NumPy | `numpy>=1.26` | BSD-3-Clause and bundled-component licences | Runtime dependency; not bundled |
| SciPy | `scipy>=1.11` | BSD-3-Clause and bundled-component licences | Runtime dependency; not bundled |
| threadpoolctl | `threadpoolctl>=3.5` | BSD-3-Clause | Runtime dependency; not bundled |
| ANYmaterial | `ANYmaterial>=0.1,<0.2` | GPL-3.0-or-later | Runtime dependency; separately distributed |
| ANYmesher | `ANYmesher>=0.1,<0.4` | GPL-3.0-or-later | Runtime dependency; separately distributed |
| ANYfileio | `ANYfileio>=0.1,<0.3` | GPL-3.0-or-later | Runtime dependency; separately distributed |
| Numba | `numba>=0.59` | BSD | Optional accelerator; not bundled |
| pypardiso | `pypardiso>=0.4` | BSD-3-Clause | Optional accelerator; not bundled |
| mpmath | `mpmath==1.3.0` | BSD-3-Clause | Development/research dependency; not bundled |
| pytest | `pytest>=8` | MIT | Development dependency; not bundled |
| build | `build>=1.2` | MIT | Development dependency; not bundled |
| Twine | `twine>=5` | Apache-2.0 | Development dependency; not bundled |

For complete licence texts and bundled-component notices, consult the exact
dependency distribution installed in the target environment. The GPL-licensed
ANY dependencies are explicitly reviewed transitional dependencies; their
presence is not an assertion that they have adopted MPL-2.0.
