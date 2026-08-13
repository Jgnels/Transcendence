-- Transcendence Gate 0 shadow-input observer.
-- Read-only by design: no campaign mutation, no save mutation, no randomness.
-- Foreign entities originate only from WH3's player-visibility-filtered lists.

local TRANS_PROBE_SCHEMA = 1
local TRANS_PROBE_KIND = "campaign_feasibility"
local TRANS_PROBE_PREFIX = "TRANS_PROBE"
local TRANS_PROBE_MAX_ITEMS = 64
local TRANS_PROBE_MAX_UNITS = 40
local TRANS_PROBE_RUNTIME_LOG = "transcendence_runtime_log.txt"

local function trans_probe_value(value)
    if value == nil then
        return "null"
    end
    if value == true then
        return "true"
    end
    if value == false then
        return "false"
    end
    local text = tostring(value)
    text = string.gsub(text, "%%", "%%25")
    text = string.gsub(text, "|", "%%7C")
    text = string.gsub(text, "=", "%%3D")
    text = string.gsub(text, "\r", "%%0D")
    text = string.gsub(text, "\n", "%%0A")
    return text
end

local function trans_probe_append_runtime(line)
    local opened, handle = pcall(io.open, TRANS_PROBE_RUNTIME_LOG, "a")
    if not opened or not handle then
        return false
    end
    local wrote = pcall(function()
        handle:write(line .. "\n")
        handle:flush()
        handle:close()
    end)
    return wrote
end

local function trans_probe_emit(event_name, fields)
    local parts = {
        TRANS_PROBE_PREFIX,
        tostring(TRANS_PROBE_SCHEMA),
        trans_probe_value(event_name)
    }
    if fields then
        for index = 1, #fields do
            local field = fields[index]
            parts[#parts + 1] =
                trans_probe_value(field[1]) .. "=" .. trans_probe_value(field[2])
        end
    end
    local line = table.concat(parts, "|")
    trans_probe_append_runtime(line)
    if ModLog then
        ModLog(line)
    elseif out then
        out(line)
    end
end

local function trans_probe_call(capability_name, callback, fallback)
    local ok, value = pcall(callback)
    if ok then
        return value, true
    end
    trans_probe_emit("CAPABILITY", {
        {"name", capability_name},
        {"available", false},
        {"error", value}
    })
    return fallback, false
end

local function trans_probe_safe(capability_name, fallback, callback)
    local value, available = trans_probe_call(capability_name, callback, fallback)
    return value, available
end

local function trans_probe_list(capability_name, callback)
    local list, available = trans_probe_call(capability_name, callback, nil)
    if not available or not list then
        return nil, -1, false
    end
    local count, count_available = trans_probe_call(
        capability_name .. ".num_items",
        function() return list:num_items() end,
        -1
    )
    return list, count, count_available
end

local function trans_probe_average_unit_health(force, capability_prefix)
    local units = trans_probe_safe(
        capability_prefix .. ".unit_list",
        nil,
        function() return force:unit_list() end
    )
    if not units then
        return -1, -1
    end

    local unit_count = trans_probe_safe(
        capability_prefix .. ".unit_list.num_items",
        -1,
        function() return units:num_items() end
    )
    if unit_count <= 0 then
        return unit_count, -1
    end

    local inspected = math.min(unit_count, TRANS_PROBE_MAX_UNITS)
    local sum = 0
    local valid = 0
    for unit_index = 0, inspected - 1 do
        local unit = units:item_at(unit_index)
        local health, available = trans_probe_safe(
            capability_prefix .. ".unit.percentage_proportion_of_full_strength",
            -1,
            function() return unit:percentage_proportion_of_full_strength() end
        )
        if available and health >= 0 then
            sum = sum + health
            valid = valid + 1
        end
    end

    if valid == 0 then
        return unit_count, -1
    end
    return unit_count, math.floor((sum / valid) * 100 + 0.5) / 100
end

local function trans_probe_settlement_fields(region, prefix)
    local x = -1
    local y = -1
    local settlement_level = -1
    local walled = false

    local settlement = trans_probe_safe(
        prefix .. ".settlement",
        nil,
        function() return region:settlement() end
    )
    if settlement and not settlement:is_null_interface() then
        x = trans_probe_safe(
            prefix .. ".settlement.logical_position_x",
            -1,
            function() return settlement:logical_position_x() end
        )
        y = trans_probe_safe(
            prefix .. ".settlement.logical_position_y",
            -1,
            function() return settlement:logical_position_y() end
        )
        walled = trans_probe_safe(
            prefix .. ".settlement.is_walled_settlement",
            false,
            function() return settlement:is_walled_settlement() end
        )

        local slot = trans_probe_safe(
            prefix .. ".settlement.primary_slot",
            nil,
            function() return settlement:primary_slot() end
        )
        if slot and not slot:is_null_interface() then
            local has_building = trans_probe_safe(
                prefix .. ".settlement.primary_slot.has_building",
                false,
                function() return slot:has_building() end
            )
            if has_building then
                local building = trans_probe_safe(
                    prefix .. ".settlement.primary_slot.building",
                    nil,
                    function() return slot:building() end
                )
                if building and not building:is_null_interface() then
                    settlement_level = trans_probe_safe(
                        prefix .. ".settlement.primary_building.building_level",
                        -1,
                        function() return building:building_level() end
                    )
                end
            end
        end
    end
    return x, y, settlement_level, walled
end

local function trans_probe_emit_own_armies(faction)
    local list, total, available = trans_probe_list(
        "shadow.local_faction.military_force_list",
        function() return faction:military_force_list() end
    )
    if not available then
        return -1, -1
    end

    local emitted = 0
    local filtered_nonfield = 0
    local limit = math.min(total, TRANS_PROBE_MAX_ITEMS)
    for index = 0, limit - 1 do
        local force = list:item_at(index)
        local is_garrison = trans_probe_safe(
            "shadow.own_force.is_armed_citizenry",
            true,
            function() return force:is_armed_citizenry() end
        )
        local is_army = trans_probe_safe(
            "shadow.own_force.is_army",
            false,
            function() return force:is_army() end
        )
        local has_general = trans_probe_safe(
            "shadow.own_force.has_general",
            false,
            function() return force:has_general() end
        )

        if not is_garrison and has_general then
            local force_cqi = trans_probe_safe(
                "shadow.own_force.command_queue_index",
                -1,
                function() return force:command_queue_index() end
            )
            local force_strength = trans_probe_safe(
                "shadow.own_force.strength",
                -1,
                function() return force:strength() end
            )
            local stance = trans_probe_safe(
                "shadow.own_force.active_stance",
                "unknown",
                function() return force:active_stance() end
            )
            local unit_count, average_unit_health_pct =
                trans_probe_average_unit_health(force, "shadow.own_force")

            local general = trans_probe_safe(
                "shadow.own_force.general_character",
                nil,
                function() return force:general_character() end
            )
            local general_cqi = -1
            local subtype = "unknown"
            local character_type_key = "unknown"
            local x = -1
            local y = -1
            local region_name = "none"
            local movement_remaining_pct = -1
            local action_points_per_turn = -1

            if general and not general:is_null_interface() then
                general_cqi = trans_probe_safe(
                    "shadow.own_general.command_queue_index",
                    -1,
                    function() return general:command_queue_index() end
                )
                subtype = trans_probe_safe(
                    "shadow.own_general.character_subtype_key",
                    "unknown",
                    function() return general:character_subtype_key() end
                )
                character_type_key = trans_probe_safe(
                    "shadow.own_general.character_type_key",
                    "unknown",
                    function() return general:character_type_key() end
                )
                x = trans_probe_safe(
                    "shadow.own_general.logical_position_x",
                    -1,
                    function() return general:logical_position_x() end
                )
                y = trans_probe_safe(
                    "shadow.own_general.logical_position_y",
                    -1,
                    function() return general:logical_position_y() end
                )
                movement_remaining_pct = trans_probe_safe(
                    "shadow.own_general.action_points_remaining_percent",
                    -1,
                    function() return general:action_points_remaining_percent() end
                )
                action_points_per_turn = trans_probe_safe(
                    "shadow.own_general.action_points_per_turn",
                    -1,
                    function() return general:action_points_per_turn() end
                )
                local region = trans_probe_safe(
                    "shadow.own_general.region",
                    nil,
                    function() return general:region() end
                )
                if region and not region:is_null_interface() then
                    region_name = trans_probe_safe(
                        "shadow.own_general.region.name",
                        "unknown",
                        function() return region:name() end
                    )
                end
            end

            local planner_eligible =
                is_army and character_type_key == "general" and unit_count > 0

            if planner_eligible then
                trans_probe_emit("SHADOW_ARMY", {
                    {"index", index},
                    {"force_cqi", force_cqi},
                    {"general_cqi", general_cqi},
                    {"subtype", subtype},
                    {"character_type_key", character_type_key},
                    {"is_army", is_army},
                    {"planner_eligible", true},
                    {"unit_count", unit_count},
                    {"force_strength", force_strength},
                    {"average_unit_health_pct", average_unit_health_pct},
                    {"movement_remaining_pct", movement_remaining_pct},
                    {"action_points_per_turn", action_points_per_turn},
                    {"stance", stance},
                    {"x", x},
                    {"y", y},
                    {"region", region_name}
                })
                emitted = emitted + 1
            else
                trans_probe_emit("SHADOW_FILTERED_FORCE", {
                    {"scope", "OWN"},
                    {"index", index},
                    {"force_cqi", force_cqi},
                    {"general_cqi", general_cqi},
                    {"subtype", subtype},
                    {"character_type_key", character_type_key},
                    {"is_army", is_army},
                    {"unit_count", unit_count},
                    {"reason", "NONFIELD_CHARACTER_OR_FORCE"}
                })
                filtered_nonfield = filtered_nonfield + 1
            end
        end
    end
    return emitted, filtered_nonfield
end

local function trans_probe_emit_visible_armies(faction)
    local list, total, available = trans_probe_list(
        "shadow.local_faction.get_foreign_visible_characters_for_player",
        function() return faction:get_foreign_visible_characters_for_player() end
    )
    if not available then
        return -1, false, -1
    end

    local emitted = 0
    local filtered_nonfield = 0
    local limit = math.min(total, TRANS_PROBE_MAX_ITEMS)
    for index = 0, limit - 1 do
        local character = list:item_at(index)
        local has_force = trans_probe_safe(
            "shadow.visible_character.has_military_force",
            false,
            function() return character:has_military_force() end
        )
        if has_force then
            local force = trans_probe_safe(
                "shadow.visible_character.military_force",
                nil,
                function() return character:military_force() end
            )
            local unit_count = -1
            local force_cqi = -1
            local is_army = false
            if force and not force:is_null_interface() then
                is_army = trans_probe_safe(
                    "shadow.visible_force.is_army",
                    false,
                    function() return force:is_army() end
                )
                local units = trans_probe_safe(
                    "shadow.visible_force.unit_list",
                    nil,
                    function() return force:unit_list() end
                )
                if units then
                    unit_count = trans_probe_safe(
                        "shadow.visible_force.unit_list.num_items",
                        -1,
                        function() return units:num_items() end
                    )
                end
                force_cqi = trans_probe_safe(
                    "shadow.visible_force.command_queue_index",
                    -1,
                    function() return force:command_queue_index() end
                )
            end

            local faction_name = trans_probe_safe(
                "shadow.visible_character.faction.name",
                "unknown",
                function() return character:faction():name() end
            )
            local character_cqi = trans_probe_safe(
                "shadow.visible_character.command_queue_index",
                -1,
                function() return character:command_queue_index() end
            )
            local subtype = trans_probe_safe(
                "shadow.visible_character.character_subtype_key",
                "unknown",
                function() return character:character_subtype_key() end
            )
            local character_type_key = trans_probe_safe(
                "shadow.visible_character.character_type_key",
                "unknown",
                function() return character:character_type_key() end
            )
            local planner_eligible =
                is_army and character_type_key == "general" and unit_count > 0

            if planner_eligible then
                trans_probe_emit("SHADOW_VISIBLE_ARMY", {
                    {"index", index},
                    {"faction", faction_name},
                    {"character_cqi", character_cqi},
                    {"force_cqi", force_cqi},
                    {"subtype", subtype},
                    {"character_type_key", character_type_key},
                    {"is_army", is_army},
                    {"planner_eligible", true},
                    {"unit_count", unit_count},
                    {"x", trans_probe_safe(
                        "shadow.visible_character.logical_position_x",
                        -1,
                        function() return character:logical_position_x() end
                    )},
                    {"y", trans_probe_safe(
                        "shadow.visible_character.logical_position_y",
                        -1,
                        function() return character:logical_position_y() end
                    )},
                    {"strength_source", "VISIBLE_UNIT_COUNT_PROXY"}
                })
                emitted = emitted + 1
            else
                trans_probe_emit("SHADOW_FILTERED_FORCE", {
                    {"scope", "VISIBLE_FOREIGN"},
                    {"index", index},
                    {"faction", faction_name},
                    {"character_cqi", character_cqi},
                    {"force_cqi", force_cqi},
                    {"subtype", subtype},
                    {"character_type_key", character_type_key},
                    {"is_army", is_army},
                    {"unit_count", unit_count},
                    {"reason", "NONFIELD_CHARACTER_OR_FORCE"}
                })
                filtered_nonfield = filtered_nonfield + 1
            end
        end
    end
    return emitted, true, filtered_nonfield
end

local function trans_probe_emit_own_regions(faction)
    local list, total, available = trans_probe_list(
        "shadow.local_faction.region_list",
        function() return faction:region_list() end
    )
    if not available then
        return -1
    end

    local emitted = 0
    local limit = math.min(total, TRANS_PROBE_MAX_ITEMS)
    for index = 0, limit - 1 do
        local region = list:item_at(index)
        local name = trans_probe_safe(
            "shadow.own_region.name",
            "unknown",
            function() return region:name() end
        )
        local x, y, settlement_level, walled =
            trans_probe_settlement_fields(region, "shadow.own_region")
        local under_siege = false
        local garrison_unit_count = -1
        local garrison_strength = -1
        local garrison_force_is_armed_citizenry = false
        local garrison_source = "SETTLEMENT_STRUCTURE_PROXY_ONLY"
        local residence = trans_probe_safe(
            "shadow.own_region.garrison_residence",
            nil,
            function() return region:garrison_residence() end
        )
        if residence and not residence:is_null_interface() then
            under_siege = trans_probe_safe(
                "shadow.own_region.garrison_residence.is_under_siege",
                false,
                function() return residence:is_under_siege() end
            )
            local army = trans_probe_safe(
                "shadow.own_region.garrison_residence.army",
                nil,
                function() return residence:army() end
            )
            if army and not army:is_null_interface() then
                garrison_force_is_armed_citizenry = trans_probe_safe(
                    "shadow.own_region.garrison_residence.army.is_armed_citizenry",
                    false,
                    function() return army:is_armed_citizenry() end
                )
                if garrison_force_is_armed_citizenry then
                    local units = trans_probe_safe(
                        "shadow.own_region.garrison_residence.army.unit_list",
                        nil,
                        function() return army:unit_list() end
                    )
                    if units then
                        garrison_unit_count = trans_probe_safe(
                            "shadow.own_region.garrison_residence.army.unit_list.num_items",
                            -1,
                            function() return units:num_items() end
                        )
                    end
                    garrison_strength = trans_probe_safe(
                        "shadow.own_region.garrison_residence.army.strength",
                        -1,
                        function() return army:strength() end
                    )
                    garrison_source = "ARMED_CITIZENRY_FORCE"
                else
                    garrison_source = "FIELD_ARMY_EXCLUDED_USE_STRUCTURE_PROXY"
                end
            end
        end

        trans_probe_emit("SHADOW_OWN_REGION", {
            {"index", index},
            {"region", name},
            {"owner", faction:name()},
            {"abandoned", trans_probe_safe(
                "shadow.own_region.is_abandoned",
                false,
                function() return region:is_abandoned() end
            )},
            {"x", x},
            {"y", y},
            {"settlement_level", settlement_level},
            {"walled", walled},
            {"under_siege", under_siege},
            {"garrison_unit_count", garrison_unit_count},
            {"garrison_strength", garrison_strength},
            {"garrison_force_is_armed_citizenry", garrison_force_is_armed_citizenry},
            {"garrison_source", garrison_source}
        })
        emitted = emitted + 1
    end
    return emitted
end

local function trans_probe_emit_visible_regions(faction)
    local list, total, available = trans_probe_list(
        "shadow.local_faction.get_foreign_visible_regions_for_player",
        function() return faction:get_foreign_visible_regions_for_player() end
    )
    if not available then
        return -1, false
    end

    local emitted = 0
    local limit = math.min(total, TRANS_PROBE_MAX_ITEMS)
    for index = 0, limit - 1 do
        local region = list:item_at(index)
        local x, y, settlement_level, walled =
            trans_probe_settlement_fields(region, "shadow.visible_region")
        local under_siege = false
        local residence = trans_probe_safe(
            "shadow.visible_region.garrison_residence",
            nil,
            function() return region:garrison_residence() end
        )
        if residence and not residence:is_null_interface() then
            under_siege = trans_probe_safe(
                "shadow.visible_region.garrison_residence.is_under_siege",
                false,
                function() return residence:is_under_siege() end
            )
        end

        trans_probe_emit("SHADOW_VISIBLE_REGION", {
            {"index", index},
            {"region", trans_probe_safe(
                "shadow.visible_region.name",
                "unknown",
                function() return region:name() end
            )},
            {"owner", trans_probe_safe(
                "shadow.visible_region.owning_faction.name",
                "unknown",
                function() return region:owning_faction():name() end
            )},
            {"abandoned", trans_probe_safe(
                "shadow.visible_region.is_abandoned",
                false,
                function() return region:is_abandoned() end
            )},
            {"x", x},
            {"y", y},
            {"settlement_level", settlement_level},
            {"walled", walled},
            {"under_siege", under_siege},
            {"garrison_source", "SETTLEMENT_STRUCTURE_PROXY_ONLY"}
        })
        emitted = emitted + 1
    end
    return emitted, true
end

local function trans_probe_emit_wars(faction)
    local list, total, available = trans_probe_list(
        "shadow.local_faction.factions_at_war_with",
        function() return faction:factions_at_war_with() end
    )
    if not available then
        return -1
    end

    local emitted = 0
    local limit = math.min(total, TRANS_PROBE_MAX_ITEMS)
    for index = 0, limit - 1 do
        local enemy = list:item_at(index)
        trans_probe_emit("WAR", {
            {"index", index},
            {"faction_a", faction:name()},
            {"faction_b", trans_probe_safe(
                "shadow.war_faction.name",
                "unknown",
                function() return enemy:name() end
            )}
        })
        emitted = emitted + 1
    end
    return emitted
end

local function trans_probe_emit_shadow_snapshot(faction, snapshot_reason)
    local reason = snapshot_reason or "LOCAL_FACTION_TURN_START"
    if not faction or faction:is_null_interface() then
        trans_probe_emit("ERROR", {
            {"stage", "shadow_snapshot"},
            {"reason", "null_local_faction"}
        })
        return
    end

    local turn = trans_probe_safe(
        "shadow.model.turn_number",
        -1,
        function() return cm:model():turn_number() end
    )
    local local_faction = trans_probe_safe(
        "shadow.local_faction.name",
        "unknown",
        function() return faction:name() end
    )

    trans_probe_emit("SNAPSHOT_BEGIN", {
        {"reason", reason},
        {"turn", turn},
        {"local_faction", local_faction}
    })

    local own_armies, own_nonfield_forces_filtered =
        trans_probe_emit_own_armies(faction)
    local visible_armies, visible_armies_available, visible_nonfield_forces_filtered =
        trans_probe_emit_visible_armies(faction)
    local own_regions = trans_probe_emit_own_regions(faction)
    local visible_regions, visible_regions_available =
        trans_probe_emit_visible_regions(faction)
    local wars = trans_probe_emit_wars(faction)

    trans_probe_emit("SNAPSHOT_END", {
        {"reason", reason},
        {"turn", turn},
        {"local_faction", local_faction},
        {"own_armies_emitted", own_armies},
        {"own_nonfield_forces_filtered", own_nonfield_forces_filtered},
        {"visible_armies_emitted", visible_armies},
        {"visible_armies_available", visible_armies_available},
        {"visible_nonfield_forces_filtered", visible_nonfield_forces_filtered},
        {"own_regions_emitted", own_regions},
        {"visible_regions_emitted", visible_regions},
        {"visible_regions_available", visible_regions_available},
        {"wars_emitted", wars},
        {"item_cap", TRANS_PROBE_MAX_ITEMS}
    })
end

local function trans_probe_first_tick()
    local local_faction_name = trans_probe_safe(
        "feasibility.campaign_manager.get_local_faction_name",
        "unknown",
        function() return cm:get_local_faction_name(true) end
    )
    trans_probe_emit("FIRST_TICK", {
        {"probe_kind", TRANS_PROBE_KIND},
        {"campaign", trans_probe_safe(
            "feasibility.model.campaign_name_key",
            "unknown",
            function() return cm:model():campaign_name_key() end
        )},
        {"turn", trans_probe_safe(
            "feasibility.model.turn_number",
            -1,
            function() return cm:model():turn_number() end
        )},
        {"local_faction", local_faction_name},
        {"is_new_game", trans_probe_safe(
            "feasibility.campaign_manager.is_new_game",
            false,
            function() return cm:is_new_game() end
        )},
        {"is_multiplayer", trans_probe_safe(
            "feasibility.model.is_multiplayer",
            false,
            function() return cm:model():is_multiplayer() end
        )}
    })

    -- Capture the loaded current state immediately. This avoids requiring the
    -- owner to end a turn merely to create a query plan. It is still a read-only
    -- observer snapshot and is distinguished from a true turn-start snapshot.
    local faction = trans_probe_safe(
        "feasibility.world.faction_by_key",
        nil,
        function() return cm:model():world():faction_by_key(local_faction_name) end
    )
    if faction and not faction:is_null_interface() then
        trans_probe_emit_shadow_snapshot(faction, "LOCAL_FACTION_FIRST_TICK")
    end
end

trans_probe_emit("PACK_LOADED", {
    {"probe_kind", TRANS_PROBE_KIND},
    {"script", "transcendence_campaign_feasibility_probe"},
    {"read_only", true},
    {"foreign_visibility_source", "WH3_PLAYER_FILTERED_LISTS"},
    {"append_log", TRANS_PROBE_RUNTIME_LOG}
})

trans_probe_emit("RUNTIME_BEGIN", {
    {"probe_kind", TRANS_PROBE_KIND},
    {"runtime", "campaign"},
    {"append_log", TRANS_PROBE_RUNTIME_LOG}
})

cm:add_first_tick_callback_sp_each(trans_probe_first_tick)

core:add_listener(
    "TranscendenceCampaignFeasibilityProbeFactionTurnStart",
    "FactionTurnStart",
    function(context)
        local local_faction_name = cm:get_local_faction_name(true)
        return local_faction_name and context:faction():name() == local_faction_name
    end,
    function(context)
        trans_probe_emit_shadow_snapshot(context:faction())
    end,
    true
)


-- v0.2I read-only dynamic feasibility request executor.
-- Request files are project-generated from the exact current observer-safe
-- snapshot and v0.2E/v0.2F/v0.2G/v0.2H deterministic pipeline. Only the
-- whitelisted read/query surfaces below can be invoked.
local TRANS_FEAS_REQUEST_FILE = "transcendence_campaign_feasibility_request.txt"
local TRANS_FEAS_MAX_QUERIES = 16
local TRANS_FEAS_COMPLETED = {}
local TRANS_FEAS_LAST_PLAN = nil
local TRANS_FEAS_POLL_TICK_EMITTED = false
local TRANS_FEAS_SEEN_PLAN = nil

local function trans_feas_decode(value)
    local result = value or ""
    result = string.gsub(result, "%%0A", "\\n")
    result = string.gsub(result, "%%0D", "\\r")
    result = string.gsub(result, "%%3D", "=")
    result = string.gsub(result, "%%7C", "|")
    result = string.gsub(result, "%%25", "%%")
    return result
end

local function trans_feas_parse_fields(parts, first_index)
    local fields = {}
    for index = first_index, #parts do
        local item = parts[index]
        local split = string.find(item, "=", 1, true)
        if not split then
            return nil
        end
        local key = trans_feas_decode(string.sub(item, 1, split - 1))
        local value = trans_feas_decode(string.sub(item, split + 1))
        if fields[key] ~= nil then
            return nil
        end
        fields[key] = value
    end
    return fields
end

local function trans_feas_read_request()
    local opened, handle = pcall(io.open, TRANS_FEAS_REQUEST_FILE, "r")
    if not opened or not handle then
        return nil
    end
    local lines = {}
    for line in handle:lines() do
        lines[#lines + 1] = line
    end
    handle:close()
    if #lines < 2 then
        return nil
    end

    local header_parts = {}
    for part in string.gmatch(lines[1], "([^|]+)") do
        header_parts[#header_parts + 1] = part
    end
    if #header_parts < 4 or header_parts[1] ~= "TRANS_FEAS_REQ" or header_parts[2] ~= "1" or header_parts[3] ~= "REQUEST" then
        return nil
    end
    local header = trans_feas_parse_fields(header_parts, 4)
    if not header then
        return nil
    end
    if not header.plan_digest or not header.scenario_id or not header.turn or not header.assignment_id then
        return nil
    end
    if header.authority ~= "NO_ORDERS" or header.application_authority ~= "PROHIBITED" then
        return {header = header, queries = {}, rejected_reason = "AUTHORITY_MISMATCH"}
    end
    local expected_count = tonumber(header.query_count or "-1")
    if not expected_count or expected_count < 1 or expected_count > TRANS_FEAS_MAX_QUERIES or expected_count ~= (#lines - 1) then
        return nil
    end

    local queries = {}
    local seen = {}
    for line_index = 2, #lines do
        local parts = {}
        for part in string.gmatch(lines[line_index], "([^|]+)") do
            parts[#parts + 1] = part
        end
        if #parts < 4 or parts[1] ~= "TRANS_FEAS_REQ" or parts[2] ~= "1" or parts[3] ~= "QUERY" then
            return nil
        end
        local fields = trans_feas_parse_fields(parts, 4)
        if not fields or fields.plan_digest ~= header.plan_digest or not fields.query_id or not fields.query_key then
            return nil
        end
        if seen[fields.query_id] then
            return nil
        end
        seen[fields.query_id] = true
        queries[#queries + 1] = fields
    end
    return {header = header, queries = queries}
end

local function trans_feas_number(fields, key)
    local value = tonumber(fields[key] or "")
    if not value then
        error("missing numeric request parameter: " .. key)
    end
    return value
end

local function trans_feas_character(model, character_cqi)
    local character = model:character_for_command_queue_index(character_cqi)
    if not character or character:is_null_interface() then
        return nil
    end
    return character
end

local function trans_feas_force(model, force_cqi)
    local force = model:military_force_for_command_queue_index(force_cqi)
    if not force or force:is_null_interface() then
        return nil
    end
    return force
end

local function trans_feas_region(model, region_key)
    local world = model:world()
    if not world or world:is_null_interface() then
        return nil
    end
    local manager = world:region_manager()
    if not manager or manager:is_null_interface() then
        return nil
    end
    local region = manager:region_by_key(region_key)
    if not region or region:is_null_interface() then
        return nil
    end
    return region
end

local function trans_feas_execute(fields)
    local model = cm:model()
    local key = fields.query_key
    if key == "MODEL_HAS_CHARACTER_CQI" then
        return model:has_character_command_queue_index(trans_feas_number(fields, "character_cqi"))
    elseif key == "MODEL_CHARACTER_FROM_CQI" then
        return trans_feas_character(model, trans_feas_number(fields, "character_cqi")) ~= nil
    elseif key == "MODEL_HAS_FORCE_CQI" then
        return model:has_military_force_command_queue_index(trans_feas_number(fields, "force_cqi"))
    elseif key == "MODEL_FORCE_FROM_CQI" then
        return trans_feas_force(model, trans_feas_number(fields, "force_cqi")) ~= nil
    elseif key == "FORCE_ACTIVE_STANCE" then
        local force = trans_feas_force(model, trans_feas_number(fields, "force_cqi"))
        if not force then error("force lookup failed") end
        return force:active_stance()
    elseif key == "POSITION_REACHABLE_THIS_TURN" then
        local character = trans_feas_character(model, trans_feas_number(fields, "character_cqi"))
        if not character then error("character lookup failed") end
        return model:character_can_reach_position(character, trans_feas_number(fields, "x"), trans_feas_number(fields, "y"))
    elseif key == "POSITION_REACHABLE_THIS_TURN_IN_STANCE" then
        local character = trans_feas_character(model, trans_feas_number(fields, "character_cqi"))
        if not character then error("character lookup failed") end
        local stance = fields.stance
        if not stance or stance == "" then error("stance missing") end
        return model:character_can_reach_position_in_stance(character, trans_feas_number(fields, "x"), trans_feas_number(fields, "y"), stance)
    elseif key == "POSITION_EVER_REACHABLE" then
        local character = trans_feas_character(model, trans_feas_number(fields, "character_cqi"))
        if not character then error("character lookup failed") end
        return model:character_can_ever_reach_position(character, trans_feas_number(fields, "x"), trans_feas_number(fields, "y"))
    elseif key == "REGION_SETTLEMENT_INTERFACE" then
        local region = trans_feas_region(model, fields.region_key or "")
        if not region then return false end
        local settlement = region:settlement()
        return settlement ~= nil and not settlement:is_null_interface()
    elseif key == "SETTLEMENT_REACHABLE_THIS_TURN" then
        local character = trans_feas_character(model, trans_feas_number(fields, "character_cqi"))
        local region = trans_feas_region(model, fields.region_key or "")
        if not character or not region then error("character or region lookup failed") end
        local settlement = region:settlement()
        if not settlement or settlement:is_null_interface() then error("settlement lookup failed") end
        return model:character_can_reach_settlement(character, settlement)
    elseif key == "SETTLEMENT_REACHABLE_THIS_TURN_IN_STANCE" then
        local character = trans_feas_character(model, trans_feas_number(fields, "character_cqi"))
        local region = trans_feas_region(model, fields.region_key or "")
        if not character or not region then error("character or region lookup failed") end
        local settlement = region:settlement()
        if not settlement or settlement:is_null_interface() then error("settlement lookup failed") end
        local stance = fields.stance
        if not stance or stance == "" then error("stance missing") end
        return model:character_can_reach_settlement_in_stance(character, settlement, stance)
    elseif key == "SETTLEMENT_EVER_REACHABLE" then
        local character = trans_feas_character(model, trans_feas_number(fields, "character_cqi"))
        local region = trans_feas_region(model, fields.region_key or "")
        if not character or not region then error("character or region lookup failed") end
        local settlement = region:settlement()
        if not settlement or settlement:is_null_interface() then error("settlement lookup failed") end
        return model:character_can_ever_reach_settlement(character, settlement)
    elseif key == "GARRISON_UNDER_SIEGE" then
        local region = trans_feas_region(model, fields.region_key or "")
        if not region then error("region lookup failed") end
        local residence = region:garrison_residence()
        if not residence or residence:is_null_interface() then error("garrison residence lookup failed") end
        return residence:is_under_siege()
    end
    error("query key is not in the v0.2I read-only whitelist")
end

local function trans_feas_poll()
    if not TRANS_FEAS_POLL_TICK_EMITTED then
        trans_probe_emit("FEASIBILITY_POLL_TICK", {
            {"timer_kind", "REAL_UI_TIMER"},
            {"orders_emitted", false},
            {"save_values_written", false},
            {"read_only", true}
        })
        TRANS_FEAS_POLL_TICK_EMITTED = true
    end
    local request = trans_feas_read_request()
    if not request then
        return
    end
    local header = request.header
    if request.rejected_reason then
        if TRANS_FEAS_LAST_PLAN ~= header.plan_digest then
            trans_probe_emit("FEASIBILITY_REQUEST_REJECTED", {
                {"plan_digest", header.plan_digest},
                {"reason", request.rejected_reason},
                {"request_turn", header.turn}
            })
            TRANS_FEAS_LAST_PLAN = header.plan_digest
            cm:remove_real_callback("TranscendenceCampaignFeasibilityReadOnlyPoll")
        end
        return
    end
    local current_turn = trans_probe_safe(
        "feasibility.model.turn_number",
        -1,
        function() return cm:model():turn_number() end
    )
    if tostring(current_turn) ~= tostring(header.turn) then
        if TRANS_FEAS_LAST_PLAN ~= header.plan_digest then
            trans_probe_emit("FEASIBILITY_REQUEST_REJECTED", {
                {"plan_digest", header.plan_digest},
                {"reason", "TURN_MISMATCH"},
                {"request_turn", header.turn},
                {"current_turn", current_turn}
            })
            TRANS_FEAS_LAST_PLAN = header.plan_digest
            cm:remove_real_callback("TranscendenceCampaignFeasibilityReadOnlyPoll")
        end
        return
    end

    if TRANS_FEAS_SEEN_PLAN ~= header.plan_digest then
        trans_probe_emit("FEASIBILITY_REQUEST_SEEN", {
            {"plan_digest", header.plan_digest},
            {"turn", header.turn},
            {"query_count", #request.queries},
            {"orders_emitted", false},
            {"save_values_written", false},
            {"read_only", true}
        })
        TRANS_FEAS_SEEN_PLAN = header.plan_digest
    end

    local completed_now = 0
    for index = 1, #request.queries do
        local fields = request.queries[index]
        if not TRANS_FEAS_COMPLETED[fields.query_id] then
            local ok, value = pcall(function() return trans_feas_execute(fields) end)
            local emitted_value = nil
            if ok then
                -- Preserve boolean false as a real observed value. Lua's
                -- a boolean-coalescing idiom would collapse false to nil.
                emitted_value = value
            end
            trans_probe_emit("FEASIBILITY_QUERY_RESULT", {
                {"plan_digest", header.plan_digest},
                {"scenario_id", header.scenario_id},
                {"turn", header.turn},
                {"assignment_id", header.assignment_id},
                {"query_id", fields.query_id},
                {"query_key", fields.query_key},
                {"observed", ok},
                {"value", emitted_value},
                {"read_only", true}
            })
            TRANS_FEAS_COMPLETED[fields.query_id] = true
            completed_now = completed_now + 1
        end
    end

    local total_completed = 0
    for index = 1, #request.queries do
        if TRANS_FEAS_COMPLETED[request.queries[index].query_id] then
            total_completed = total_completed + 1
        end
    end
    if total_completed == #request.queries and TRANS_FEAS_LAST_PLAN ~= header.plan_digest then
        trans_probe_emit("FEASIBILITY_PACKET_END", {
            {"plan_digest", header.plan_digest},
            {"scenario_id", header.scenario_id},
            {"turn", header.turn},
            {"assignment_id", header.assignment_id},
            {"query_count", #request.queries},
            {"orders_emitted", false},
            {"save_values_written", false},
            {"read_only", true}
        })
        TRANS_FEAS_LAST_PLAN = header.plan_digest
        cm:remove_real_callback("TranscendenceCampaignFeasibilityReadOnlyPoll")
    end
end

local function trans_feas_start_polling()
    trans_probe_emit("FEASIBILITY_EXECUTOR_READY", {
        {"request_file", "RELATIVE_GAME_ROOT_REQUEST_FILE"},
        {"maximum_queries", TRANS_FEAS_MAX_QUERIES},
        {"orders_emitted", false},
        {"save_values_written", false},
        {"read_only", true}
    })
    -- The owner-runtime v0.2I limiting observation showed that a model-time
    -- repeat callback can remain dormant while the campaign map is idle.
    -- Poll once immediately, then use a UI-synchronised real timer so the
    -- read-only request can execute without requiring a turn advance or order.
    trans_feas_poll()
    cm:repeat_real_callback(trans_feas_poll, 250, "TranscendenceCampaignFeasibilityReadOnlyPoll")
end

cm:add_post_first_tick_callback(trans_feas_start_polling)

function transcendence_campaign_feasibility_probe()
    -- Lifecycle registration occurs at file load.
end
