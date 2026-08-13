-- Transcendence Gate 0 campaign observer probe.
-- Read-only by design: this file does not mutate campaign state or save data.

local TRANS_PROBE_SCHEMA = 1
local TRANS_PROBE_KIND = "observer"
local TRANS_PROBE_PREFIX = "TRANS_PROBE"
local TRANS_PROBE_MAX_ITEMS = 64

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

local function trans_probe_emit(event_name, fields)
    local parts = {
        TRANS_PROBE_PREFIX,
        tostring(TRANS_PROBE_SCHEMA),
        trans_probe_value(event_name)
    }

    if fields then
        for index = 1, #fields do
            local field = fields[index]
            parts[#parts + 1] = trans_probe_value(field[1]) .. "=" .. trans_probe_value(field[2])
        end
    end

    local line = table.concat(parts, "|")
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

local function trans_probe_list_count(capability_name, callback)
    local list, available = trans_probe_call(capability_name, callback, nil)
    if not available or not list then
        return -1, nil, false
    end

    local count, count_available = trans_probe_call(
        capability_name .. ".num_items",
        function() return list:num_items() end,
        -1
    )
    return count, list, count_available
end

local function trans_probe_safe_method(capability_name, fallback, callback)
    local value, available = trans_probe_call(capability_name, callback, fallback)
    return value, available
end

local function trans_probe_emit_own_armies(faction)
    local total, force_list, available = trans_probe_list_count(
        "local_faction.military_force_list",
        function() return faction:military_force_list() end
    )
    if not available then
        return -1, -1
    end

    local emitted = 0
    local field_forces = 0
    local limit = math.min(total, TRANS_PROBE_MAX_ITEMS)

    for index = 0, limit - 1 do
        local force = force_list:item_at(index)
        local is_garrison = trans_probe_safe_method(
            "military_force.is_armed_citizenry",
            true,
            function() return force:is_armed_citizenry() end
        )
        local has_general = trans_probe_safe_method(
            "military_force.has_general",
            false,
            function() return force:has_general() end
        )

        if not is_garrison and has_general then
            field_forces = field_forces + 1
            local force_cqi = trans_probe_safe_method(
                "military_force.command_queue_index",
                -1,
                function() return force:command_queue_index() end
            )
            local unit_count = -1
            local unit_list = trans_probe_safe_method(
                "military_force.unit_list",
                nil,
                function() return force:unit_list() end
            )
            if unit_list then
                unit_count = trans_probe_safe_method(
                    "military_force.unit_list.num_items",
                    -1,
                    function() return unit_list:num_items() end
                )
            end

            local general = trans_probe_safe_method(
                "military_force.general_character",
                nil,
                function() return force:general_character() end
            )
            local general_cqi = -1
            local subtype = "unknown"
            local x = -1
            local y = -1
            local region = "none"
            if general then
                general_cqi = trans_probe_safe_method(
                    "character.command_queue_index",
                    -1,
                    function() return general:command_queue_index() end
                )
                subtype = trans_probe_safe_method(
                    "character.character_subtype_key",
                    "unknown",
                    function() return general:character_subtype_key() end
                )
                x = trans_probe_safe_method(
                    "character.logical_position_x",
                    -1,
                    function() return general:logical_position_x() end
                )
                y = trans_probe_safe_method(
                    "character.logical_position_y",
                    -1,
                    function() return general:logical_position_y() end
                )
                local character_region = trans_probe_safe_method(
                    "character.region",
                    nil,
                    function() return general:region() end
                )
                if character_region and not character_region:is_null_interface() then
                    region = trans_probe_safe_method(
                        "region.name",
                        "unknown",
                        function() return character_region:name() end
                    )
                end
            end

            trans_probe_emit("OWN_ARMY", {
                {"index", index},
                {"force_cqi", force_cqi},
                {"general_cqi", general_cqi},
                {"subtype", subtype},
                {"unit_count", unit_count},
                {"x", x},
                {"y", y},
                {"region", region}
            })
            emitted = emitted + 1
        end
    end

    return total, emitted
end

local function trans_probe_emit_own_regions(faction)
    local total, region_list, available = trans_probe_list_count(
        "local_faction.region_list",
        function() return faction:region_list() end
    )
    if not available then
        return -1, -1
    end

    local emitted = 0
    local limit = math.min(total, TRANS_PROBE_MAX_ITEMS)
    for index = 0, limit - 1 do
        local region = region_list:item_at(index)
        local region_name = trans_probe_safe_method(
            "region.name",
            "unknown",
            function() return region:name() end
        )
        local abandoned = trans_probe_safe_method(
            "region.is_abandoned",
            false,
            function() return region:is_abandoned() end
        )
        local x = -1
        local y = -1
        local settlement = trans_probe_safe_method(
            "region.settlement",
            nil,
            function() return region:settlement() end
        )
        if settlement and not settlement:is_null_interface() then
            x = trans_probe_safe_method(
                "settlement.logical_position_x",
                -1,
                function() return settlement:logical_position_x() end
            )
            y = trans_probe_safe_method(
                "settlement.logical_position_y",
                -1,
                function() return settlement:logical_position_y() end
            )
        end

        trans_probe_emit("OWN_REGION", {
            {"index", index},
            {"region", region_name},
            {"abandoned", abandoned},
            {"x", x},
            {"y", y}
        })
        emitted = emitted + 1
    end
    return total, emitted
end

local function trans_probe_emit_visible_characters(faction)
    local total, character_list, available = trans_probe_list_count(
        "local_faction.get_foreign_visible_characters_for_player",
        function() return faction:get_foreign_visible_characters_for_player() end
    )
    if not available then
        return -1, -1, false
    end

    local emitted = 0
    local limit = math.min(total, TRANS_PROBE_MAX_ITEMS)
    for index = 0, limit - 1 do
        local character = character_list:item_at(index)
        local foreign_faction = trans_probe_safe_method(
            "visible_character.faction.name",
            "unknown",
            function() return character:faction():name() end
        )
        local character_cqi = trans_probe_safe_method(
            "visible_character.command_queue_index",
            -1,
            function() return character:command_queue_index() end
        )
        local subtype = trans_probe_safe_method(
            "visible_character.character_subtype_key",
            "unknown",
            function() return character:character_subtype_key() end
        )
        local x = trans_probe_safe_method(
            "visible_character.logical_position_x",
            -1,
            function() return character:logical_position_x() end
        )
        local y = trans_probe_safe_method(
            "visible_character.logical_position_y",
            -1,
            function() return character:logical_position_y() end
        )
        local has_force = trans_probe_safe_method(
            "visible_character.has_military_force",
            false,
            function() return character:has_military_force() end
        )
        local unit_count = -1
        if has_force then
            local force = trans_probe_safe_method(
                "visible_character.military_force",
                nil,
                function() return character:military_force() end
            )
            if force then
                local units = trans_probe_safe_method(
                    "visible_character.military_force.unit_list",
                    nil,
                    function() return force:unit_list() end
                )
                if units then
                    unit_count = trans_probe_safe_method(
                        "visible_character.military_force.unit_list.num_items",
                        -1,
                        function() return units:num_items() end
                    )
                end
            end
        end

        trans_probe_emit("VISIBLE_CHARACTER", {
            {"index", index},
            {"faction", foreign_faction},
            {"character_cqi", character_cqi},
            {"subtype", subtype},
            {"has_force", has_force},
            {"unit_count", unit_count},
            {"x", x},
            {"y", y}
        })
        emitted = emitted + 1
    end

    return total, emitted, true
end

local function trans_probe_emit_visible_regions(faction)
    local total, region_list, available = trans_probe_list_count(
        "local_faction.get_foreign_visible_regions_for_player",
        function() return faction:get_foreign_visible_regions_for_player() end
    )
    if not available then
        return -1, -1, false
    end

    local emitted = 0
    local limit = math.min(total, TRANS_PROBE_MAX_ITEMS)
    for index = 0, limit - 1 do
        local region = region_list:item_at(index)
        local region_name = trans_probe_safe_method(
            "visible_region.name",
            "unknown",
            function() return region:name() end
        )
        local owner_name = trans_probe_safe_method(
            "visible_region.owning_faction.name",
            "unknown",
            function() return region:owning_faction():name() end
        )
        local abandoned = trans_probe_safe_method(
            "visible_region.is_abandoned",
            false,
            function() return region:is_abandoned() end
        )

        trans_probe_emit("VISIBLE_REGION", {
            {"index", index},
            {"region", region_name},
            {"owner", owner_name},
            {"abandoned", abandoned}
        })
        emitted = emitted + 1
    end

    return total, emitted, true
end

local function trans_probe_emit_snapshot(faction, reason)
    if not faction or faction:is_null_interface() then
        trans_probe_emit("ERROR", {{"stage", "snapshot"}, {"reason", "null_local_faction"}})
        return
    end

    local faction_name = trans_probe_safe_method(
        "local_faction.name",
        "unknown",
        function() return faction:name() end
    )
    local turn = trans_probe_safe_method(
        "model.turn_number",
        -1,
        function() return cm:model():turn_number() end
    )
    local war_count = -1
    local war_list = trans_probe_safe_method(
        "local_faction.factions_at_war_with",
        nil,
        function() return faction:factions_at_war_with() end
    )
    if war_list then
        war_count = trans_probe_safe_method(
            "local_faction.factions_at_war_with.num_items",
            -1,
            function() return war_list:num_items() end
        )
    end

    trans_probe_emit("SNAPSHOT_BEGIN", {
        {"reason", reason},
        {"turn", turn},
        {"local_faction", faction_name}
    })

    local own_force_total, own_armies_emitted = trans_probe_emit_own_armies(faction)
    local own_region_total, own_regions_emitted = trans_probe_emit_own_regions(faction)
    local visible_character_total, visible_characters_emitted, visible_characters_available = trans_probe_emit_visible_characters(faction)
    local visible_region_total, visible_regions_emitted, visible_regions_available = trans_probe_emit_visible_regions(faction)

    trans_probe_emit("SNAPSHOT_END", {
        {"reason", reason},
        {"turn", turn},
        {"local_faction", faction_name},
        {"own_force_total", own_force_total},
        {"own_armies_emitted", own_armies_emitted},
        {"own_region_total", own_region_total},
        {"own_regions_emitted", own_regions_emitted},
        {"visible_character_total", visible_character_total},
        {"visible_characters_emitted", visible_characters_emitted},
        {"visible_characters_available", visible_characters_available},
        {"visible_region_total", visible_region_total},
        {"visible_regions_emitted", visible_regions_emitted},
        {"visible_regions_available", visible_regions_available},
        {"war_count", war_count},
        {"item_cap", TRANS_PROBE_MAX_ITEMS}
    })
end

local function trans_probe_first_tick()
    local local_faction_name = trans_probe_safe_method(
        "campaign_manager.get_local_faction_name",
        "unknown",
        function() return cm:get_local_faction_name(true) end
    )
    local campaign_name = trans_probe_safe_method(
        "model.campaign_name_key",
        "unknown",
        function() return cm:model():campaign_name_key() end
    )
    local turn = trans_probe_safe_method(
        "model.turn_number",
        -1,
        function() return cm:model():turn_number() end
    )
    local is_new_game = trans_probe_safe_method(
        "campaign_manager.is_new_game",
        false,
        function() return cm:is_new_game() end
    )
    local is_multiplayer = trans_probe_safe_method(
        "model.is_multiplayer",
        false,
        function() return cm:model():is_multiplayer() end
    )

    trans_probe_emit("FIRST_TICK", {
        {"probe_kind", TRANS_PROBE_KIND},
        {"campaign", campaign_name},
        {"turn", turn},
        {"local_faction", local_faction_name},
        {"is_new_game", is_new_game},
        {"is_multiplayer", is_multiplayer}
    })

    local faction = cm:get_faction(local_faction_name)
    trans_probe_emit_snapshot(faction, "FIRST_TICK")
end

trans_probe_emit("PACK_LOADED", {
    {"probe_kind", TRANS_PROBE_KIND},
    {"script", "transcendence_observer_probe"}
})

cm:add_first_tick_callback_sp_each(trans_probe_first_tick)

core:add_listener(
    "TranscendenceObserverProbeFactionTurnStart",
    "FactionTurnStart",
    function(context)
        local local_faction_name = cm:get_local_faction_name(true)
        return local_faction_name and context:faction():name() == local_faction_name
    end,
    function(context)
        trans_probe_emit_snapshot(context:faction(), "LOCAL_FACTION_TURN_START")
    end,
    true
)


-- WH3's generic mod loader attempts to invoke a function matching the filename.
function transcendence_observer_probe()
    -- Lifecycle registration occurs at file load; this entrypoint intentionally does nothing.
end
