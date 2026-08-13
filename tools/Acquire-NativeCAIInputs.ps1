[CmdletBinding()]
param(
    [string]$RpfmRoot = "",
    [string]$SteamRoot = "",
    [switch]$CopyWorkshopPacks
)

$ErrorActionPreference = 'Stop'
$ExpectedSchemaGitBlob = '232216808ff5d38edd9e056c7828afdc1700d297'
$ExpectedSchemaCommit = 'd12f59cb6de106d205f51b81739951adbc840c49'
$Wh3AppId = '1142710'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$OutRoot = Join-Path $RepoRoot 'local_inputs\native_cai_reconciliation'
$AcquireRoot = Join-Path $OutRoot 'acquired'
New-Item -ItemType Directory -Force -Path $AcquireRoot | Out-Null

function Get-Sha256([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Get-GitBlobSha1([string]$Path) {
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $prefix = [System.Text.Encoding]::ASCII.GetBytes("blob $($bytes.Length)`0")
    $all = New-Object byte[] ($prefix.Length + $bytes.Length)
    [Array]::Copy($prefix, 0, $all, 0, $prefix.Length)
    [Array]::Copy($bytes, 0, $all, $prefix.Length, $bytes.Length)
    $sha1 = [System.Security.Cryptography.SHA1]::Create()
    try {
        return (($sha1.ComputeHash($all) | ForEach-Object { $_.ToString('x2') }) -join '')
    } finally { $sha1.Dispose() }
}

function Get-SteamRoots {
    param([string]$Explicit)
    $roots = New-Object System.Collections.Generic.List[string]
    if ($Explicit -and (Test-Path -LiteralPath $Explicit)) { $roots.Add((Resolve-Path $Explicit).Path) }
    try {
        $reg = Get-ItemProperty 'HKCU:\Software\Valve\Steam' -ErrorAction Stop
        if ($reg.SteamPath -and (Test-Path $reg.SteamPath)) { $roots.Add((Resolve-Path $reg.SteamPath).Path) }
    } catch {}
    foreach ($candidate in @(
        'C:\Program Files (x86)\Steam',
        'C:\Program Files\Steam'
    )) { if (Test-Path $candidate) { $roots.Add((Resolve-Path $candidate).Path) } }

    $expanded = New-Object System.Collections.Generic.List[string]
    foreach ($root in ($roots | Select-Object -Unique)) {
        $expanded.Add($root)
        $vdf = Join-Path $root 'steamapps\libraryfolders.vdf'
        if (Test-Path $vdf) {
            foreach ($line in Get-Content -LiteralPath $vdf -ErrorAction SilentlyContinue) {
                if ($line -match '^\s*"path"\s+"(.+)"') {
                    $p = $Matches[1] -replace '\\\\','\'
                    if (Test-Path $p) { $expanded.Add($p) }
                }
            }
        }
    }
    return @($expanded | Select-Object -Unique)
}

function Find-Schema {
    param([string]$ExplicitRoot)
    $candidates = New-Object System.Collections.Generic.List[string]

    function Add-SchemaIfPresent([string]$Path) {
        if ($Path -and (Test-Path -LiteralPath $Path -PathType Leaf)) {
            $candidates.Add((Resolve-Path -LiteralPath $Path).Path)
        }
    }

    # RPFM 5 uses directories::ProjectDirs("com", "FrodoWazEre", "rpfm")
    # and stores schemas under <config>/schemas. A custom config directory, when
    # configured, is named in config_folder.txt under the default config path.
    $defaultConfigs = @()
    if ($env:APPDATA) {
        $defaultConfigs += (Join-Path $env:APPDATA 'FrodoWazEre\rpfm')
        # Legacy/alternate candidate retained for older local installs.
        $defaultConfigs += (Join-Path $env:APPDATA 'Frodo45127\rpfm')
    }
    if ($env:LOCALAPPDATA) {
        $defaultConfigs += (Join-Path $env:LOCALAPPDATA 'FrodoWazEre\rpfm')
    }
    foreach ($config in ($defaultConfigs | Select-Object -Unique)) {
        Add-SchemaIfPresent (Join-Path $config 'schemas\schema_wh3.ron')
        $redirect = Join-Path $config 'config_folder.txt'
        if (Test-Path -LiteralPath $redirect -PathType Leaf) {
            $customRaw = Get-Content -Raw -LiteralPath $redirect -ErrorAction SilentlyContinue
            if ($customRaw) {
                $custom = $customRaw.Trim()
                if ($custom) { Add-SchemaIfPresent (Join-Path $custom 'schemas\schema_wh3.ron') }
            }
        }
    }

    # Explicit portable/unusual RPFM folder: recursive lookup is acceptable
    # because the owner deliberately scoped the root.
    if ($ExplicitRoot -and (Test-Path -LiteralPath $ExplicitRoot)) {
        Get-ChildItem -LiteralPath $ExplicitRoot -Filter 'schema_wh3.ron' -File -Recurse -ErrorAction SilentlyContinue |
            ForEach-Object { $candidates.Add($_.FullName) }
    }

    # Downloads is bounded enough to support a manually downloaded schema/repo
    # without recursively walking all of AppData.
    $downloads = Join-Path $HOME 'Downloads'
    if (Test-Path -LiteralPath $downloads) {
        Get-ChildItem -LiteralPath $downloads -Filter 'schema_wh3.ron' -File -Recurse -ErrorAction SilentlyContinue |
            ForEach-Object { $candidates.Add($_.FullName) }
    }
    return @($candidates | Select-Object -Unique)
}

$steamRoots = @(Get-SteamRoots -Explicit $SteamRoot)
$gameDataCandidates = @()
$workshopCandidates = @()
foreach ($root in $steamRoots) {
    $gameData = Join-Path $root 'steamapps\common\Total War WARHAMMER III\data'
    if (Test-Path $gameData) { $gameDataCandidates += (Resolve-Path $gameData).Path }
    $workshop = Join-Path $root "steamapps\workshop\content\$Wh3AppId"
    if (Test-Path $workshop) { $workshopCandidates += (Resolve-Path $workshop).Path }
}

$schemaRecords = @()
foreach ($schema in @(Find-Schema -ExplicitRoot $RpfmRoot)) {
    $blob = Get-GitBlobSha1 $schema
    $schemaRecords += [ordered]@{
        path = $schema
        bytes = (Get-Item -LiteralPath $schema).Length
        sha256 = Get-Sha256 $schema
        git_blob_sha1 = $blob
        exact_patch_8_1_schema = ($blob -eq $ExpectedSchemaGitBlob)
    }
}
$bestSchema = $schemaRecords | Where-Object { $_.exact_patch_8_1_schema } | Select-Object -First 1
if (-not $bestSchema) { $bestSchema = $schemaRecords | Select-Object -First 1 }
if ($bestSchema) {
    Copy-Item -LiteralPath $bestSchema.path -Destination (Join-Path $AcquireRoot 'schema_wh3.ron') -Force
}

$mods = @(
    @{ name='SFO_Grimhammer_III'; id='2792731173' },
    @{ name='DeepWar_AI'; id='2978779730' },
    @{ name='Hecleas_AI_Overhaul'; id='2905096541' },
    @{ name='Incata_AI_Army_Tasks_and_Strategy'; id='2935815665' },
    @{ name='AI_Camping_Settlements_Fix'; id='3594429287' },
    @{ name='Campaign_AI_Tweaks_Sleepy'; id='3485519396' },
    @{ name='Better_AI_Army_Builder'; id='3617312541' }
)
$modRecords = @()
foreach ($mod in $mods) {
    $found = @()
    foreach ($workshopRoot in $workshopCandidates) {
        $dir = Join-Path $workshopRoot $mod.id
        if (Test-Path $dir) {
            foreach ($pack in Get-ChildItem -LiteralPath $dir -Filter '*.pack' -File -Recurse -ErrorAction SilentlyContinue) {
                $rec = [ordered]@{
                    mod_name = $mod.name
                    workshop_id = $mod.id
                    path = $pack.FullName
                    bytes = $pack.Length
                    sha256 = Get-Sha256 $pack.FullName
                }
                $found += $rec
                if ($CopyWorkshopPacks) {
                    $copyDir = Join-Path $AcquireRoot ("workshop_" + $mod.id)
                    New-Item -ItemType Directory -Force -Path $copyDir | Out-Null
                    Copy-Item -LiteralPath $pack.FullName -Destination (Join-Path $copyDir $pack.Name) -Force
                }
            }
        }
    }
    if ($found.Count -eq 0) {
        $modRecords += [ordered]@{ mod_name=$mod.name; workshop_id=$mod.id; status='NOT_FOUND' }
    } else { $modRecords += $found }
}

$manifest = [ordered]@{
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    repository_root = $RepoRoot
    authority = 'RESEARCH_INPUT_DISCOVERY_ONLY'
    expected_schema_commit = $ExpectedSchemaCommit
    expected_schema_git_blob_sha1 = $ExpectedSchemaGitBlob
    schema_candidates = $schemaRecords
    selected_schema_exact = [bool]($bestSchema -and $bestSchema.exact_patch_8_1_schema)
    steam_roots = $steamRoots
    game_data_paths = $gameDataCandidates
    workshop_roots = $workshopCandidates
    mods = $modRecords
    workshop_packs_copied = [bool]$CopyWorkshopPacks
    notes = @(
        'This script does not edit WH3, Workshop content, saves, load order, or repository research state.',
        'CA game packs are not copied.',
        'Workshop packs are copied only with -CopyWorkshopPacks and remain under ignored local_inputs.',
        'Exact schema bytes are copied because rpfm-schemas is MIT-licensed; verify git_blob_sha1 before row decoding.'
    )
}
$manifestPath = Join-Path $OutRoot 'acquisition_manifest.json'
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

$summary = @()
$summary += 'TRANSCENDENCE NATIVE CAI INPUT ACQUISITION'
$summary += "manifest=$manifestPath"
$summary += "expected_schema_commit=$ExpectedSchemaCommit"
$summary += "expected_schema_git_blob=$ExpectedSchemaGitBlob"
if ($bestSchema) {
    $summary += "schema=$($bestSchema.path)"
    $summary += "schema_git_blob=$($bestSchema.git_blob_sha1)"
    $summary += "schema_exact_patch_8_1=$($bestSchema.exact_patch_8_1_schema)"
} else { $summary += 'schema=NOT_FOUND' }
$summary += "game_data_paths=$($gameDataCandidates.Count)"
$summary += "workshop_roots=$($workshopCandidates.Count)"
$summary += "found_pack_records=$(($modRecords | Where-Object { $_.status -ne 'NOT_FOUND' }).Count)"
$summary += ''
$summary += 'Next: update RPFM schemas if schema_exact_patch_8_1 is not True; then export target DB tables as TSV per intake/NATIVE_CAI_RECONCILIATION_OWNER_HANDOFF.md.'
$summaryPath = Join-Path $OutRoot 'ACQUISITION_SUMMARY.txt'
$summary | Set-Content -LiteralPath $summaryPath -Encoding UTF8
$summary | ForEach-Object { Write-Host $_ }
