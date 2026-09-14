# B3-GE production opt-in

`B3-GE` is the public name of the accepted model-owned geometrically exact
Simo--Reissner beam workflow. Select it explicitly with `b3-ge`:

```python
from anysolver import b3_ge

# definition = b3_ge.define_beam(b3_ge.SELECTOR, ...)
# analysis = b3_ge.create_analysis(b3_ge.SELECTOR, (definition,), boundaries)
```

Legacy B3 remains the default for `b3`, `beam3`, `quadratic_beam`, inferred
three-node topology, and every record without explicit B3-GE authority. The
older `ge-beam3` element facade is a separate historical formulation and is
not redirected. A B3-GE request that is incomplete or outside the admitted
native workflow fails; it never falls back to legacy B3.

The production admission binds the immutable native workflow profile and the
accepted G6 full applicable legacy-domain parity record. It does not expand
that accepted scope. Finite-velocity rotational dynamics, gyroscopic terms,
generic FEModel insertion, arbitrary section laws, plastic/fibre shell
coupling, and stable postbuckling are not claimed.
