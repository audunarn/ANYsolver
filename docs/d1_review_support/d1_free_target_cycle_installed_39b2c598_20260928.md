# Installed deformable-target cycle — development check

The source at `39b2c598f003d1da4e65a60b72a412708edb2db2` built
`anysolver-0.4.7-py3-none-any.whl` with SHA-256
`187ebdc40adf6165fb39a4f78d8a481b31ceec1eae02b2f1dbab9e0ba513fcf8`.
It was installed with `--no-deps --no-cache-dir` into the isolated
`reports/install-free-target-39b2c598` directory. Build and install logs are
`reports/general_contact_d1_free_target_wheel_{build,install}_20260928.txt`.

The example `examples/general_contact_free_target_cycle_dev.py` ran once with
the checkout module and once with `PYTHONPATH` pointing to the isolated install.
The installed report resolves `anysolver.__file__` inside that target. All
mechanical JSON fields match the local run exactly after excluding that module
path. The [local](d1_free_target_cycle_local_39b2c598_20260928.json) and
[installed](d1_free_target_cycle_installed_39b2c598_20260928.json) reports
contain eight accepted steps, zero contact force at opening, positive force at
recontact, a restart checkpoint, a minimum represented gap of −2.3331 µm and
a maximum complementarity relative force of 3.63e−13. The example checks
equal-and-opposite pair forces/moments and its declared dimensional gap gate.

The example source and model-building helper remain in the source checkout;
the `anysolver` mechanics module was loaded from the installed wheel. This is
an installed development check, not independent D1 acceptance, final package
qualification or application integration.
