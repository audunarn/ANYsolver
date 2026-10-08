# Development checks and dispositions

Observed root-owned portable source checks:
- Initial framing22PASS,0.29s.
- Added comparison control:22PASS/1FAIL,0.50s. The wrapper returned a third
  Decimal field, while the new comparison unpacked two fields. Fixed unpack;
  no scientific run/result affected. failed-tests-v1 retains runtime/selection.
- Corrected focused23PASS,0.46s.
- Final affected comparison + existing feasibility suite37PASS,1.38s,
  portable-ci-lkno51h_/P01. Exact runtime/selection/resource records retained
  in checks-final-v1. This paragraph records observed terminal summaries;
  the portable runner did not save pytest stdout to those three JSON records.
- Supporting reviewer found DAT section-order coupling; now keyed selection,
  reversed order, valid binary/printed agreement and out-of-bound controls pass.

Failed startup and parse attempts remain:
- startup-v1-failed.json: logical LF deck hash versus CRLF saved-byte hash;
  no CCX child launched. binding-v2 binds actual bytes and preserves logical hash.
- parse-execution-v1: wrong repository parent prevented module import;
  original parse-v1/run-parse-v1 and stderr retained. Corrected v2 completes.

The final checks cover script evidence readers, not product numerical changes.
No solver wheel changed or installed regression campaign repeated for this slice.
Solver34f0a513's installed material checks/artifacts retain their original scope.
No qualification criterion, tolerance, authority or historical evidence changed.
