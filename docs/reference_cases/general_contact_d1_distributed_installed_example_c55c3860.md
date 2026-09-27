# Distributed Q4/S3 cycle: installed development example

From source commit `c55c3860`, an offline no-isolation wheel was built and
installed without dependencies into an isolated target. Wheel:
`C:/ANYworkspaceWork/general-contact-evidence/wheel-c55c3860-20260927/anysolver-0.4.7-py3-none-any.whl`,
SHA256 `dcade18155bd1e5f1e2b98b6869711c07f7ba06435877f75a13a05062f304c81`.
The example used `PYTHONPATH` set only to the isolated install target and
ran as:

```text
python -m examples.general_contact_distributed_q4_s3_cycle --columns 8 --output C:/ANYworkspaceWork/general-contact-evidence/distributed-cycle-8q4-installed-c55c3860.json
```

The output's `anysolver_module` resolves inside that target. Its tracked
[raw report](../../reports/general_contact_d1_distributed_cycle_8q4_installed_c55c3860_20260927.json)
has SHA256 `8998c7802cad60be7647987203730c4f6d039e1ae5e40da2d28f862f6e94a4bf`.
All twelve steps completed with a checkpoint, loaded normal force
0.10347981515520803 N, first-unload force 0.03980671281149368 N,
zero open force at steps 8–10 and recontact. Worst independent gap was
−0.0804 µm within 50 µm. Force, gap, pressure-change and active-count
histories match the earlier eight-Q4 source development report exactly.

This verifies the installed route for the eight-Q4 demonstration. The
independently reviewed 24-Q4 response and the installed eight-Q4 example
are distinct evidence. This does not establish installed 24-Q4 response,
complete C1, application integration or release.
