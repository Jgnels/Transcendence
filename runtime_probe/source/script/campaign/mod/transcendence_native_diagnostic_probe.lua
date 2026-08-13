-- Transcendence v0.2N native-CAI diagnostic behavior-study telemetry probe.
-- RESEARCH ONLY. Read-only by design: no campaign mutation, no save mutation, no randomness.
-- This probe intentionally observes complete AI-faction state and is APPLICATION-INELIGIBLE.

local TRANS_DIAG_SCHEMA = 1
local TRANS_DIAG_PREFIX = "TRANS_DIAG"
local TRANS_DIAG_KIND = "native_diagnostic"
local TRANS_DIAG_LOG = "transcendence_native_diagnostic_log.txt"
local TRANS_DIAG_MAX_ITEMS = 128
local TRANS_DIAG_MAX_UNITS = 40
local TRANS_DIAG_BATTLE_SEQUENCE = 0

local function trans_diag_value(value)
    if value == nil then return "null" end
    if value == true then return "true" end
    if value == false then return "false" end
    local text = tostring(value)
    text = string.gsub(text, "%%", "%%25")
    text = string.gsub(text, "|", "%%7C")
    text = string.gsub(text, "=", "%%3D")
    text = string.gsub(text, "\r", "%%0D")
    text = string.gsub(text, "\n", "%%0A")
    return text
end

local function trans_diag_append(line)
    local opened, handle = pcall(io.open, TRANS_DIAG_LOG, "a")
    if not opened or not handle then return false end
    local wrote = pcall(function()
        handle:write(line .. "\n")
        handle:flush()
        handle:close()
    end)
    return wrote
end

local function trans_diag_emit(event_name, fields)
    local parts = { TRANS_DIAG_PREFIX, tostring(TRANS_DIAG_SCHEMA), trans_diag_value(event_name) }
    if fields then
        for index = 1, #fields do
            local field = fields[index]
            parts[#parts + 1] = trans_diag_value(field[1]) .. "=" .. trans_diag_value(field[2])
        end
    end
    local line = table.concat(parts, "|")
    trans_diag_append(line)
    if ModLog then ModLog(line) elseif out then out(line) end
end

local function trans_diag_safe(name, fallback, callback)
    local ok, value = pcall(callback)
    if ok then return value, true end
    trans_diag_emit("CAPABILITY", {{"name", name}, {"available", false}, {"error", value}})
    return fallback, false
end

local function trans_diag_list(name, callback)
    local list, available = trans_diag_safe(name, nil, callback)
    if not available or not list then return nil, -1, false end
    local count, count_available = trans_diag_safe(name .. ".num_items", -1, function() return list:num_items() end)
    return list, count, count_available
end

local function trans_diag_safe3(name, fallback1, fallback2, fallback3, callback)
    local ok, value1, value2, value3 = pcall(callback)
    if ok then return value1, value2, value3, true end
    trans_diag_emit("CAPABILITY", {{"name", name}, {"available", false}, {"error", value1}})
    return fallback1, fallback2, fallback3, false
end

local function trans_diag_average_health(force)
    local units = trans_diag_safe("diagnostic.force.unit_list", nil, function() return force:unit_list() end)
    if not units then return -1, -1 end
    local count = trans_diag_safe("diagnostic.force.unit_list.num_items", -1, function() return units:num_items() end)
    if count <= 0 then return count, -1 end
    local inspected = math.min(count, TRANS_DIAG_MAX_UNITS)
    local total = 0
    local valid = 0
    for index = 0, inspected - 1 do
        local unit = units:item_at(index)
        local health, available = trans_diag_safe(
            "diagnostic.unit.percentage_proportion_of_full_strength",
            -1,
            function() return unit:percentage_proportion_of_full_strength() end
        )
        if available and health >= 0 then
            total = total + health
            valid = valid + 1
        end
    end
    if valid == 0 then return count, -1 end
    return count, math.floor((total / valid) * 100 + 0.5) / 100
end

local function trans_diag_settlement_position(region)
    local settlement = trans_diag_safe("diagnostic.region.settlement", nil, function() return region:settlement() end)
    if not settlement or settlement:is_null_interface() then return -1, -1 end
    local x = trans_diag_safe("diagnostic.settlement.logical_position_x", -1, function() return settlement:logical_position_x() end)
    local y = trans_diag_safe("diagnostic.settlement.logical_position_y", -1, function() return settlement:logical_position_y() end)
    return x, y
end

local function trans_diag_emit_forces(faction, phase, turn)
    local list, total, available = trans_diag_list("diagnostic.faction.military_force_list", function() return faction:military_force_list() end)
    if not available then return -1, -1 end
    local emitted = 0
    local filtered = 0
    local limit = math.min(total, TRANS_DIAG_MAX_ITEMS)
    for index = 0, limit - 1 do
        local force = list:item_at(index)
        local is_garrison = trans_diag_safe("diagnostic.force.is_armed_citizenry", true, function() return force:is_armed_citizenry() end)
        local is_army = trans_diag_safe("diagnostic.force.is_army", false, function() return force:is_army() end)
        local has_general = trans_diag_safe("diagnostic.force.has_general", false, function() return force:has_general() end)
        if not is_garrison and is_army and has_general then
            local general = trans_diag_safe("diagnostic.force.general_character", nil, function() return force:general_character() end)
            local force_cqi = trans_diag_safe("diagnostic.force.command_queue_index", -1, function() return force:command_queue_index() end)
            local unit_count, average_health = trans_diag_average_health(force)
            local x = -1
            local y = -1
            local general_cqi = -1
            local subtype = "unknown"
            local character_type_key = "unknown"
            local region = "none"
            local action_points_remaining_pct = -1
            if general and not general:is_null_interface() then
                general_cqi = trans_diag_safe("diagnostic.general.command_queue_index", -1, function() return general:command_queue_index() end)
                subtype = trans_diag_safe("diagnostic.general.character_subtype_key", "unknown", function() return general:character_subtype_key() end)
                character_type_key = trans_diag_safe("diagnostic.general.character_type_key", "unknown", function() return general:character_type_key() end)
                x = trans_diag_safe("diagnostic.general.logical_position_x", -1, function() return general:logical_position_x() end)
                y = trans_diag_safe("diagnostic.general.logical_position_y", -1, function() return general:logical_position_y() end)
                action_points_remaining_pct = trans_diag_safe("diagnostic.general.action_points_remaining_percent", -1, function() return general:action_points_remaining_percent() end)
                local current_region = trans_diag_safe("diagnostic.general.region", nil, function() return general:region() end)
                if current_region and not current_region:is_null_interface() then
                    region = trans_diag_safe("diagnostic.general.region.name", "unknown", function() return current_region:name() end)
                end
            end
            trans_diag_emit("AI_FORCE", {
                {"turn", turn}, {"phase", phase}, {"faction", faction:name()}, {"index", index},
                {"force_cqi", force_cqi}, {"general_cqi", general_cqi}, {"subtype", subtype},
                {"character_type_key", character_type_key}, {"unit_count", unit_count},
                {"force_strength", trans_diag_safe("diagnostic.force.strength", -1, function() return force:strength() end)},
                {"average_unit_health_pct", average_health},
                {"action_points_remaining_pct", action_points_remaining_pct},
                {"stance", trans_diag_safe("diagnostic.force.active_stance", "unknown", function() return force:active_stance() end)},
                {"x", x}, {"y", y}, {"region", region}
            })
            emitted = emitted + 1
        else
            filtered = filtered + 1
        end
    end
    return emitted, filtered
end

local function trans_diag_emit_regions(faction, phase, turn)
    local list, total, available = trans_diag_list("diagnostic.faction.region_list", function() return faction:region_list() end)
    if not available then return -1 end
    local emitted = 0
    local limit = math.min(total, TRANS_DIAG_MAX_ITEMS)
    for index = 0, limit - 1 do
        local region = list:item_at(index)
        local x, y = trans_diag_settlement_position(region)
        local under_siege = false
        local residence = trans_diag_safe("diagnostic.region.garrison_residence", nil, function() return region:garrison_residence() end)
        if residence and not residence:is_null_interface() then
            under_siege = trans_diag_safe("diagnostic.region.garrison_residence.is_under_siege", false, function() return residence:is_under_siege() end)
        end
        trans_diag_emit("AI_REGION", {
            {"turn", turn}, {"phase", phase}, {"faction", faction:name()}, {"index", index},
            {"region", trans_diag_safe("diagnostic.region.name", "unknown", function() return region:name() end)},
            {"x", x}, {"y", y}, {"under_siege", under_siege},
            {"abandoned", trans_diag_safe("diagnostic.region.is_abandoned", false, function() return region:is_abandoned() end)}
        })
        emitted = emitted + 1
    end
    return emitted
end

local function trans_diag_emit_wars(faction, phase, turn)
    local list, total, available = trans_diag_list("diagnostic.faction.factions_at_war_with", function() return faction:factions_at_war_with() end)
    if not available then return -1 end
    local emitted = 0
    local limit = math.min(total, TRANS_DIAG_MAX_ITEMS)
    for index = 0, limit - 1 do
        local enemy = list:item_at(index)
        trans_diag_emit("AI_WAR", {
            {"turn", turn}, {"phase", phase}, {"faction", faction:name()}, {"index", index},
            {"enemy", trans_diag_safe("diagnostic.enemy.name", "unknown", function() return enemy:name() end)}
        })
        emitted = emitted + 1
    end
    return emitted
end

local function trans_diag_emit_pending_battle()
    TRANS_DIAG_BATTLE_SEQUENCE = TRANS_DIAG_BATTLE_SEQUENCE + 1
    local battle_sequence = TRANS_DIAG_BATTLE_SEQUENCE
    local turn = trans_diag_safe("diagnostic.model.turn_number.battle", -1, function() return cm:model():turn_number() end)
    local attacker_count = trans_diag_safe(
        "diagnostic.pending_battle_cache_num_attackers",
        -1,
        function() return cm:pending_battle_cache_num_attackers() end
    )
    local defender_count = trans_diag_safe(
        "diagnostic.pending_battle_cache_num_defenders",
        -1,
        function() return cm:pending_battle_cache_num_defenders() end
    )
    trans_diag_emit("AI_BATTLE_BEGIN", {
        {"turn", turn}, {"battle_sequence", battle_sequence},
        {"attacker_count", attacker_count}, {"defender_count", defender_count}
    })

    local attackers_emitted = 0
    if attacker_count and attacker_count > 0 then
        local limit = math.min(attacker_count, TRANS_DIAG_MAX_ITEMS)
        for index = 1, limit do
            local char_cqi, force_cqi, faction_name, available = trans_diag_safe3(
                "diagnostic.pending_battle_cache_get_attacker",
                -1, -1, "unknown",
                function() return cm:pending_battle_cache_get_attacker(index) end
            )
            if available then
                trans_diag_emit("AI_BATTLE_PARTICIPANT", {
                    {"turn", turn}, {"battle_sequence", battle_sequence}, {"side", "ATTACKER"},
                    {"index", index}, {"char_cqi", char_cqi}, {"force_cqi", force_cqi}, {"faction", faction_name}
                })
                attackers_emitted = attackers_emitted + 1
            end
        end
    end

    local defenders_emitted = 0
    if defender_count and defender_count > 0 then
        local limit = math.min(defender_count, TRANS_DIAG_MAX_ITEMS)
        for index = 1, limit do
            local char_cqi, force_cqi, faction_name, available = trans_diag_safe3(
                "diagnostic.pending_battle_cache_get_defender",
                -1, -1, "unknown",
                function() return cm:pending_battle_cache_get_defender(index) end
            )
            if available then
                trans_diag_emit("AI_BATTLE_PARTICIPANT", {
                    {"turn", turn}, {"battle_sequence", battle_sequence}, {"side", "DEFENDER"},
                    {"index", index}, {"char_cqi", char_cqi}, {"force_cqi", force_cqi}, {"faction", faction_name}
                })
                defenders_emitted = defenders_emitted + 1
            end
        end
    end

    trans_diag_emit("AI_BATTLE_END", {
        {"turn", turn}, {"battle_sequence", battle_sequence},
        {"attackers_emitted", attackers_emitted}, {"defenders_emitted", defenders_emitted}
    })
end

local function trans_diag_snapshot(faction, phase)
    if not faction or faction:is_null_interface() then return end
    local turn = trans_diag_safe("diagnostic.model.turn_number", -1, function() return cm:model():turn_number() end)
    local faction_name = trans_diag_safe("diagnostic.faction.name", "unknown", function() return faction:name() end)
    trans_diag_emit("AI_SNAPSHOT_BEGIN", {{"turn", turn}, {"phase", phase}, {"faction", faction_name}})
    local forces, filtered = trans_diag_emit_forces(faction, phase, turn)
    local regions = trans_diag_emit_regions(faction, phase, turn)
    local wars = trans_diag_emit_wars(faction, phase, turn)
    trans_diag_emit("AI_SNAPSHOT_END", {
        {"turn", turn}, {"phase", phase}, {"faction", faction_name},
        {"forces_emitted", forces}, {"forces_filtered", filtered}, {"regions_emitted", regions},
        {"wars_emitted", wars}, {"item_cap", TRANS_DIAG_MAX_ITEMS}
    })
end

local function trans_diag_handle_turn(context, phase)
    local faction = context:faction()
    if not faction or faction:is_null_interface() then return end
    local faction_name = trans_diag_safe("diagnostic.faction.name", "unknown", function() return faction:name() end)
    local is_human = trans_diag_safe("diagnostic.faction.is_human", false, function() return faction:is_human() end)
    local turn = trans_diag_safe("diagnostic.model.turn_number", -1, function() return cm:model():turn_number() end)
    if is_human then
        trans_diag_emit("HUMAN_TURN_MARKER", {{"turn", turn}, {"phase", phase}, {"faction", faction_name}})
        return
    end
    -- The special campaign pseudo-faction `rebels` owns abandoned/ruin regions rather than
    -- representing a normal strategic CAI actor. Owner crash evidence from 2026-08-02 ended
    -- while enumerating this pseudo-faction's abandoned-region list. It is both unsafe and
    -- irrelevant to the intended real-faction CAI telemetry, so fail closed and skip it.
    if faction_name == "rebels" then
        trans_diag_emit("AI_FACTION_SKIPPED", {
            {"turn", turn}, {"phase", phase}, {"faction", faction_name},
            {"reason", "SPECIAL_PSEUDO_FACTION_REBELS"}
        })
        return
    end
    trans_diag_snapshot(faction, phase)
end

trans_diag_emit("PACK_LOADED", {
    {"probe_kind", TRANS_DIAG_KIND}, {"read_only", true},
    {"research_visibility", "PRIVILEGED_OMNISCIENT_DIAGNOSTIC"},
    {"application_eligible", false}, {"authority", "NO_ORDERS"},
    {"application_authority", "PROHIBITED"}, {"battle_participant_telemetry", true}, {"append_log", TRANS_DIAG_LOG}
})

trans_diag_emit("RUNTIME_BEGIN", {
    {"probe_kind", TRANS_DIAG_KIND}, {"runtime", "campaign"},
    {"research_visibility", "PRIVILEGED_OMNISCIENT_DIAGNOSTIC"},
    {"application_eligible", false}
})

core:add_listener(
    "TranscendenceNativeDiagnosticFactionTurnStart",
    "FactionTurnStart",
    true,
    function(context) trans_diag_handle_turn(context, "TURN_START") end,
    true
)

core:add_listener(
    "TranscendenceNativeDiagnosticFactionTurnEnd",
    "FactionTurnEnd",
    true,
    function(context) trans_diag_handle_turn(context, "TURN_END") end,
    true
)

core:add_listener(
    "TranscendenceNativeDiagnosticPendingBattle",
    "ScriptEventPendingBattle",
    true,
    function() trans_diag_emit_pending_battle() end,
    true
)

function transcendence_native_diagnostic_probe()
    -- Lifecycle registration occurs at file load. This function intentionally does nothing.
end
