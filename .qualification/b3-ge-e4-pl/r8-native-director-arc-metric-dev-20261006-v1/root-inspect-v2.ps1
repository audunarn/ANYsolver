$ErrorActionPreference='Stop'
$raw=$PSScriptRoot
$repo=Split-Path (Split-Path (Split-Path $raw -Parent) -Parent) -Parent
function Json($name){Get-Content -LiteralPath (Join-Path $raw $name) -Raw|ConvertFrom-Json}
function Sha($path){(Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLower()}
$ledger=Json 'ledger.json';$manifest=Json 'inputs-manifest-v2.json';$artifact=Json 'installed-v2/artifact-binding.json'
if($ledger.status -ne 'APPROVED' -or $ledger.total_seconds -ne 300 -or $ledger.attempts.Count -ne 4){throw 'Unexpected cumulative ledger'}
$sum=0.0;$steps=@()
foreach($attempt in @('source-v2','build-v2','install-v2','installed-v2')){
    $receipt=Json "$attempt/execution.json";$resource=Json "$attempt/resource-summary.json"
    if($receipt.status -ne 'completed' -or $receipt.exit_code -ne 0 -or $resource.peak_tree_rss -ge 2147483648){throw "Failed/resource-invalid $attempt"}
    if($receipt.entry_sha256 -ne (Sha (Join-Path $raw 'entry-v2.py')) -or $receipt.supervisor_sha256 -ne (Sha (Join-Path $raw 'supervise-v2.ps1')) -or $receipt.input_manifest_sha256 -ne (Sha (Join-Path $raw 'inputs-manifest-v2.json')) -or $receipt.authority_sha256 -ne (Sha (Join-Path $raw 'authority.json'))){throw 'Receipt identity mismatch'}
    if(Test-Path -LiteralPath (Join-Path $raw "$attempt/affinity-failure.json")){throw 'Affinity failure'}
    if(Test-Path -LiteralPath (Join-Path $raw "$attempt/resource-failure.json")){throw 'Memory failure'}
    $sum+=[double]$receipt.process_wall_seconds
    $steps+=[ordered]@{attempt=$attempt;process_wall_seconds=$receipt.process_wall_seconds;peak_sampled_tree_bytes=$resource.peak_tree_rss;execution_sha256=(Sha (Join-Path $raw "$attempt/execution.json"))}
}
if([Math]::Abs($sum-[double]$ledger.used_seconds) -gt 1e-9 -or $sum -ge 300){throw 'Cumulative accounting mismatch'}
$checks=@()
foreach($attempt in @('source-v2','installed-v2')){
    [xml]$junit=Get-Content -LiteralPath (Join-Path $raw "$attempt/junit.xml") -Raw
    $suite=$junit.testsuites.testsuite
    if($suite.tests -ne '17' -or $suite.failures -ne '0' -or $suite.errors -ne '0' -or $suite.skipped -ne '0'){throw "Nonpassing/skipped $attempt"}
    foreach($phase in @('before','after')){
        $runtime=Json "$attempt/runtime-$phase.json"
        if($runtime.affinity.Count -ne 1 -or $runtime.affinity[0] -ne 0 -or $runtime.numba_threads -ne 1 -or -not $runtime.jit_off -or @($runtime.pools|Where-Object num_threads -ne 1).Count){throw 'Incorrect effective runtime'}
    }
    $checks+=[ordered]@{attempt=$attempt;passed=17;failed=0;skipped=0;junit_sha256=(Sha (Join-Path $raw "$attempt/junit.xml"))}
}
$modules=@($manifest.source_modules.psobject.Properties)
if($modules.Count -ne 430 -or @($artifact.payload.psobject.Properties).Count -ne 430){throw 'Module inventory changed'}
foreach($item in $modules){
    if((Sha (Join-Path $repo "src/$($item.Name)")) -ne $item.Value -or (Sha (Join-Path $raw "site-v1/$($item.Name)")) -ne $item.Value -or $artifact.payload.psobject.Properties[$item.Name].Value -ne $item.Value){throw "Source/artifact mismatch $($item.Name)"}
}
foreach($item in $manifest.inputs.psobject.Properties){if((Sha (Join-Path $raw "inputs-snapshot-v2/$($item.Name)")) -ne $item.Value){throw 'Input mutation'}}
if((Sha $artifact.wheel) -ne $artifact.wheel_sha256){throw 'Wheel changed'}
$loaded=Json 'installed-v2/loaded-modules.json'
$result=[ordered]@{status='LIMITED_INSTALLED_DEVELOPMENT_PASS';candidate_source_commit=$manifest.candidate_source_commit;checkpoint_commit=$manifest.checkpoint_commit;wheel_sha256=$artifact.wheel_sha256;package_module_count=430;actual_imported_files=@($loaded.psobject.Properties).Count;loaded_solver_files=@($loaded.psobject.Properties|Where-Object Name -Like 'anysolver*').Count;checks=$checks;execution=$steps;total_process_wall_seconds=$sum;allowance_seconds=300;remaining_seconds=(300-$sum);runtime='CPU0; numerical pools1; Numba1; JITdisabled; sampled tree memory<2GiB';preparation_failure_preserved='preparation-v1-failure.json';pending_guard_proof='preparation-v2.json';fixture_sha256=$manifest.inputs.'loaded-seed.bin';claims_excluded=@('F03/connection acceptance','capacity/first limit point/descending branch','mesh and unit engineering qualification','different-family scientific acceptance','complete G0-G6','main merge or release')}
[System.IO.File]::WriteAllText((Join-Path $raw 'root-installed-director-proof-v2.json'),($result|ConvertTo-Json -Depth 20),[System.Text.UTF8Encoding]::new($false))
[pscustomobject]$result|Select-Object status,wheel_sha256,package_module_count,actual_imported_files,loaded_solver_files,total_process_wall_seconds,remaining_seconds|ConvertTo-Json
