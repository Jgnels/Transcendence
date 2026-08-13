-- Transcendence Gate 0 shadow-input observer.
-- Read-only by design: no campaign mutation, no save mutation, no randomness.
-- Foreign entities originate only from WH3's player-visibility-filtered lists.

local TRANS_PROBE_SCHEMA = 1
local TRANS_PROBE_KIND = "shadow"
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

local function trans_probe_emit_shadow_snapshot(faction)
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
        {"reason", "LOCAL_FACTION_TURN_START"},
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
        {"reason", "LOCAL_FACTION_TURN_START"},
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
    trans_probe_emit("FIRST_TICK", {
        {"probe_kind", TRANS_PROBE_KIND},
        {"campaign", trans_probe_safe(
            "shadow.model.campaign_name_key",
            "unknown",
            function() return cm:model():campaign_name_key() end
        )},
        {"turn", trans_probe_safe(
            "shadow.model.turn_number",
            -1,
            function() return cm:model():turn_number() end
        )},
        {"local_faction", trans_probe_safe(
            "shadow.campaign_manager.get_local_faction_name",
            "unknown",
            function() return cm:get_local_faction_name(true) end
        )},
        {"is_new_game", trans_probe_safe(
            "shadow.campaign_manager.is_new_game",
            false,
            function() return cm:is_new_game() end
        )},
        {"is_multiplayer", trans_probe_safe(
            "shadow.model.is_multiplayer",
            false,
            function() return cm:model():is_multiplayer() end
        )}
    })
end

trans_probe_emit("PACK_LOADED", {
    {"probe_kind", TRANS_PROBE_KIND},
    {"script", "transcendence_shadow_probe"},
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
    "TranscendenceShadowProbeFactionTurnStart",
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

function transcendence_shadow_probe()
    -- Lifecycle registration occurs at file load.
end
