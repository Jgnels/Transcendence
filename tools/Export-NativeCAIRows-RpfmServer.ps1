[CmdletBinding()]
param(
    [string]$ServerUrl = 'ws://127.0.0.1:45127/ws',
    [string]$AcquisitionManifest = '',
    [switch]$SkipVanilla,
    [switch]$SkipMods
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$OutRoot = Join-Path $RepoRoot 'local_inputs\native_cai_reconciliation'
$ExportRoot = Join-Path $OutRoot 'exports'
if (-not $AcquisitionManifest) { $AcquisitionManifest = Join-Path $OutRoot 'acquisition_manifest.json' }
New-Item -ItemType Directory -Force -Path $ExportRoot | Out-Null

$TargetTables = @(
    'cai_gds_task_generators_tables',
    'cai_task_management_system_task_generator_groups_generators_junctions_tables',
    'cai_task_management_system_task_generator_variable_group_junctions_tables',
    'cai_task_management_system_task_generator_variables_tables',
    'cai_task_management_system_variable_group_junctions_tables',
    'cai_task_management_system_variables_tables',
    'cai_variables_tables',
    'cai_variables_overides_tables',
    'cai_personalities_tables',
    'cai_personality_strategic_components_tables',
    'cai_personality_variables_tables',
    'cai_personality_variable_set_junctions_tables',
    'cai_personalities_budget_allocations_tables',
    'cai_personalities_income_allocations_tables',
    'cai_personality_faction_potential_modifiers_tables',
    'cai_query_variable_set_junctions_tables',
    'campaign_ai_manager_behaviour_junctions_tables',
    'cdir_military_generator_template_ratios_tables',
    'cdir_military_generator_unit_qualities_tables'
)
$TargetSet = @{}
foreach ($t in $TargetTables) { $TargetSet[$t.ToLowerInvariant()] = $true }
$SchemaObservations = @()

function Get-Sha256([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Get-SafeName([string]$Name) {
    return (($Name -replace '[^A-Za-z0-9._-]+','_').Trim('_')).ToLowerInvariant()
}

function Receive-WebSocketText([System.Net.WebSockets.ClientWebSocket]$Ws) {
    $buffer = New-Object byte[] 65536
    $stream = New-Object System.IO.MemoryStream
    try {
        do {
            $segment = [System.ArraySegment[byte]]::new($buffer)
            $result = $Ws.ReceiveAsync($segment, [Threading.CancellationToken]::None).GetAwaiter().GetResult()
            if ($result.MessageType -eq [System.Net.WebSockets.WebSocketMessageType]::Close) {
                throw 'RPFM server closed the WebSocket connection.'
            }
            $stream.Write($buffer, 0, $result.Count)
        } while (-not $result.EndOfMessage)
        return [System.Text.Encoding]::UTF8.GetString($stream.ToArray())
    } finally { $stream.Dispose() }
}

$ws = New-Object System.Net.WebSockets.ClientWebSocket
$nextId = 1
try {
    try {
        $ws.ConnectAsync([Uri]$ServerUrl, [Threading.CancellationToken]::None).GetAwaiter().GetResult()
    } catch {
        throw "Could not connect to RPFM server at $ServerUrl. Open RPFM 5.x (the UI starts rpfm_server automatically), verify Warhammer 3 is configured, then rerun. Original error: $($_.Exception.Message)"
    }

    # RPFM sends SessionConnected unsolicited immediately after connection.
    $helloRaw = Receive-WebSocketText $ws
    $hello = $helloRaw | ConvertFrom-Json
    if (-not ($hello.data -and $hello.data.SessionConnected -ne $null)) {
        Write-Warning "Expected SessionConnected first; received: $helloRaw"
    }

    function Invoke-Rpfm([object]$Command) {
        $id = $script:nextId
        $script:nextId++
        $message = [ordered]@{ id = $id; data = $Command } | ConvertTo-Json -Depth 30 -Compress
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($message)
        $segment = [System.ArraySegment[byte]]::new($bytes)
        $script:ws.SendAsync($segment, [System.Net.WebSockets.WebSocketMessageType]::Text, $true, [Threading.CancellationToken]::None).GetAwaiter().GetResult()
        while ($true) {
            $raw = Receive-WebSocketText $script:ws
            $response = $raw | ConvertFrom-Json
            if ($response.data -and $response.data.SessionConnected -ne $null) { continue }
            if ([int]$response.id -ne $id) { continue }
            if ($response.data -and $response.data.Error -ne $null) {
                throw "RPFM server error: $($response.data.Error)"
            }
            return $response.data
        }
    }

    function Get-EffectiveFieldRecord([object]$Field, [object]$DefinitionPatch) {
        $name = [string]$Field.name
        $isKey = [bool]$Field.is_key
        if ($DefinitionPatch -and $name) {
            $fieldPatchProperty = $DefinitionPatch.PSObject.Properties[$name]
            if ($fieldPatchProperty -and $fieldPatchProperty.Value) {
                $isKeyProperty = $fieldPatchProperty.Value.PSObject.Properties['is_key']
                if ($isKeyProperty) {
                    $raw = [string]$isKeyProperty.Value
                    $parsed = $false
                    if ([bool]::TryParse($raw, [ref]$parsed)) { $isKey = $parsed }
                    elseif ($raw -eq '1') { $isKey = $true }
                    elseif ($raw -eq '0') { $isKey = $false }
                }
            }
        }
        return [ordered]@{
            name = $name
            is_key = $isKey
            field_type = $Field.field_type
            is_reference = $Field.is_reference
            description = [string]$Field.description
        }
    }

    function Get-TableSchemaObservation([string]$PackKey, [string]$Path, [string]$SourceName, [string]$DataSource) {
        $usedSource = $DataSource
        try {
            $decoded = Invoke-Rpfm ([ordered]@{ DecodePackedFile = @($PackKey, $Path, $usedSource) })
        } catch {
            if ($usedSource -eq 'PackFile') {
                $usedSource = 'GameFiles'
                $decoded = Invoke-Rpfm ([ordered]@{ DecodePackedFile = @($PackKey, $Path, $usedSource) })
            } else { throw }
        }
        if (-not $decoded.DBRFileInfo) { throw "DecodePackedFile did not return DBRFileInfo for $Path" }
        $tuple = @($decoded.DBRFileInfo)
        if ($tuple.Count -lt 1) { throw "Empty DBRFileInfo for $Path" }
        $db = $tuple[0]
        $table = $db.table
        if (-not $table -or -not $table.definition) { throw "Decoded DB is missing table definition for $Path" }
        $definition = $table.definition
        $definitionPatch = $table.definition_patch
        $fields = @()
        foreach ($field in @($definition.fields)) {
            $fields += Get-EffectiveFieldRecord -Field $field -DefinitionPatch $definitionPatch
        }
        $primaryKeys = @($fields | Where-Object { $_.is_key } | ForEach-Object { $_.name })
        return [ordered]@{
            source = $SourceName
            path = $Path
            data_source = $usedSource
            status = 'DECODED'
            table = [string]$table.table_name
            definition_version = [int]$definition.version
            primary_keys = $primaryKeys
            fields = $fields
        }
    }

    function Get-TargetPaths([object[]]$Files) {
        $paths = New-Object System.Collections.Generic.List[string]
        foreach ($file in $Files) {
            if (-not $file.path) { continue }
            $path = [string]$file.path
            if ($path -notmatch '^db/([^/]+)/') { continue }
            $table = $Matches[1].ToLowerInvariant()
            if ($script:TargetSet.ContainsKey($table) -or ($table -like 'cai_decision_*_tables')) {
                $paths.Add($path)
            }
        }
        return @($paths | Sort-Object -Unique)
    }

    function Export-OpenPack([string]$PackKey, [string]$SourceName, [string]$DataSource = 'PackFile') {
        $treeResp = Invoke-Rpfm ([ordered]@{ GetPackFileDataForTreeView = $PackKey })
        $tree = $treeResp.ContainerInfoVecRFileInfo
        if (-not $tree -or $tree.Count -lt 2) { throw "Unexpected tree response for $SourceName" }
        $files = @($tree[1])
        $targetPaths = Get-TargetPaths $files
        $dest = Join-Path $script:ExportRoot (Get-SafeName $SourceName)
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        if ($targetPaths.Count -eq 0) {
            return [ordered]@{ source=$SourceName; status='NO_TARGET_TABLE_FILES'; pack_key=$PackKey; exported=0; destination=$dest }
        }
        foreach ($path in $targetPaths) {
            try {
                $script:SchemaObservations += Get-TableSchemaObservation -PackKey $PackKey -Path $path -SourceName $SourceName -DataSource $DataSource
            } catch {
                $script:SchemaObservations += [ordered]@{ source=$SourceName; path=$path; status='DECODE_FAILED'; error=$_.Exception.Message }
            }
        }
        $containerPaths = @()
        foreach ($path in $targetPaths) { $containerPaths += ,([ordered]@{ File = $path }) }
        $pathMap = [ordered]@{}
        $pathMap[$DataSource] = $containerPaths
        try {
            $extractResp = Invoke-Rpfm ([ordered]@{ ExtractPackedFiles = @($PackKey, $pathMap, $dest, $true) })
        } catch {
            if ($DataSource -eq 'PackFile') {
                # Some CA/dependency-backed files may be classified as GameFiles.
                $pathMap = [ordered]@{ GameFiles = $containerPaths }
                $extractResp = Invoke-Rpfm ([ordered]@{ ExtractPackedFiles = @($PackKey, $pathMap, $dest, $true) })
                $DataSource = 'GameFiles'
            } else { throw }
        }
        $exported = @($extractResp.StringVecPathBuf[1]).Count
        return [ordered]@{
            source=$SourceName
            status='EXPORTED'
            data_source=$DataSource
            pack_key=$PackKey
            selected_target_files=$targetPaths.Count
            exported=$exported
            destination=$dest
            target_paths=$targetPaths
        }
    }

    # Select WH3 without changing game data. Rebuild=true allows the server to index configured game files.
    $null = Invoke-Rpfm ([ordered]@{ SetGameSelected = @('warhammer_3', $true) })
    $records = @()

    if (-not $SkipVanilla) {
        Write-Host 'Loading vanilla CA packs read-only through RPFM server...'
        $vanillaResp = Invoke-Rpfm 'LoadAllCAPackFiles'
        $vanillaPair = $vanillaResp.StringContainerInfo
        if (-not $vanillaPair -or $vanillaPair.Count -lt 2) { throw 'Unexpected LoadAllCAPackFiles response.' }
        $vanillaKey = [string]$vanillaPair[0]
        $records += Export-OpenPack -PackKey $vanillaKey -SourceName 'vanilla' -DataSource 'PackFile'
        $null = Invoke-Rpfm ([ordered]@{ ClosePack = $vanillaKey })
    }

    if (-not $SkipMods) {
        if (-not (Test-Path -LiteralPath $AcquisitionManifest)) {
            Write-Warning "Acquisition manifest not found at $AcquisitionManifest; skipping mods. Run Acquire-NativeCAIInputs.ps1 first."
        } else {
            $manifest = Get-Content -Raw -LiteralPath $AcquisitionManifest | ConvertFrom-Json
            $groups = @($manifest.mods | Where-Object { $_.path -and (Test-Path -LiteralPath $_.path) } | Group-Object mod_name)
            foreach ($group in $groups) {
                $paths = @($group.Group | ForEach-Object { $_.path } | Sort-Object -Unique)
                if ($paths.Count -eq 0) { continue }
                Write-Host "Opening $($group.Name) read-only ($($paths.Count) pack file(s))..."
                $openResp = Invoke-Rpfm ([ordered]@{ OpenPackFiles = $paths })
                $pair = $openResp.StringContainerInfo
                if (-not $pair -or $pair.Count -lt 2) { throw "Unexpected OpenPackFiles response for $($group.Name)" }
                $packKey = [string]$pair[0]
                $records += Export-OpenPack -PackKey $packKey -SourceName $group.Name -DataSource 'PackFile'
                $null = Invoke-Rpfm ([ordered]@{ ClosePack = $packKey })
            }
        }
    }

    $fileRecords = @()
    if (Test-Path $ExportRoot) {
        foreach ($file in Get-ChildItem -LiteralPath $ExportRoot -File -Recurse -ErrorAction SilentlyContinue) {
            $fileRecords += [ordered]@{
                path = $file.FullName.Substring($ExportRoot.Length).TrimStart([char[]]'\/') -replace '\\','/'
                bytes = $file.Length
                sha256 = Get-Sha256 $file.FullName
            }
        }
    }
    $schemaMetadataPath = Join-Path $OutRoot 'rpfm_table_schema_metadata.json'
    [ordered]@{
        generated_at_utc = (Get-Date).ToUniversalTime().ToString('o')
        authority = 'RPFM_DECODED_SCHEMA_METADATA_READ_ONLY'
        observations = $SchemaObservations
    } | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $schemaMetadataPath -Encoding UTF8

    # Build a fail-closed primary-key specification from VANILLA decoded definitions only.
    # RPFM's current schema Field.is_key is the primary-key marker; definition_patch can
    # override it, which Get-EffectiveFieldRecord applies before this aggregation.
    $keyTables = [ordered]@{}
    $vanillaDecoded = @($SchemaObservations | Where-Object { $_.source -eq 'vanilla' -and $_.status -eq 'DECODED' -and $_.table })
    foreach ($group in @($vanillaDecoded | Group-Object table | Sort-Object Name)) {
        $keyVariants = @($group.Group | ForEach-Object { (@($_.primary_keys) -join '|||KEYSEP|||') } | Sort-Object -Unique)
        $versions = @($group.Group | ForEach-Object { $_.definition_version } | Sort-Object -Unique)
        if ($keyVariants.Count -eq 1 -and $keyVariants[0]) {
            $keys = @($keyVariants[0] -split '\|\|\|KEYSEP\|\|\|')
            $keyTables[$group.Name] = [ordered]@{
                status = 'RESOLVED_FROM_RPFM_VANILLA_DEFINITION'
                primary_keys = $keys
                observed_definition_versions = $versions
                observations = $group.Count
            }
        } elseif ($keyVariants.Count -eq 1) {
            $keyTables[$group.Name] = [ordered]@{
                status = 'NO_PRIMARY_KEY_FIELDS_OBSERVED'
                primary_keys = @()
                observed_definition_versions = $versions
                observations = $group.Count
            }
        } else {
            $keyTables[$group.Name] = [ordered]@{
                status = 'CONFLICTING_PRIMARY_KEY_DEFINITIONS'
                primary_keys = @()
                observed_key_variants = $keyVariants
                observed_definition_versions = $versions
                observations = $group.Count
            }
        }
    }
    $keySpecPath = Join-Path $OutRoot 'rpfm_table_key_spec.json'
    [ordered]@{
        schema_version = 1
        generated_at_utc = (Get-Date).ToUniversalTime().ToString('o')
        authority = 'RPFM_ACTIVE_SCHEMA_DECODED_VANILLA_ONLY'
        expected_patch_8_1_schema_commit = 'd12f59cb6de106d205f51b81739951adbc840c49'
        expected_patch_8_1_schema_git_blob_sha1 = '232216808ff5d38edd9e056c7828afdc1700d297'
        note = 'Keys are emitted only when all decoded vanilla instances agree. Conflicts/no-key cases remain unresolved; no key is guessed.'
        tables = $keyTables
    } | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $keySpecPath -Encoding UTF8

    $runManifest = [ordered]@{
        generated_at_utc = (Get-Date).ToUniversalTime().ToString('o')
        authority = 'READ_ONLY_RPFM_SERVER_EXPORT'
        rpfm_server = $ServerUrl
        game = 'warhammer_3'
        target_table_count = $TargetTables.Count
        dynamic_family = 'cai_decision_*_tables'
        records = $records
        exported_files = $fileRecords
        safety = @(
            'No SavePack/SavePackAs command is used.',
            'No WH3 or Workshop pack is modified.',
            'Exports are written only under ignored local_inputs/native_cai_reconciliation/exports.',
            'RPFM extracts the selected DB evidence read-only. Some RPFM server builds may return binary DB payloads even when as_tsv=true; downstream tooling detects and decodes that case fail-closed.'
        )
    }
    $runPath = Join-Path $OutRoot 'rpfm_export_manifest.json'
    $runManifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $runPath -Encoding UTF8
    Write-Host "RPFM export manifest: $runPath"
    Write-Host "RPFM decoded schema metadata: $schemaMetadataPath"
    Write-Host "RPFM primary-key spec: $keySpecPath"
    foreach ($record in $records) {
        Write-Host ("{0}: {1} target files selected; status={2}" -f $record.source, $record.selected_target_files, $record.status)
    }

    try { $null = Invoke-Rpfm 'ClientDisconnecting' } catch {}
} finally {
    if ($ws.State -eq [System.Net.WebSockets.WebSocketState]::Open) {
        try { $ws.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure, 'done', [Threading.CancellationToken]::None).GetAwaiter().GetResult() } catch {}
    }
    $ws.Dispose()
}
