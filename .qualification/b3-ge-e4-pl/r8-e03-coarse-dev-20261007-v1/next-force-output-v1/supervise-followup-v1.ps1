param([ValidateSet('controls','analytic','finalize-analytic','external','finalize-external')][string]$Mode,
 [string]$Attempt,[string]$PhaseAttempt='none',[double]$Cap=10,[double]$Reserve=60)
$ErrorActionPreference='Stop'
$raw=$PSScriptRoot
$authorityFile='authority-followup-v1.json'
$authority=Get-Content -LiteralPath (Join-Path $raw $authorityFile) -Raw|ConvertFrom-Json
if($authority.status -ne 'APPROVED' -or -not $authority.approval_evidence){throw 'PENDING_USER_APPROVAL: all launches refused'}
$lock=[IO.File]::Open((Join-Path $raw 'launch-lock-followup-v1'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
try {
$ledger=Get-Content -LiteralPath (Join-Path $raw 'ledger-followup-v1.json') -Raw|ConvertFrom-Json
$manifest=Get-Content -LiteralPath (Join-Path $raw 'inputs-manifest-followup-v1.json') -Raw|ConvertFrom-Json
$manifestHash=(Get-FileHash -LiteralPath (Join-Path $raw 'inputs-manifest-followup-v1.json') -Algorithm SHA256).Hash.ToLower()
if($authority.total_seconds -ne 150 -or $authority.reserve_seconds -ne 60 -or $ledger.total_seconds -ne 150 -or $ledger.status -ne 'APPROVED' -or $authority.allowed_modes -notcontains $Mode){throw 'Fresh150 authority/ledger mismatch'}
if($null -eq $ledger.used_seconds -or $null -eq $ledger.remaining_seconds -or -not [double]::IsFinite([double]$ledger.used_seconds) -or [double]$ledger.used_seconds -lt 0 -or [double]$ledger.remaining_seconds -ne (150-[double]$ledger.used_seconds)){throw 'Unknown/inconsistent remaining authority'}
if(@($ledger.attempts|Where-Object{$_.receipt.status -ne 'completed' -or $_.receipt.exit_code -ne 0}).Count){throw 'Stop on first failure; no retries'}
if($Attempt -notmatch '^[a-z][a-z0-9-]{0,63}$' -or $PhaseAttempt -notmatch '^[a-z][a-z0-9-]{0,63}$' -or $Cap -le 0 -or $Reserve -ne 60){throw 'Exact attempt/bound/reserve60 required'}
$modeCap=switch($Mode){'controls'{20};'analytic'{20};'external'{30};default{10}}
if($Cap -gt $modeCap){throw 'Mode cap exceeded'}
if($Mode -eq 'controls'){
 $used=0.0;foreach($old in @($ledger.attempts|Where-Object{$_.receipt.mode -eq 'controls'})){$used+=[double]$old.receipt.process_wall_seconds}
 $Cap=[Math]::Min($Cap,20-$used)
} elseif($Mode -like 'finalize-*'){
 $used=0.0;foreach($old in @($ledger.attempts|Where-Object{$_.receipt.mode -like 'finalize-*'})){$used+=[double]$old.receipt.process_wall_seconds}
 $Cap=[Math]::Min($Cap,20-$used)
}
function SuccessfulAttempt([string]$wanted){
 $matches=@($ledger.attempts|Where-Object{$_.receipt.mode -eq $wanted -and $_.receipt.input_manifest_sha256 -eq $manifestHash})
 if($matches.Count -ne 1 -or $matches[0].receipt.status -ne 'completed' -or $matches[0].receipt.exit_code -ne 0 -or -not $matches[0].receipt.owned_child_exited){throw ('Exact completed '+$wanted+' required')}
 return $matches[0]
}
if($Mode -ne 'controls'){
 $control=SuccessfulAttempt 'controls'
 [xml]$junit=Get-Content -LiteralPath (Join-Path $control.path 'junit.xml') -Raw
 if([int]$junit.testsuites.testsuite.tests -ne $manifest.source_controls_expected -or [int]$junit.testsuites.testsuite.failures -ne 0 -or [int]$junit.testsuites.testsuite.errors -ne 0 -or [int]$junit.testsuites.testsuite.skipped -ne 0){throw 'Every frozen control must pass'}
}
if($Mode -like 'finalize-*'){
 $physical=SuccessfulAttempt ($Mode.Substring(9))
 if($physical.path -ne (Join-Path $raw $PhaseAttempt)){throw 'Exact prior physical attempt required'}
 if(@($ledger.attempts|Where-Object{$_.receipt.mode -eq $Mode}).Count){throw 'One finalization per phase; no retry'}
}
if($Mode -in @('external','finalize-external')){
 $analytic=SuccessfulAttempt 'finalize-analytic'
 if($analytic.path -ne (Join-Path $raw $authority.analytic_finalization_attempt)){throw 'Declared analytic finalization path required'}
 $result=Get-Content -LiteralPath (Join-Path $analytic.path 'finalization.json') -Raw|ConvertFrom-Json
 if($result.status -ne 'ANALYTIC_SEMANTICS_REVIEW_CANDIDATE' -or $result.semantics_adopted -ne $false){throw 'Actual independent analytic oracle required'}
 $confirmation=Get-Content -LiteralPath (Join-Path $raw 'semantics-confirmation-v1.json') -Raw|ConvertFrom-Json
 $bindings=Get-Content -LiteralPath (Join-Path $analytic.path 'analytic-bindings.json') -Raw|ConvertFrom-Json
 if($confirmation.status -ne 'CONFIRMED_BY_INDEPENDENT_REVIEW' -or $confirmation.runtime_binary_correspondence -ne 'INDEPENDENTLY_CONFIRMED' -or $confirmation.control_evidence_sha256 -ne $bindings.candidate_sha256 -or $bindings.candidate_sha256 -ne (Get-FileHash -LiteralPath (Join-Path $analytic.path 'finalization.json') -Algorithm SHA256).Hash.ToLower()){throw 'Root-adopted actual analytic semantics record required'}
}
if($Mode -in @('analytic','external') -and $ledger.($Mode+'_primary') -ne 'UNCONSUMED'){throw 'Fresh physical primary already consumed'}
$limit=[Math]::Min($Cap,[double]$ledger.remaining_seconds-$Reserve)
if($limit -le 0){throw 'No authorized time after reserve'}
# Remaining process-start/accounting block is copied from the existing supervisor.
$folder=Join-Path $raw $Attempt
if(Test-Path -LiteralPath $folder){throw 'Attempt already exists'}
[void](New-Item -ItemType Directory -Path $folder)
$process=[System.Diagnostics.Process]::new()
$process.StartInfo.FileName='C:/Python/Python314/python.exe'
foreach($arg in @('-I','-B','-X',('pycache_prefix='+(Join-Path $folder 'pycache')),(Join-Path $raw 'entry-followup-v1.py'),$Mode,$Attempt)){$process.StartInfo.ArgumentList.Add($arg)}
$process.StartInfo.ArgumentList.Add($PhaseAttempt)
$process.StartInfo.WorkingDirectory=$raw
$process.StartInfo.UseShellExecute=$false;$process.StartInfo.CreateNoWindow=$true
$process.StartInfo.RedirectStandardOutput=$true;$process.StartInfo.RedirectStandardError=$true
foreach($key in @($process.StartInfo.Environment.Keys|Where-Object{$_ -like 'CCX_NPROC_*'})){[void]$process.StartInfo.Environment.Remove($key)}
foreach($key in @('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS','NUMBA_NUM_THREADS','NUMBER_OF_CPUS','CCX_NPROC_CFD','CCX_NPROC_RESULTS')){$process.StartInfo.Environment[$key]='1'}
$process.StartInfo.Environment['NUMBA_DISABLE_JIT']='1'
$process.StartInfo.Environment['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
$process.StartInfo.Environment['PIP_NO_INDEX']='1'
[void]$process.StartInfo.Environment.Remove('OPENBLAS_CORETYPE')
$bindings=[ordered]@{
    supervisor_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $PSCommandPath).Hash.ToLower()
    entry_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw 'entry-followup-v1.py')).Hash.ToLower()
    input_manifest_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw 'inputs-manifest-followup-v1.json')).Hash.ToLower()
    authority_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw $authorityFile)).Hash.ToLower()
}
$clock=[System.Diagnostics.Stopwatch]::new()
$started=$false; $timedOut=$false; $childExited=$false
$primary=$null; $cleanup=$null; $out=$null; $err=$null; $exitCode=$null
# Root-owned ledger is consumed durably BEFORE attempting the one-use launch.
if($Mode -in @('analytic','external')){
    $ledger.($Mode+'_primary')='CONSUMED_BEFORE_LAUNCH'
    $ledgerPath=Join-Path $raw 'ledger-followup-v1.json'
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
    # A dead Python parent is not proof that its owned CCX descendants exited.
    try {
        $registryPath=Join-Path $folder 'owned-processes.json'
        if($Mode -in @('analytic','external') -and -not (Test-Path -LiteralPath $registryPath)){throw 'Physical descendant registry missing; cleanup cannot be proven'}
        if(Test-Path -LiteralPath $registryPath){
            $ownedRows=@(Get-Content -LiteralPath $registryPath -Raw|ConvertFrom-Json)
            if($ownedRows.Count -gt 64){throw 'Owned descendant registry exceeds bound'}
            foreach($ownedRow in $ownedRows){
                $ownedProcess=Get-Process -Id ([int]$ownedRow.pid) -ErrorAction SilentlyContinue
                if($null -eq $ownedProcess){continue}
                $actualCreated=([DateTimeOffset]$ownedProcess.StartTime.ToUniversalTime()).ToUnixTimeMilliseconds()/1000.0
                # psutil's Windows timestamp is compared at native millisecond resolution.
                if([Math]::Abs($actualCreated-[double]$ownedRow.creation_time) -ge .001){throw 'PID creation identity mismatch; foreign process will not be killed'}
                if(-not $ownedProcess.HasExited){$ownedProcess.Kill($true)}
                if(-not $ownedProcess.WaitForExit(2000)){throw 'Owned descendant remains alive'}
            }
        }
    } catch { $cleanup=$_ }
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
        $ledger.remaining_seconds=$receipt.remaining_seconds
        $ledger.attempts+=([pscustomobject]@{path=$folder;receipt=$receipt})
        if($null -ne $cleanup){$ledger.status='ACCOUNTING_OR_CLEANUP_UNCERTAIN'}
        $ledgerPath=Join-Path $raw 'ledger-followup-v1.json'
        [IO.File]::WriteAllText(($ledgerPath+'.part'),($ledger|ConvertTo-Json -Depth 30))
        Move-Item -LiteralPath ($ledgerPath+'.part') -Destination $ledgerPath -Force
    } catch { throw ('Accounting persistence failed; no remainder may be assumed. Primary: '+$primary+'; cleanup: '+$cleanup+'; persistence: '+$_) }
    $receipt|ConvertTo-Json -Depth 8 -Compress
}
if($null -ne $primary){throw $primary}
if($null -ne $cleanup){throw $cleanup}
if($exitCode -ne 0 -or $timedOut){exit 1}

} finally { $lock.Dispose() }
