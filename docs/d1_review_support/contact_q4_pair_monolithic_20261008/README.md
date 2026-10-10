# Reproduce the opt-in Q4/Q4 monolithic example

With the current package installed, from the repository:

```powershell
python examples/general_contact_q4_pair_monolithic.py
```

The example uses the existing ordinary force API with default structural options and explicit tolerance1e-12. It selects augmented contact plus monolithic_active_set, original Q4 Jet2 geometry, exact fine-Q1 support and whole-face guards. The default historical contact routes are unchanged.

See OUTCOME.md for checks, proof scope, failed evidence and the next strict-opening obstruction. Captured development stages are build, unit, full, alternate-c, prefix, resume, safety, safety-corrective, safety-fields, legacy-monolithic, legacy-penalty and example. Existing paths are immutable; reproduction requires new unique evidence paths and its own execution authority.
