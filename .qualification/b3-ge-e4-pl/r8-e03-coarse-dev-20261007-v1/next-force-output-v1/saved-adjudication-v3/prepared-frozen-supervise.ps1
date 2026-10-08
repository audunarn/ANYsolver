param([Parameter(Mandatory)][ValidateSet('analytic-adjudication','external','external-adjudication')][string]$Mode)
$ErrorActionPreference='Stop'
$TaskRoot=$PSScriptRoot
$Lease=[IO.FileStream]::new("$TaskRoot/launch.lock",[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
trap { if($null -ne $Lease) { $Lease.Dispose() }; throw }
function Read-Json($Path) { $Stream=[IO.FileStream]::new($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete); $Reader=[IO.StreamReader]::new($Stream); try { $Reader.ReadToEnd() | ConvertFrom-Json -AsHashtable } finally { $Reader.Dispose() } }
function Hash($Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Save-Json($Path,$Value) { $Part="$Path.$([Guid]::NewGuid().ToString('N')).part"; $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Part -Encoding utf8NoBOM; for($Index=0;$Index -lt 8;$Index++) { try { Move-Item -LiteralPath $Part -Destination $Path -Force; return } catch { if($Index -eq 7){throw}; Start-Sleep -Milliseconds 10 } } }
$Manifest=Read-Json "$TaskRoot/manifest.json"
$Authority=Read-Json "$TaskRoot/authority.json"
$Proposal=Read-Json "$TaskRoot/proposal.json"
$LedgerPath="$TaskRoot/ledger.json"
$Ledger=Read-Json $LedgerPath
if($Authority.status -ne 'APPROVED' -or $Authority.manifest_sha256 -ne (Hash "$TaskRoot/manifest.json") -or $Authority.proposal_sha256 -ne (Hash "$TaskRoot/proposal.json")) { throw 'No matching approved authority' }
if($Ledger.status -ne 'APPROVED' -or $null -ne $Ledger.in_flight -or $Ledger.stopped -or $Ledger.consumed[$Mode]) { throw 'Spent, failed or in-flight authority' }
if($Ledger.authority_sha256 -ne (Hash "$TaskRoot/authority.json") -or $Ledger.original_ledger_sha256 -ne $Manifest.original_ledger_sha256) { throw 'Ledger approval/history identity' }
if((Hash "$TaskRoot/entry.py") -ne $Manifest.entry_sha256 -or (Hash $PSCommandPath) -ne $Manifest.supervisor_sha256) { throw 'Wrapper identity changed' }
foreach($Path in $Manifest.frozen.Keys) { if((Hash $Path) -ne $Manifest.frozen[$Path]) { throw "Frozen input changed: $Path" } }
if($Ledger.base_used_seconds -ne [decimal]41.8408609 -or $Ledger.total_seconds -ne 150 -or $Ledger.reserve_seconds -ne 60) { throw 'Original cumulative accounting changed' }
$Original=Read-Json (Join-Path (Split-Path $TaskRoot) 'ledger-followup-v2.json')
if($Original.external_primary -ne 'UNCONSUMED') { throw 'Original external allowance already consumed' }
$Historical=[decimal]0
foreach($Row in @($Original.prior_history)+@($Original.attempts)) { $Historical += [decimal]$Row.receipt.process_wall_seconds }
if($Historical -ne [decimal]41.8408609) { throw 'Original receipt charge mismatch' }
$Used=[decimal]$Ledger.base_used_seconds
foreach($Row in $Ledger.attempts) {
    $Stored=Read-Json "$($Row.path)/execution.json"
    if(($Stored | ConvertTo-Json -Depth 100 -Compress) -ne ($Row.receipt | ConvertTo-Json -Depth 100 -Compress)) { throw 'Stored receipt differs from ledger' }
    $Used += [decimal]$Stored.process_wall_seconds
}
if($Used -ne [decimal]$Ledger.used_seconds -or [decimal]$Ledger.remaining_seconds -ne (150-$Used)) { throw 'Ledger charge mismatch' }
if($Mode -ne 'analytic-adjudication') {
    $Analytic=Read-Json "$TaskRoot/analytic-adjudication-v1/execution.json"
    if($Analytic.status -ne 'completed' -or $Analytic.exit_code -ne 0) { throw 'Analytic saved adjudication not completed' }
    if(-not (Test-Path -LiteralPath "$TaskRoot/semantics-confirmation.json")) { throw 'Independent root semantic adoption required' }
}
if($Mode -eq 'external-adjudication') {
    $External=Read-Json "$TaskRoot/external-v1/execution.json"
    if($External.status -ne 'completed' -or $External.exit_code -ne 0) { throw 'Original external attempt not completed' }
}
$Cap=[double]$Proposal.caps[$Mode]
if($Cap -gt [double](150-$Used-60) -or $Cap -le 0) { throw 'Remaining authority cannot retain reserve' }
$Attempt="$Mode-v1"
$Folder=Join-Path $TaskRoot $Attempt
if(Test-Path -LiteralPath $Folder) { throw 'Attempt already exists; no retry/overwrite' }
New-Item -ItemType Directory -Path $Folder | Out-Null
$Ledger.consumed[$Mode]=$true
$Ledger.in_flight=@{mode=$Mode; path=$Folder; cap_seconds=$Cap; before_used_seconds=$Used; started_utc=[DateTime]::UtcNow.ToString('o')}
$Ledger.remaining_seconds=$null
Save-Json $LedgerPath $Ledger
# In-flight is durable before any Start. Failure before charge/commit refuses restart.
$Info=[Diagnostics.ProcessStartInfo]::new()
$Info.FileName='C:/Python/Python314/python.exe'
$Info.WorkingDirectory=$TaskRoot
$Info.UseShellExecute=$false
$Info.CreateNoWindow=$true
$Info.RedirectStandardOutput=$true
$Info.RedirectStandardError=$true
foreach($Key in @($Info.Environment.Keys)) {
    if($Key -like 'CCX_NPROC*' -or $Key -in @('OPENBLAS_CORETYPE','PYTHONOPTIMIZE')) { $Info.Environment.Remove($Key) | Out-Null }
}
foreach($Key in $Manifest.thread_environment.Keys) { $Info.Environment[$Key]=$Manifest.thread_environment[$Key] }
$Info.Environment['NUMBA_DISABLE_JIT']='1'
$Info.Environment['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
$Info.Environment['PIP_NO_INDEX']='1'
$Clock=[Diagnostics.Stopwatch]::new()
$Deadline=([Diagnostics.Stopwatch]::GetTimestamp()/[double][Diagnostics.Stopwatch]::Frequency)+$Cap
$Arguments=@('-I','-B',"$TaskRoot/entry.py",$Mode,$Attempt,$Deadline.ToString('R',[Globalization.CultureInfo]::InvariantCulture))
foreach($Argument in $Arguments) { $Info.ArgumentList.Add($Argument) }
$Child=[Diagnostics.Process]::new(); $Child.StartInfo=$Info
$Started=$false; $Exited=$false; $Code=$null; $Status='failed'; $ErrorText=$null; $CleanupError=$null
try {
    $Clock.Start()
    $Started=$Child.Start()
    if(-not $Started) { throw 'Start refused' }
    $Child.ProcessorAffinity=[IntPtr]1
    Save-Json "$Folder/root-process.json" @{pid=$Child.Id; creation_utc=$Child.StartTime.ToUniversalTime().ToString('o'); affinity=1}
    $Out=$Child.StandardOutput.ReadToEndAsync(); $Err=$Child.StandardError.ReadToEndAsync()
    $Wait=[Math]::Max(0,[int][Math]::Floor(($Cap-$Clock.Elapsed.TotalSeconds)*1000))
    $Exited=$Child.WaitForExit($Wait)
    if(-not $Exited) { $Status='timeout'; throw 'Process-tree deadline' }
    $Code=$Child.ExitCode
    if($Code -ne 0) { throw "Entry exit $Code" }
    foreach($Name in @('entry-failure.json','resource-failure.json','cleanup-failure.json')) { if(Test-Path -LiteralPath "$Folder/$Name") { throw "Entry refusal: $Name" } }
    $Resources=Read-Json "$Folder/resource-summary.json"
    if($Resources.samples -le 0 -or $Resources.peak_tree_rss -le 0 -or $Resources.peak_tree_rss -gt 2147483648 -or $Resources.cleanup_uncertainty) { throw 'No valid resources/cleanup' }
    $Status='completed'
} catch { $ErrorText=$_.Exception.Message } finally {
    if($Started) {
        try {
            if(-not $Child.HasExited) { $Child.Kill($true) }
            $Wait=[Math]::Max(0,[int][Math]::Floor(($Cap-$Clock.Elapsed.TotalSeconds)*1000))
            $Exited=$Child.WaitForExit($Wait)
            # Creation-bound registry survives owner exit; never open a guessed PID.
            if(Test-Path -LiteralPath "$Folder/owned-processes.json") {
                foreach($Row in (Read-Json "$Folder/owned-processes.json")) {
                    $OwnerBirth=([DateTimeOffset]$Child.StartTime.ToUniversalTime()).ToUnixTimeMilliseconds()/1000.0
                    if($Row.owner_pid -ne $Child.Id -or [Math]::Abs($OwnerBirth-[double]$Row.owner_creation_time) -ge 0.002) { throw 'Registry owner identity mismatch' }
                    try {
                        $Owned=Get-Process -Id $Row.pid -ErrorAction Stop
                        $Birth=([DateTimeOffset]$Owned.StartTime.ToUniversalTime()).ToUnixTimeMilliseconds()/1000.0
                        if([Math]::Abs($Birth-[double]$Row.creation_time) -lt 0.002) { $Owned.Kill($true); if(-not $Owned.WaitForExit([Math]::Max(0,[int][Math]::Floor(($Cap-$Clock.Elapsed.TotalSeconds)*1000)))) { throw 'Owned descendant remains' } }
                    } catch [Microsoft.PowerShell.Commands.ProcessCommandException] { }
                }
            }
            if(-not $Exited) { throw 'Root cleanup uncertain' }
            $Code=$Child.ExitCode
            $Out.GetAwaiter().GetResult() | Set-Content -LiteralPath "$Folder/stdout.log" -Encoding utf8NoBOM
            $Err.GetAwaiter().GetResult() | Set-Content -LiteralPath "$Folder/stderr.log" -Encoding utf8NoBOM
        } catch { $CleanupError=$_.Exception.Message; $Status='failed' }
    }
    $Clock.Stop()
    $Duration=[decimal]$Clock.ElapsedTicks/[decimal][Diagnostics.Stopwatch]::Frequency
    $Used += $Duration
    if($Duration -gt [decimal]$Cap) { $Status='cap-overrun' }
    $Certain=$Exited -and $null -eq $CleanupError -and $Duration -le [decimal]$Cap
    $Receipt=@{mode=$Mode;command=@($Info.FileName)+$Arguments;cwd=$TaskRoot;status=$Status;started=$Started;owned_child_exited=$Exited;exit_code=$Code;primary_error=$ErrorText;cleanup_error=$CleanupError;process_wall_seconds=$Duration;seconds_limit=$Cap;cumulative_used_seconds=$Used;remaining_seconds=$(if($Certain){150-$Used}else{$null});entry_sha256=$Manifest.entry_sha256;supervisor_sha256=$Manifest.supervisor_sha256;input_manifest_sha256=(Hash "$TaskRoot/manifest.json");authority_sha256=(Hash "$TaskRoot/authority.json")}
    Save-Json "$Folder/execution.json" $Receipt
    $Ledger.attempts += @{path=$Folder;receipt=$Receipt}
    $Ledger.used_seconds=$Used
    $Ledger.remaining_seconds=$Receipt.remaining_seconds
    $Ledger.stopped=($Status -ne 'completed')
    $Ledger.in_flight=$null
    Save-Json $LedgerPath $Ledger
}
$Lease.Dispose()
if($Status -ne 'completed') { throw "Attempt $Status; preserved evidence: $Folder" }
