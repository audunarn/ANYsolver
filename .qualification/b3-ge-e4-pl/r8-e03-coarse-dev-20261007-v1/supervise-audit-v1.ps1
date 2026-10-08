param([ValidateSet('controls')][string]$Mode,
      [string]$Attempt,[string]$PhaseAttempt='none',[double]$Cap=30,[double]$Reserve=60)
$ErrorActionPreference='Stop'
$raw=$PSScriptRoot
$authorityFile='authority-v1.json'
$authority=Get-Content -LiteralPath (Join-Path $raw $authorityFile) -Raw|ConvertFrom-Json
if($authority.status -ne 'APPROVED' -or -not $authority.approval_evidence){throw 'PENDING_USER_APPROVAL: interpreter launch refused'}
$ledger=Get-Content -LiteralPath (Join-Path $raw 'ledger-v1.json') -Raw|ConvertFrom-Json
if($ledger.status -ne 'APPROVED' -or $authority.total_seconds -ne 240 -or $ledger.total_seconds -ne 240 -or $authority.allowed_modes -notcontains $Mode){throw 'Cumulative authority/ledger mismatch'}
$manifest=Get-Content -LiteralPath (Join-Path $raw 'inputs-manifest-audit-v1.json') -Raw|ConvertFrom-Json
$manifestHash=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw 'inputs-manifest-audit-v1.json')).Hash.ToLower()
if($Mode -ne 'controls'){
    $eligible=@($ledger.attempts|Where-Object{$_.receipt.mode -eq 'controls' -and $_.receipt.input_manifest_sha256 -eq $manifestHash})
    if($eligible.Count -eq 0){throw 'Matching controls PASS required first'}
    $last=$eligible[-1]
    if($last.receipt.status -ne 'completed' -or $last.receipt.exit_code -ne 0 -or -not $last.receipt.owned_child_exited){throw 'Latest matching controls failed/incomplete'}
    [xml]$junit=Get-Content -LiteralPath (Join-Path $last.path 'junit.xml') -Raw
    if([int]$junit.testsuites.testsuite.tests -ne $manifest.source_controls_expected -or [int]$junit.testsuites.testsuite.failures -ne 0 -or [int]$junit.testsuites.testsuite.errors -ne 0 -or [int]$junit.testsuites.testsuite.skipped -ne 0){throw 'All prepared controls must pass'}
}
if($Attempt -notmatch '^[a-z][a-z0-9-]{0,63}$' -or $PhaseAttempt -notmatch '^[a-z][a-z0-9-]{0,63}$' -or $Cap -le 0 -or $Reserve -lt 0 -or $ledger.used_seconds -lt 0){throw 'Invalid execution bound/attempt'}
if($Mode -ne 'finalize-external' -and $Reserve -lt 60){throw 'Protected final reserve60 required'}
$modeCap=if($Mode -in @('native','external')){60}else{30}
if($Cap -gt $modeCap){throw 'Mode cap exceeded'}
if($Mode -eq 'controls'){
    $controlsUsed=0.0
    foreach($old in @($ledger.attempts|Where-Object{$_.receipt.mode -eq 'controls'})){$controlsUsed+=[double]$old.receipt.process_wall_seconds}
    $Cap=[Math]::Min($Cap,[double]$authority.controls_budget_seconds-$controlsUsed)
}
if($Mode -in @('external','finalize-external')){
    $prior=@($ledger.attempts|Where-Object{$_.receipt.mode -eq 'finalize-native' -and $_.receipt.input_manifest_sha256 -eq $manifestHash})
    if($prior.Count -eq 0){throw 'Finalized matching native phase required'}
    $native=$prior[-1]
    if($native.receipt.status -ne 'completed' -or $native.receipt.exit_code -ne 0 -or -not $native.receipt.owned_child_exited){throw 'Native finalization failed'}
    $outcome=Get-Content -LiteralPath (Join-Path $native.path 'finalization.json') -Raw|ConvertFrom-Json
    if($outcome.phase -ne 'native' -or $outcome.status -ne 'PROVISIONAL_COARSE_PHASE_COMPLETED'){throw 'Native provisional completion required'}
}
if($Mode -like 'finalize-*'){
    $physicalMode=$Mode.Substring(9)
    $physical=@($ledger.attempts|Where-Object{$_.path -eq (Join-Path $raw $PhaseAttempt) -and $_.receipt.mode -eq $physicalMode})
    if($physical.Count -ne 1 -or -not $physical[0].receipt.owned_child_exited){throw 'Exact exited physical attempt required before finalization'}
}
if($Mode -in @('native','external') -and $ledger.($Mode+'_primary') -ne 'UNCONSUMED'){throw 'Physical primary already consumed; no retry'}
$limit=[Math]::Min($Cap,[double]$ledger.total_seconds-[double]$ledger.used_seconds-$Reserve)
if($limit -le 0){throw 'No authorised time after reserve'}
$folder=Join-Path $raw $Attempt
if(Test-Path -LiteralPath $folder){throw 'Attempt already exists'}
[void](New-Item -ItemType Directory -Path $folder)
$process=[System.Diagnostics.Process]::new()
$process.StartInfo.FileName='C:/Python/Python314/python.exe'
foreach($arg in @('-I','-B','-X',('pycache_prefix='+(Join-Path $folder 'pycache')),(Join-Path $raw 'entry-audit-v1.py'),$Mode,$Attempt)){$process.StartInfo.ArgumentList.Add($arg)}
$process.StartInfo.ArgumentList.Add($PhaseAttempt)
$process.StartInfo.WorkingDirectory=$raw
$process.StartInfo.UseShellExecute=$false;$process.StartInfo.CreateNoWindow=$true
$process.StartInfo.RedirectStandardOutput=$true;$process.StartInfo.RedirectStandardError=$true
foreach($key in @('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS','NUMBA_NUM_THREADS')){$process.StartInfo.Environment[$key]='1'}
$process.StartInfo.Environment['NUMBA_DISABLE_JIT']='1'
$process.StartInfo.Environment['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
$process.StartInfo.Environment['PIP_NO_INDEX']='1'
[void]$process.StartInfo.Environment.Remove('OPENBLAS_CORETYPE')
$bindings=[ordered]@{
    supervisor_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $PSCommandPath).Hash.ToLower()
    entry_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw 'entry-audit-v1.py')).Hash.ToLower()
    input_manifest_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw 'inputs-manifest-audit-v1.json')).Hash.ToLower()
    authority_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw $authorityFile)).Hash.ToLower()
}
$clock=[System.Diagnostics.Stopwatch]::new()
$started=$false; $timedOut=$false; $childExited=$false
$primary=$null; $cleanup=$null; $out=$null; $err=$null; $exitCode=$null
# Root-owned ledger is consumed durably BEFORE attempting the one-use launch.
if($Mode -in @('native','external')){
    $ledger.($Mode+'_primary')='CONSUMED_BEFORE_LAUNCH'
    $ledgerPath=Join-Path $raw 'ledger-v1.json'
    [IO.File]::WriteAllText(($ledgerPath+'.part'),($ledger|ConvertTo-Json -Depth 30))
    Move-Item -LiteralPath ($ledgerPath+'.part') -Destination $ledgerPath -Force
}
try {
    $clock.Start()
    $started=$process.Start()
    if(-not $started){throw 'Process start returned false'}
    $out=$process.StandardOutput.ReadToEndAsync()
    $err=$process.StandardError.ReadToEndAsync()
    $process.ProcessorAffinity=[IntPtr]1
    $waitMilliseconds=[Math]::Max(0,[Math]::Floor(($limit-$clock.Elapsed.TotalSeconds)*1000))
    $timedOut=-not $process.WaitForExit([int]$waitMilliseconds)
} catch { $primary=$_ }
finally {
    if($started){
        try {
            if(-not $process.HasExited){$process.Kill($true)}
            $childExited=$process.WaitForExit(5000)
            if(-not $childExited){throw 'Owned process did not exit after tree termination'}
            $exitCode=$process.ExitCode
        } catch { $cleanup=$_ }
    }
    $clock.Stop()
    $elapsed=$(if($started){$clock.Elapsed.TotalSeconds}else{0.0})
    foreach($stream in @(@('stdout.log',$out),@('stderr.log',$err))){
        try {
            if($null -ne $stream[1]){
                if(-not $stream[1].Wait(5000)){throw ('Stream drain did not complete: '+$stream[0])}
                [IO.File]::WriteAllText((Join-Path $folder $stream[0]),$stream[1].GetAwaiter().GetResult())
            }
        } catch {if($null -eq $cleanup){$cleanup=$_}}
    }
    $status=if($null -ne $cleanup){'cleanup_or_evidence_failure'}elseif($null -ne $primary){'supervisor_failure'}elseif($timedOut){'timeout'}elseif($exitCode -ne 0){'failed'}else{'completed'}
    $receipt=[ordered]@{
        command=@($process.StartInfo.FileName)+@($process.StartInfo.ArgumentList);cwd=$raw;mode=$Mode
        status=$status;started=$started;owned_child_exited=$childExited;exit_code=$exitCode
        primary_error=$(if($null -ne $primary){$primary.ToString()}else{$null})
        cleanup_error=$(if($null -ne $cleanup){$cleanup.ToString()}else{$null})
        process_wall_seconds=$elapsed;seconds_limit=$limit
        cumulative_used_seconds=([double]$ledger.used_seconds+$elapsed)
        remaining_seconds=$(if($null -ne $cleanup){$null}else{[double]$ledger.total_seconds-[double]$ledger.used_seconds-$elapsed})
        supervisor_sha256=$bindings.supervisor_sha256
        entry_sha256=$bindings.entry_sha256
        input_manifest_sha256=$bindings.input_manifest_sha256
        authority_sha256=$bindings.authority_sha256
        tree_memory='entry psutil samples process tree at20ms/2GiB; timeout kills owned process tree'
    }
    try {
        [IO.File]::WriteAllText((Join-Path $folder 'execution.json'),($receipt|ConvertTo-Json -Depth 8))
        $ledger.used_seconds=$receipt.cumulative_used_seconds
        $ledger.attempts+=([pscustomobject]@{path=$folder;receipt=$receipt})
        if($null -ne $cleanup){$ledger.status='ACCOUNTING_OR_CLEANUP_UNCERTAIN'}
        $ledgerPath=Join-Path $raw 'ledger-v1.json'
        [IO.File]::WriteAllText(($ledgerPath+'.part'),($ledger|ConvertTo-Json -Depth 30))
        Move-Item -LiteralPath ($ledgerPath+'.part') -Destination $ledgerPath -Force
    } catch { throw ('Accounting persistence failed; no remainder may be assumed. Primary: '+$primary+'; cleanup: '+$cleanup+'; persistence: '+$_) }
    $receipt|ConvertTo-Json -Depth 8 -Compress
}
if($null -ne $primary){throw $primary}
if($null -ne $cleanup){throw $cleanup}
if($exitCode -ne 0 -or $timedOut){exit 1}
