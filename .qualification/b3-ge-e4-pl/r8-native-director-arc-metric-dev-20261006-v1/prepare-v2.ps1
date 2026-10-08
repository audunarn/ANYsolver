$ErrorActionPreference='Stop'
$raw=$PSScriptRoot
$repo=Split-Path (Split-Path (Split-Path $raw -Parent) -Parent) -Parent
$utf8=[System.Text.UTF8Encoding]::new($false)
function SaveJson($name,$value){[System.IO.File]::WriteAllText((Join-Path $raw $name),($value|ConvertTo-Json -Depth 40),$utf8)}
SaveJson 'preparation-v1-failure.json' ([ordered]@{status='PREPARATION_FAILED';cause='Nonexistent examples/stiffened_shell_native_fibre_bl5_mixed_j2.py and nonterminating PowerShell copy/hash errors';python_launched=$false;verification_seconds_used=0;partial_v1_preserved=$true})
$guarded=$false
try{& (Join-Path $raw 'supervise-v1.ps1') -Mode source -Attempt pending-guard -Cap 1 -Reserve 60}catch{if($_.Exception.Message -notlike 'PENDING_USER_APPROVAL:*'){throw};$guarded=$true}
if(-not $guarded -or (Test-Path -LiteralPath (Join-Path $raw 'pending-guard'))){throw 'Pending-authority guard did not refuse before directory/process creation'}
$ledger=Get-Content -LiteralPath (Join-Path $raw 'ledger.json') -Raw|ConvertFrom-Json
if($ledger.used_seconds -ne 0 -or $ledger.attempts.Count -ne 0){throw 'Preparation unexpectedly consumed verification time'}
$snapshot=Join-Path $raw 'inputs-snapshot-v2'
if(Test-Path -LiteralPath $snapshot){throw 'v2 snapshot already exists'}
[void](New-Item -ItemType Directory -Path $snapshot)
$names=@('pyproject.toml','tests/test_stiffened_shell_native_director_arc_metric.py','tests/test_stiffened_shell_arc_chart.py','tests/test_stiffened_shell_native_material_bl5_arc.py','tests/test_native_material_bl5_arc_same_origin_jacobian.py','examples/stiffened_shell_native_director_arc_metric.py','examples/stiffened_shell_native_material_bl5_arc.py','examples/stiffened_shell_native_fibre_bl5_mixed_j2_displacement.py','examples/stiffened_shell_native_fibre_bl5_displacement.py','examples/stiffened_shell_native_fibre_bl5.py','examples/stiffened_shell_native_fibre_bl5_material.py')
$inputs=[ordered]@{}
foreach($name in $names){
    $source=Join-Path $repo $name;$target=Join-Path $snapshot $name
    [void][System.IO.Directory]::CreateDirectory((Split-Path $target -Parent))
    [System.IO.File]::Copy($source,$target,$false)
    $inputs[$name]=(Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLower()
}
[System.IO.File]::Copy((Join-Path $raw 'inputs-snapshot-v1/loaded-seed.bin'),(Join-Path $snapshot 'loaded-seed.bin'),$false)
$inputs['loaded-seed.bin']=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $snapshot 'loaded-seed.bin')).Hash.ToLower()
$manifest=Get-Content -LiteralPath (Join-Path $raw 'inputs-manifest-v1.json') -Raw|ConvertFrom-Json
$manifest.status='PREPARED_UNRUN';$manifest.inputs=[pscustomobject]$inputs
SaveJson 'inputs-manifest-v2.json' $manifest
$entry=[System.IO.File]::ReadAllText((Join-Path $raw 'entry-v1.py')).Replace('inputs-snapshot-v1','inputs-snapshot-v2').Replace('inputs-manifest-v1.json','inputs-manifest-v2.json')
$entry=$entry.Replace("str(p.relative_to(REPO/'src')).replace('\\','/')","p.relative_to(REPO/'src').as_posix()")
$entry=$entry.Replace("str(p.relative_to(solver)).replace('\\','/')","p.relative_to(solver).as_posix()")
$entry=$entry.Replace("str(Path(row['path']).relative_to(solver)).replace('\\','/')","Path(row['path']).relative_to(solver).as_posix()")
[System.IO.File]::WriteAllText((Join-Path $raw 'entry-v2.py'),$entry,$utf8)
$supervisor=[System.IO.File]::ReadAllText((Join-Path $raw 'supervise-v1.ps1')).Replace('entry-v1.py','entry-v2.py').Replace('inputs-snapshot-v1','inputs-snapshot-v2').Replace('inputs-manifest-v1.json','inputs-manifest-v2.json')
[System.IO.File]::WriteAllText((Join-Path $raw 'supervise-v2.ps1'),$supervisor,$utf8)
$tokens=$null;$parseErrors=$null
[void][System.Management.Automation.Language.Parser]::ParseFile((Join-Path $raw 'supervise-v2.ps1'),[ref]$tokens,[ref]$parseErrors)
if($parseErrors.Count){throw ($parseErrors|Out-String)}
SaveJson 'preparation-v2.json' ([ordered]@{status='PREPARED_UNRUN';v1_failure_preserved=$true;pending_guard_refused_before_launch=$guarded;python_launched=$false;verification_seconds_used=0;inputs_count=$inputs.Count;source_modules_count=$manifest.source_modules.psobject.Properties.Count;entry_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw 'entry-v2.py')).Hash.ToLower();supervisor_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw 'supervise-v2.ps1')).Hash.ToLower();manifest_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $raw 'inputs-manifest-v2.json')).Hash.ToLower()})
$authority=Get-Content -LiteralPath (Join-Path $raw 'authority.json') -Raw|ConvertFrom-Json
SaveJson 'authority-pending-original.json' $authority
$authority.status='APPROVED';$authority.approval_evidence='Human reply I approve on 2026-10-06 to fresh300s director-metric candidate4295a3da request; scope and exclusions unchanged'
SaveJson 'authority.json' $authority
$ledger.status='APPROVED';SaveJson 'ledger.json' $ledger
Write-Output 'Prepared v2: 12 frozen inputs; pending guard passed; human approval recorded; used0/remaining300 seconds'
