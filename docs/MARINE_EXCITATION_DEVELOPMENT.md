# Native prescribed excitation series (development)

`PotentialFlowDevelopmentData.with_excitation_series(series,
development_only=True)` consumes an exact public ANYhydro ExcitationSeries.
Install the optional `marine-excitation` extra to use this conversion. Legacy
base imports/records need no ANYhydro dependency.

The conversion explicitly replaces the legacy harmonic amplitudes/frequency.
Construction refuses simultaneous nonzero legacy forcing, mismatched full
body-qualified DOF order, non-GLOBAL coefficient axes or source status other
than development_fixture. No source status is upgraded. The series retains
materialized phase/amplitude weights, source/wave hashes and full force axes.
Forces are evaluated at the authoritative trial time and pass through the
existing equilibrium-coordinate work-conjugate force pullback. Radiation memory,
infinite-frequency inertia, incremental restoring, geometric forces and accepted
history ownership retain their existing definitions.

```python
from anyhydro import build_excitation_series, UNIT_INCIDENT_AMPLITUDE
series = build_excitation_series(
    fixture_dataset, waves, amplitude_normalization=UNIT_INCIDENT_AMPLITUDE,
    phase_origin_xy=(0., 0.))
data = data.with_excitation_series(series, development_only=True)
environment = waves.environment(water_depth=20.)  # same saved components
```

`data_to_dict` omits an absent optional field, preserving legacy records/hashes.
An included series is strict data-only and immutable after reconstruction.
Diagnostics retain excitation series, source and wave hashes. Native developer
tests use analytic phasors/discrete Newmark recurrence and a three-step two-body
coupled fixture with Morison drag correction from the same saved realization.
No BEM solve is executed by these tests.

The caller must match source reference points, geometry, water depth, gravity
and phase origin. This conversion does not establish physical source/environment
binding, backend unit normalization, diffraction or large-excursion qualification.
Existing BEM source-admission and scientific W3/W4 gates remain required. The
optional series field is currently a public headless Solver development capability;
ANYmarine's Qt project editor does not yet admit this declaration. Full application
workflow, mooring lines/contact and W8-W10 acceptance remain pending.
