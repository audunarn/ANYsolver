param([ValidateSet('prefix')][string]$Mode,
      [string]$Attempt,[double]$Cap=90,[double]$Reserve=60)
$ErrorActionPreference='Stop'
$raw=$PSScriptRoot
$authority=Get-Content -LiteralPath (Join-Path $raw 'authority.json') -Raw|ConvertFrom-Json
if($authority.status -ne 'APPROVED' -or -not $authority.approval_evidence){throw 'PENDING_USER_APPROVAL: interpreter launch refused'}
$ledger=Get-Content -LiteralPath (Join-Path $raw 'ledger.json') -Raw|ConvertFrom-Json
if($ledger.status -ne 'APPROVED' -or $authority.total_seconds -ne 600 -or $ledger.total_seconds -ne 600){throw 'Fresh verification authority/ledger mismatch'}
if($Attempt -notmatch '^[a-z][a-z0-9-]{0,63}$' -or $Cap -le 0 -or $Reserve -lt 0 -or $ledger.used_seconds -lt 0){throw 'Invalid execution bound/attempt'}
$limit=[Math]::Min($Cap,[double]$ledger.total_seconds-[double]$ledger.used_seconds-$Reserve)
if($limit -le 0){throw 'No authorised time after reserve'}
$folder=Join-Path $raw $Attempt
if(Test-Path -LiteralPath $folder){throw 'Attempt already exists'}
[void](New-Item -ItemType Directory -Path $folder)
$process=[System.Diagnostics.Process]::new()
$process.StartInfo.FileName='C:/Python/Python314/python.exe'
foreach($arg in @('-I','-B','-X',('pycache_prefix='+(Join-Path $folder 'pycache')),(Join-Path $raw 'entry-v2.py'),$Mode,$Attempt)){$process.StartInfo.ArgumentList.Add($arg)}
$process.StartInfo.WorkingDirectory=$raw
$process.StartInfo.UseShellExecute=$false;$process.StartInfo.CreateNoWindow=$true
$process.StartInfo.RedirectStandardOutput=$true;$process.StartInfo.RedirectStandardError=$true
foreach($key in @('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS','NUMBA_NUM_THREADS')){$process.StartInfo.Environment[$key]='1'}
$process.StartInfo.Environment['NUMBA_DISABLE_JIT']='1'
$process.StartInfo.Environment['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
$process.StartInfo.Environment['PIP_NO_INDEX']='1'
[void]$process.StartInfo.Environment.Remove('OPENBLAS_CORETYPE')
$clock=[System.Diagnostics.Stopwatch]::StartNew()
[void]$process.Start();$process.ProcessorAffinity=[IntPtr]1
$out=$process.StandardOutput.ReadToEndAsync();$err=$process.StandardError.ReadToEndAsync()
$timedOut=-not $process.WaitForExit([int]($limit*1000))
if($timedOut){$process.Kill($true);$process.WaitForExit()}
$clock.Stop();$elapsed=$clock.Elapsed.TotalSeconds
[System.IO.File]::WriteAllText((Join-Path $folder 'stdout.log'),$out.GetAwaiter().GetResult())
[System.IO.File]::WriteAllText((Join-Path $folder 'stderr.log'),$err.GetAwaiter().GetResult())
$receipt=[ordered]@{command=@($process.StartInfo.FileName)+@($process.StartInfo.ArgumentList);cwd=$raw;mode=$Mode;status=$(if($timedOut){'timeout'}elseif($process.ExitCode -ne 0){'failed'}else{'completed'});exit_code=$process.ExitCode;process_wall_seconds=$elapsed;seconds_limit=$limit;cumulative_used_seconds=([double]$ledger.used_seconds+$elapsed);remaining_seconds=([double]$ledger.total_seconds-[double]$ledger.used_seconds-$elapsed);supervisor_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $PSCommandPath).Hash.ToLower();entry_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw 'entry-v2.py')).Hash.ToLower();input_manifest_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw 'inputs-manifest-v2.json')).Hash.ToLower();authority_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw 'authority.json')).Hash.ToLower();tree_memory='entry psutil samples process tree at20ms/2GiB; timeout kills process tree'}
[System.IO.File]::WriteAllText((Join-Path $folder 'execution.json'),($receipt|ConvertTo-Json -Depth 8))
$ledger.used_seconds=$receipt.cumulative_used_seconds;$ledger.attempts+=([pscustomobject]@{path=$folder;receipt=$receipt})
[System.IO.File]::WriteAllText((Join-Path $raw 'ledger.json'),($ledger|ConvertTo-Json -Depth 30))
$receipt|ConvertTo-Json -Depth 8 -Compress
if($process.ExitCode -ne 0 -or $timedOut){exit 1}