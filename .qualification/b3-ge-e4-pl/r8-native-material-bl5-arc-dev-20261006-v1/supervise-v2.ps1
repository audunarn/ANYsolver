param([string]$Mode,[string]$Attempt,[double]$Cap=90,[double]$Reserve=60)
$ErrorActionPreference='Stop'
$raw=$PSScriptRoot
$ledger=Get-Content -LiteralPath (Join-Path $raw 'ledger.json') -Raw | ConvertFrom-Json
$limit=[Math]::Min($Cap,[double]$ledger.total_seconds-[double]$ledger.used_seconds-$Reserve)
if($limit -le 0){throw 'No authorized allowance after reserve'}
$folder=Join-Path $raw $Attempt
if(Test-Path -LiteralPath $folder){throw 'Attempt already exists'}
[void](New-Item -ItemType Directory -Path $folder)
$process=[System.Diagnostics.Process]::new()
$process.StartInfo.FileName='C:/Python/Python314/python.exe'
foreach($arg in @('-I',(Join-Path $raw 'entry-v2.py'),$Mode,$Attempt)){$process.StartInfo.ArgumentList.Add($arg)}
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
$receipt=[ordered]@{command=@('C:/Python/Python314/python.exe','-I',(Join-Path $raw 'entry-v2.py'),$Mode,$Attempt);cwd=$raw;status=$(if($timedOut){'timeout'}elseif($process.ExitCode -ne 0){'failed'}else{'completed'});exit_code=$process.ExitCode;process_wall_seconds=$elapsed;seconds_limit=$limit;cumulative_used_seconds=([double]$ledger.used_seconds+$elapsed);remaining_seconds=([double]$ledger.total_seconds-[double]$ledger.used_seconds-$elapsed);supervisor_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $PSCommandPath).Hash.ToLower();entry_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw 'entry-v2.py')).Hash.ToLower();tree_memory='entry psutil sampled entire process tree, 2GiB ceiling; native timeout kills entire tree'}
[System.IO.File]::WriteAllText((Join-Path $folder 'execution.json'),($receipt|ConvertTo-Json -Depth 8))
$ledger.used_seconds=$receipt.cumulative_used_seconds;$ledger.attempts+=([pscustomobject]@{path=$folder;receipt=$receipt})
[System.IO.File]::WriteAllText((Join-Path $raw 'ledger.json'),($ledger|ConvertTo-Json -Depth 30))
$receipt|ConvertTo-Json -Depth 8 -Compress

