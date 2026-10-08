param([string]$Attempt='saved-chain-inspection-v1',[double]$Cap=15,[double]$Reserve=60)
$ErrorActionPreference='Stop'
$raw=$PSScriptRoot
$authority=Get-Content -LiteralPath (Join-Path $raw 'authority-v5.json') -Raw|ConvertFrom-Json
$ledger=Get-Content -LiteralPath (Join-Path $raw 'ledger-v5.json') -Raw|ConvertFrom-Json
if($authority.status -ne 'APPROVED' -or $ledger.status -ne 'APPROVED' -or $ledger.total_seconds -ne 150 -or $Cap -le 0 -or $Cap -gt 15 -or $Reserve -lt 60){throw 'Inspection authority/bound mismatch'}
if($Attempt -notmatch '^[a-z][a-z0-9-]{0,63}$'){throw 'Invalid inspection attempt'}
$limit=[Math]::Min($Cap,150-[double]$ledger.used_seconds-$Reserve)
if($limit -le 0){throw 'No verification remainder after reserve'}
$folder=Join-Path $raw $Attempt
if(Test-Path -LiteralPath $folder){throw 'Inspection attempt already exists'}
[void](New-Item -ItemType Directory -Path $folder)
$process=[Diagnostics.Process]::new()
$process.StartInfo.FileName='C:/Python/Python314/python.exe'
foreach($arg in @('-I','-B','-X',('pycache_prefix='+(Join-Path $folder 'pycache')),(Join-Path $raw 'inspect-saved-q4-chain-v1.py'),$Attempt)){$process.StartInfo.ArgumentList.Add($arg)}
$process.StartInfo.UseShellExecute=$false
$process.StartInfo.CreateNoWindow=$true
$process.StartInfo.RedirectStandardOutput=$true
$process.StartInfo.RedirectStandardError=$true
foreach($key in @('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS','NUMBA_NUM_THREADS')){$process.StartInfo.Environment[$key]='1'}
$process.StartInfo.Environment['NUMBA_DISABLE_JIT']='1'
[void]$process.StartInfo.Environment.Remove('OPENBLAS_CORETYPE')
$clock=[Diagnostics.Stopwatch]::new();$started=$false;$timeout=$false;$out=$null;$err=$null;$exited=$false;$primary=$null
try{
    $clock.Start();$started=$process.Start();if(-not $started){throw 'Inspection launch failed'}
    $out=$process.StandardOutput.ReadToEndAsync();$err=$process.StandardError.ReadToEndAsync()
    if(-not $process.WaitForExit([int]($limit*1000))){$timeout=$true;$process.Kill($true)}
}catch{$primary=$_}finally{
    if($started -and -not $process.HasExited){$process.Kill($true)}
    if($started){$exited=$process.WaitForExit(10000)}
    $clock.Stop();$elapsed=if($started){$clock.Elapsed.TotalSeconds}else{0.}
    if(-not $exited -and $started){throw 'Inspection cleanup uncertain; no authority remainder may be assumed'}
    foreach($pair in @(@('stdout.log',$out),@('stderr.log',$err))){if($null -ne $pair[1]){if(-not $pair[1].Wait(5000)){throw 'Inspection stream incomplete'};[IO.File]::WriteAllText((Join-Path $folder $pair[0]),$pair[1].GetAwaiter().GetResult())}}
    $exit=if($exited){$process.ExitCode}else{$null}
    $receipt=[ordered]@{mode='saved_record_inspection';scope='Approved v5 verification remainder; arithmetic on fixed captures only; zero evaluator calls'
        command=@($process.StartInfo.FileName)+@($process.StartInfo.ArgumentList)
        status=$(if($primary){'supervisor_failure'}elseif($timeout){'timeout'}elseif($exit -ne 0){'failed'}else{'completed'})
        exit_code=$exit;owned_child_exited=$exited;process_wall_seconds=$elapsed;seconds_limit=$limit
        cumulative_used_seconds=([double]$ledger.used_seconds+$elapsed);remaining_seconds=150-[double]$ledger.used_seconds-$elapsed
        inspector_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw 'inspect-saved-q4-chain-v1.py')).Hash.ToLower()
        supervisor_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $PSCommandPath).Hash.ToLower()
        authority_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw 'authority-v5.json')).Hash.ToLower()}
    [IO.File]::WriteAllText((Join-Path $folder 'execution.json'),($receipt|ConvertTo-Json -Depth 8))
    $ledger.used_seconds=$receipt.cumulative_used_seconds
    $ledger.attempts+=([pscustomobject]@{path=$folder;receipt=$receipt})
    [IO.File]::WriteAllText((Join-Path $raw 'ledger-v5.json.part'),($ledger|ConvertTo-Json -Depth 30))
    Move-Item -LiteralPath (Join-Path $raw 'ledger-v5.json.part') -Destination (Join-Path $raw 'ledger-v5.json') -Force
    $receipt|ConvertTo-Json -Depth 8 -Compress
}
if($primary){throw $primary}
if($timeout -or $exit -ne 0){exit 1}