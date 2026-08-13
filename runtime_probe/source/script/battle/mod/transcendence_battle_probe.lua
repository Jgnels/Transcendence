-- Transcendence v0.1K dense ordinary-battle/replay telemetry probe.
-- Read-only by design: no unitcontrollers, no orders, no battle speed changes,
-- no save writes, no damage/healing, no visibility changes, and no randomness.
-- Enemy unit records are emitted only while the unit is visible to the local alliance.

local TRANS_BATTLE_SCHEMA = 2
local TRANS_BATTLE_PREFIX = "TRANS_BATTLE"
local TRANS_BATTLE_SAMPLE_MS = 3000
local TRANS_BATTLE_AGGREGATE_MS = 1000
local TRANS_BATTLE_REAL_TICK_MS = 500
local TRANS_BATTLE_HEARTBEAT_REAL_TICKS = 10
local TRANS_BATTLE_MAX_UNITS = 240
local TRANS_BATTLE_RUNTIME_LOG = "transcendence_runtime_log.txt"

local trans_battle_started = false
local trans_battle_complete = false
local trans_battle_manager = nil
local trans_battle_local_alliance_index = -1
local trans_battle_local_army_index = -1
local trans_battle_local_alliance = nil
local trans_battle_static_emitted = {}
local trans_battle_army_static_emitted = {}
local trans_battle_last_hierarchy = {}
local trans_battle_selection_registered = {}
local trans_battle_selected = {}
local trans_battle_capability_failures = {}
local trans_battle_sample_index = 0
local trans_battle_aggregate_index = 0
local trans_battle_command_index = 0
local trans_battle_model_tick_count = 0
local trans_battle_real_tick_count = 0
local trans_battle_last_detail_ms = -1
local trans_battle_last_aggregate_ms = -1
local trans_battle_sampler_lock = false

local function trans_battle_value(value)
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

local function trans_battle_append_runtime(line)
    local opened, handle = pcall(io.open, TRANS_BATTLE_RUNTIME_LOG, "a")
    if not opened or not handle then return false end
    local wrote = pcall(function()
        handle:write(line .. "\n")
        handle:flush()
        handle:close()
    end)
    return wrote
end

local function trans_battle_emit(event_name, fields)
    local parts = {TRANS_BATTLE_PREFIX, tostring(TRANS_BATTLE_SCHEMA), trans_battle_value(event_name)}
    if fields then
        for index = 1, #fields do
            local field = fields[index]
            parts[#parts + 1] = trans_battle_value(field[1]) .. "=" .. trans_battle_value(field[2])
        end
    end
    local line = table.concat(parts, "|")
    trans_battle_append_runtime(line)
    if ModLog then
        ModLog(line)
    elseif out then
        out(line)
    elseif trans_battle_manager then
        trans_battle_manager:out(line)
    end
end

local function trans_battle_safe(name, fallback, callback, required)
    local ok, value = pcall(callback)
    if ok then return value, true end
    if not trans_battle_capability_failures[name] then
        trans_battle_capability_failures[name] = true
        trans_battle_emit("CAPABILITY", {
            {"name", name}, {"available", false}, {"required", required == true}, {"error", value}
        })
    end
    return fallback, false
end

local function trans_battle_try(fallback, callback)
    local ok, value = pcall(callback)
    if ok then return value end
    return fallback
end

local function trans_battle_time_ms()
    if not trans_battle_manager then return -1 end
    return trans_battle_safe(
        "battle.time_elapsed_ms", -1,
        function() return trans_battle_manager:time_elapsed_ms() end,
        true
    )
end

local function trans_battle_vector_fields(vector, prefix)
    if not vector then
        return {{prefix .. "_x", -1}, {prefix .. "_y", -1}, {prefix .. "_z", -1}}
    end
    local x = trans_battle_safe(prefix .. ".get_x", -1, function() return vector:get_x() end)
    local y = trans_battle_safe(prefix .. ".get_y", -1, function() return vector:get_y() end)
    local z = trans_battle_safe(prefix .. ".get_z", -1, function() return vector:get_z() end)
    return {{prefix .. "_x", x}, {prefix .. "_y", y}, {prefix .. "_z", z}}
end

local function trans_battle_append(target, additions)
    for index = 1, #additions do target[#target + 1] = additions[index] end
end

local function trans_battle_sorted_table_values(value)
    if type(value) ~= "table" then return "" end
    local values = {}
    for _, item in pairs(value) do values[#values + 1] = tostring(item) end
    table.sort(values)
    return table.concat(values, ",")
end

local function trans_battle_unit_identity(unit, alliance_index, army_index, unit_index)
    local unique_ui_id, available = trans_battle_safe(
        "unit.unique_ui_id", -1,
        function() return unit:unique_ui_id() end,
        true
    )
    if available and unique_ui_id ~= nil and tonumber(unique_ui_id) and tonumber(unique_ui_id) >= 0 then
        return tostring(alliance_index) .. ":u" .. tostring(unique_ui_id), "UNIQUE_UI_ID", unique_ui_id
    end
    return tostring(alliance_index) .. ":a" .. tostring(army_index) .. ":i" .. tostring(unit_index), "HIERARCHY_FALLBACK", -1
end

local function trans_battle_unit_is_observable(unit, alliance_index)
    if alliance_index == trans_battle_local_alliance_index then return true, "LOCAL_ALLIANCE" end
    if not trans_battle_local_alliance then return false, "NO_LOCAL_ALLIANCE" end
    local visible, available = trans_battle_safe(
        "unit.is_visible_to_alliance", false,
        function() return unit:is_visible_to_alliance(trans_battle_local_alliance) end,
        true
    )
    if not available then return false, "VISIBILITY_UNAVAILABLE" end
    if visible then return true, "VISIBLE_TO_LOCAL_ALLIANCE" end
    return false, "HIDDEN_FROM_LOCAL_ALLIANCE"
end

local function trans_battle_target_id(target)
    if not target then return "none" end
    local alliance_index = trans_battle_safe("target.alliance_index", -1, function() return target:alliance_index() end)
    local army_index = trans_battle_safe("target.army_index", -1, function() return target:army_index() end)
    local observable = trans_battle_unit_is_observable(target, alliance_index)
    if not observable then return "hidden" end
    local unit_index = -1
    local unit_id = trans_battle_unit_identity(target, alliance_index, army_index, unit_index)
    return unit_id
end

local function trans_battle_emit_army_static(army, alliance_index, army_index, unit_count)
    local army_id = tostring(alliance_index) .. ":" .. tostring(army_index)
    if trans_battle_army_static_emitted[army_id] then return end
    trans_battle_army_static_emitted[army_id] = true
    trans_battle_emit("ARMY_STATIC", {
        {"time_ms", trans_battle_time_ms()},
        {"army_id", army_id},
        {"alliance_index", alliance_index},
        {"army_index", army_index},
        {"local_alliance", alliance_index == trans_battle_local_alliance_index},
        {"faction_key", trans_battle_safe("army.faction_key", "unknown", function() return army:faction_key() end)},
        {"subculture_key", trans_battle_safe("army.subculture_key", "unknown", function() return army:subculture_key() end)},
        {"unit_count", unit_count},
        {"reinforcement_collection_count", trans_battle_safe("army.num_reinforcement_units", 0, function() return army:num_reinforcement_units() end)}
    })
end

local function trans_battle_note_hierarchy(unit_id, alliance_index, army_index, unit_index, visibility_source)
    local current = tostring(alliance_index) .. ":" .. tostring(army_index) .. ":" .. tostring(unit_index)
    local previous = trans_battle_last_hierarchy[unit_id]
    if previous ~= current then
        trans_battle_last_hierarchy[unit_id] = current
        trans_battle_emit("UNIT_HIERARCHY", {
            {"time_ms", trans_battle_time_ms()}, {"unit_id", unit_id},
            {"alliance_index", alliance_index}, {"army_index", army_index}, {"unit_index", unit_index},
            {"local_alliance", alliance_index == trans_battle_local_alliance_index},
            {"visibility_source", visibility_source}, {"previous_hierarchy", previous or "none"}
        })
    end
end

local function trans_battle_register_selection(unit, unit_id, alliance_index)
    if alliance_index ~= trans_battle_local_alliance_index then return end
    if trans_battle_selection_registered[unit_id] then return end
    local player_controlled = trans_battle_safe(
        "selection.is_player_controlled", false,
        function() return unit:is_player_controlled() end
    )
    if not player_controlled then return end
    local registered, available = trans_battle_safe(
        "battle.register_unit_selection_callback", false,
        function()
            trans_battle_manager:register_unit_selection_callback(unit, transcendence_battle_probe_selection_handler)
            return true
        end,
        true
    )
    if available and registered then trans_battle_selection_registered[unit_id] = true end
end

local function trans_battle_emit_static(unit, unit_id, identity_source, unique_ui_id, alliance_index, army_index, unit_index, visibility_source)
    if trans_battle_static_emitted[unit_id] then return end
    trans_battle_static_emitted[unit_id] = true
    local is_local = alliance_index == trans_battle_local_alliance_index
    local passive_abilities = ""
    local active_abilities = ""
    if is_local then
        passive_abilities = trans_battle_sorted_table_values(
            trans_battle_safe("unit.owned_passive_special_abilities", {}, function() return unit:owned_passive_special_abilities() end)
        )
        active_abilities = trans_battle_sorted_table_values(
            trans_battle_safe("unit.owned_non_passive_special_abilities", {}, function() return unit:owned_non_passive_special_abilities() end)
        )
    end
    trans_battle_emit("UNIT_STATIC", {
        {"time_ms", trans_battle_time_ms()}, {"unit_id", unit_id}, {"stable_unit_id", unit_id},
        {"identity_source", identity_source}, {"unique_ui_id", unique_ui_id},
        {"alliance_index", alliance_index}, {"army_index", army_index}, {"unit_index", unit_index},
        {"local_alliance", is_local}, {"visibility_source", visibility_source},
        {"script_name", trans_battle_safe("unit.name", "", function() return unit:name() end)},
        {"unit_type", trans_battle_safe("unit.type", "unknown", function() return unit:type() end, true)},
        {"unit_class", trans_battle_safe("unit.unit_class", "unknown", function() return unit:unit_class() end, true)},
        {"is_commander", trans_battle_safe("unit.is_commanding_unit", false, function() return unit:is_commanding_unit() end)},
        {"is_infantry", trans_battle_safe("unit.is_infantry", false, function() return unit:is_infantry() end)},
        {"is_pikemen", trans_battle_safe("unit.is_pikemen", false, function() return unit:is_pikemen() end)},
        {"is_anti_cavalry_infantry", trans_battle_safe("unit.is_anti_cavalry_infantry", false, function() return unit:is_anti_cavalry_infantry() end)},
        {"is_cavalry", trans_battle_safe("unit.is_cavalry", false, function() return unit:is_cavalry() end)},
        {"is_lancers", trans_battle_safe("unit.is_lancers", false, function() return unit:is_lancers() end)},
        {"is_dismounted_cavalry", trans_battle_safe("unit.is_dismounted_cavalry", false, function() return unit:is_dismounted_cavalry() end)},
        {"is_chariot", trans_battle_safe("unit.is_chariot", false, function() return unit:is_chariot() end)},
        {"is_camels", trans_battle_safe("unit.is_camels", false, function() return unit:is_camels() end)},
        {"is_elephants", trans_battle_safe("unit.is_elephants", false, function() return unit:is_elephants() end)},
        {"is_war_beasts", trans_battle_safe("unit.is_war_beasts", false, function() return unit:is_war_beasts() end)},
        {"is_artillery", trans_battle_safe("unit.is_artillery", false, function() return unit:is_artillery() end)},
        {"is_unlimbered_artillery", trans_battle_safe("unit.is_unlimbered_artillery", false, function() return unit:is_unlimbered_artillery() end)},
        {"is_limbered_artillery", trans_battle_safe("unit.is_limbered_artillery", false, function() return unit:is_limbered_artillery() end)},
        {"is_fixed_artillery", trans_battle_safe("unit.is_fixed_artillery", false, function() return unit:is_fixed_artillery() end)},
        {"is_war_machine", trans_battle_safe("unit.is_war_machine", false, function() return unit:is_war_machine() end)},
        {"can_fly", trans_battle_safe("unit.can_fly", false, function() return unit:can_fly() end)},
        {"initial_men", trans_battle_safe("unit.initial_number_of_men", -1, function() return unit:initial_number_of_men() end, true)},
        {"starting_ammo", trans_battle_safe("unit.starting_ammo", -1, function() return unit:starting_ammo() end)},
        {"missile_range", trans_battle_safe("unit.missile_range", -1, function() return unit:missile_range() end)},
        {"slow_speed", trans_battle_safe("unit.slow_speed", -1, function() return unit:slow_speed() end)},
        {"fast_speed", trans_battle_safe("unit.fast_speed", -1, function() return unit:fast_speed() end)},
        {"initial_strategic_value_proxy", trans_battle_safe("unit.strategic_value.initial", -1, function() return unit:strategic_value() end)},
        {"num_special_abilities", is_local and trans_battle_safe("unit.num_special_abilities", 0, function() return unit:num_special_abilities() end) or -1},
        {"owned_passive_abilities", passive_abilities},
        {"owned_non_passive_abilities", active_abilities},
        {"player_controlled", trans_battle_safe("unit.is_player_controlled", false, function() return unit:is_player_controlled() end)},
        {"ai_controlled", trans_battle_safe("unit.is_ai_controlled", false, function() return unit:is_ai_controlled() end)},
        {"script_controlled", trans_battle_safe("unit.is_script_controlled", false, function() return unit:is_script_controlled() end)}
    })
end

local function trans_battle_emit_dynamic(unit, unit_id, alliance_index, army_index, unit_index, visibility_source, sample_index)
    local position = trans_battle_safe("unit.position", nil, function() return unit:position() end, true)
    local ordered_position = trans_battle_safe("unit.ordered_position", nil, function() return unit:ordered_position() end)
    local officer_position = trans_battle_safe("unit.position_of_officer", nil, function() return unit:position_of_officer() end)
    local current_target = trans_battle_safe("unit.current_target", nil, function() return unit:current_target() end)
    local left_threat = trans_battle_safe("unit.left_flank_threat", nil, function() return unit:left_flank_threat() end)
    local right_threat = trans_battle_safe("unit.right_flank_threat", nil, function() return unit:right_flank_threat() end)
    local rear_threat = trans_battle_safe("unit.rear_threat", nil, function() return unit:rear_threat() end)
    local target_distance = -1
    local target_in_range = false
    if current_target and trans_battle_target_id(current_target) ~= "hidden" then
        target_distance = trans_battle_safe("unit.unit_distance", -1, function() return unit:unit_distance(current_target) end)
        target_in_range = trans_battle_safe("unit.unit_in_range", false, function() return unit:unit_in_range(current_target) end)
    end
    local fields = {
        {"time_ms", trans_battle_time_ms()}, {"sample_index", sample_index}, {"unit_id", unit_id}, {"stable_unit_id", unit_id},
        {"alliance_index", alliance_index}, {"army_index", army_index}, {"unit_index", unit_index},
        {"local_alliance", alliance_index == trans_battle_local_alliance_index}, {"visibility_source", visibility_source},
        {"men_alive", trans_battle_safe("unit.number_of_men_alive", -1, function() return unit:number_of_men_alive() end, true)},
        {"men_fraction", trans_battle_safe("unit.unary_of_men_alive", -1, function() return unit:unary_of_men_alive() end)},
        {"hitpoints_fraction", trans_battle_safe("unit.unary_hitpoints", -1, function() return unit:unary_hitpoints() end, true)},
        {"kills", trans_battle_safe("unit.number_of_enemies_killed", -1, function() return unit:number_of_enemies_killed() end, true)},
        {"ammo", trans_battle_safe("unit.ammo_left", -1, function() return unit:ammo_left() end)},
        {"strategic_value_proxy", trans_battle_safe("unit.strategic_value", -1, function() return unit:strategic_value() end)},
        {"bearing", trans_battle_safe("unit.bearing", -1, function() return unit:bearing() end)},
        {"ordered_bearing", trans_battle_safe("unit.ordered_bearing", -1, function() return unit:ordered_bearing() end)},
        {"ordered_width", trans_battle_safe("unit.ordered_width", -1, function() return unit:ordered_width() end)},
        {"moving", trans_battle_safe("unit.is_moving", false, function() return unit:is_moving() end)},
        {"moving_fast", trans_battle_safe("unit.is_moving_fast", false, function() return unit:is_moving_fast() end)},
        {"idle", trans_battle_safe("unit.is_idle", false, function() return unit:is_idle() end)},
        {"leaving", trans_battle_safe("unit.is_leaving_battle", false, function() return unit:is_leaving_battle() end)},
        {"valid_for_deployment", trans_battle_safe("unit.is_valid_for_deployment", false, function() return unit:is_valid_for_deployment() end)},
        {"valid_target", trans_battle_safe("unit.is_valid_target", false, function() return unit:is_valid_target() end)},
        {"controllable", trans_battle_safe("unit.is_controllable", false, function() return unit:is_controllable() end)},
        {"deploying", trans_battle_safe("unit.is_deploying", false, function() return unit:is_deploying() end)},
        {"deployed", trans_battle_safe("unit.is_deployed", false, function() return unit:is_deployed() end)},
        {"hidden", trans_battle_safe("unit.is_hidden", false, function() return unit:is_hidden() end)},
        {"currently_flying", trans_battle_safe("unit.is_currently_flying", false, function() return unit:is_currently_flying() end)},
        {"invulnerable", trans_battle_safe("unit.is_invulnerable", false, function() return unit:is_invulnerable() end)},
        {"in_melee", trans_battle_safe("unit.is_in_melee", false, function() return unit:is_in_melee() end)},
        {"under_missile_attack", trans_battle_safe("unit.is_under_missile_attack", false, function() return unit:is_under_missile_attack() end)},
        {"wavering", trans_battle_safe("unit.is_wavering", false, function() return unit:is_wavering() end)},
        {"routing", trans_battle_safe("unit.is_routing", false, function() return unit:is_routing() end)},
        {"shattered", trans_battle_safe("unit.is_shattered", false, function() return unit:is_shattered() end)},
        {"crumbling", trans_battle_safe("unit.is_crumbling", false, function() return unit:is_crumbling() end)},
        {"unstable", trans_battle_safe("unit.is_unstable", false, function() return unit:is_unstable() end)},
        {"rampaging", trans_battle_safe("unit.is_rampaging", false, function() return unit:is_rampaging() end)},
        {"fatigue", trans_battle_safe("unit.fatigue_state", "unknown", function() return unit:fatigue_state() end)},
        {"left_flank_threatened", trans_battle_safe("unit.is_left_flank_threatened", false, function() return unit:is_left_flank_threatened() end)},
        {"right_flank_threatened", trans_battle_safe("unit.is_right_flank_threatened", false, function() return unit:is_right_flank_threatened() end)},
        {"rear_flank_threatened", trans_battle_safe("unit.is_rear_flank_threatened", false, function() return unit:is_rear_flank_threatened() end)},
        {"left_flank_threat_id", trans_battle_target_id(left_threat)},
        {"right_flank_threat_id", trans_battle_target_id(right_threat)},
        {"rear_flank_threat_id", trans_battle_target_id(rear_threat)},
        {"current_target_id", trans_battle_target_id(current_target)},
        {"current_target_distance", target_distance}, {"current_target_in_range", target_in_range},
        {"on_platform", trans_battle_safe("unit.is_on_top_of_platform", false, function() return unit:is_on_top_of_platform() end)},
        {"currently_garrisoned", trans_battle_safe("unit.is_currently_garrisoned", false, function() return unit:is_currently_garrisoned() end)},
        {"player_controlled", trans_battle_safe("unit.is_player_controlled", false, function() return unit:is_player_controlled() end)},
        {"ai_controlled", trans_battle_safe("unit.is_ai_controlled", false, function() return unit:is_ai_controlled() end)},
        {"script_controlled", trans_battle_safe("unit.is_script_controlled", false, function() return unit:is_script_controlled() end)}
    }
    trans_battle_append(fields, trans_battle_vector_fields(position, "position"))
    trans_battle_append(fields, trans_battle_vector_fields(ordered_position, "ordered_position"))
    trans_battle_append(fields, trans_battle_vector_fields(officer_position, "officer_position"))
    trans_battle_emit("UNIT_STATE", fields)
end

local function trans_battle_each_observable_unit(callback)
    if not trans_battle_manager then return 0, 0, 0 end
    local alliances, available = trans_battle_safe("battle.alliances", nil, function() return trans_battle_manager:alliances() end, true)
    if not available or not alliances then return 0, 0, 0 end
    local alliance_count = trans_battle_safe("alliances.count", 0, function() return alliances:count() end, true)
    local observed, hidden, total = 0, 0, 0
    for alliance_index = 1, alliance_count do
        local alliance = alliances:item(alliance_index)
        local armies = trans_battle_safe("alliance.armies", nil, function() return alliance:armies() end, true)
        if armies then
            local army_count = trans_battle_safe("armies.count", 0, function() return armies:count() end, true)
            for army_index = 1, army_count do
                local army = armies:item(army_index)
                local units = trans_battle_safe("army.units", nil, function() return army:units() end, true)
                if units then
                    local unit_count = trans_battle_safe("units.count", 0, function() return units:count() end, true)
                    trans_battle_emit_army_static(army, alliance_index, army_index, unit_count)
                    for unit_index = 1, unit_count do
                        if total >= TRANS_BATTLE_MAX_UNITS then return observed, hidden, total end
                        total = total + 1
                        local unit = units:item(unit_index)
                        local observable, visibility_source = trans_battle_unit_is_observable(unit, alliance_index)
                        if observable then
                            observed = observed + 1
                            callback(unit, alliance_index, army_index, unit_index, visibility_source)
                        else
                            hidden = hidden + 1
                        end
                    end
                end
            end
        end
    end
    return observed, hidden, total
end

local function trans_battle_detailed_sample(reason, scheduler_source)
    trans_battle_sample_index = trans_battle_sample_index + 1
    local sample_time = trans_battle_time_ms()
    trans_battle_emit("SAMPLE_BEGIN", {
        {"time_ms", sample_time}, {"sample_index", trans_battle_sample_index},
        {"reason", reason}, {"scheduler_source", scheduler_source or "DIRECT"}
    })
    local observed, hidden, total = trans_battle_each_observable_unit(function(unit, alliance_index, army_index, unit_index, visibility_source)
        local unit_id, identity_source, unique_ui_id = trans_battle_unit_identity(unit, alliance_index, army_index, unit_index)
        trans_battle_note_hierarchy(unit_id, alliance_index, army_index, unit_index, visibility_source)
        trans_battle_register_selection(unit, unit_id, alliance_index)
        trans_battle_emit_static(unit, unit_id, identity_source, unique_ui_id, alliance_index, army_index, unit_index, visibility_source)
        trans_battle_emit_dynamic(unit, unit_id, alliance_index, army_index, unit_index, visibility_source, trans_battle_sample_index)
    end)
    trans_battle_emit("SAMPLE_END", {
        {"time_ms", trans_battle_time_ms()}, {"sample_index", trans_battle_sample_index},
        {"reason", reason}, {"scheduler_source", scheduler_source or "DIRECT"},
        {"observed_units", observed}, {"hidden_enemy_units", hidden},
        {"total_units_seen_by_hierarchy", total}, {"unit_cap", TRANS_BATTLE_MAX_UNITS}
    })
    trans_battle_last_detail_ms = sample_time
end

local function trans_battle_aggregate_sample(scheduler_source)
    trans_battle_aggregate_index = trans_battle_aggregate_index + 1
    local sample_time = trans_battle_time_ms()
    local by_alliance = {}
    local observed, hidden, total = trans_battle_each_observable_unit(function(unit, alliance_index)
        if not by_alliance[alliance_index] then
            by_alliance[alliance_index] = {units=0, men=0, kills=0, ammo=0, strategic_value=0, melee=0, missile=0, routing=0, wavering=0, shattered=0, idle=0, moving=0, flank=0}
        end
        local a = by_alliance[alliance_index]
        a.units = a.units + 1
        a.men = a.men + trans_battle_safe("aggregate.men", 0, function() return unit:number_of_men_alive() end)
        a.kills = a.kills + trans_battle_safe("aggregate.kills", 0, function() return unit:number_of_enemies_killed() end)
        local aggregate_ammo = trans_battle_safe(
            "aggregate.ammo", 0, function() return unit:ammo_left() end
        )
        local aggregate_strategic_value = trans_battle_safe(
            "aggregate.strategic_value", 0, function() return unit:strategic_value() end
        )
        a.ammo = a.ammo + math.max(0, tonumber(aggregate_ammo) or 0)
        a.strategic_value = a.strategic_value + math.max(0, tonumber(aggregate_strategic_value) or 0)
        if trans_battle_safe("aggregate.melee", false, function() return unit:is_in_melee() end) then a.melee = a.melee + 1 end
        if trans_battle_safe("aggregate.missile", false, function() return unit:is_under_missile_attack() end) then a.missile = a.missile + 1 end
        if trans_battle_safe("aggregate.routing", false, function() return unit:is_routing() end) then a.routing = a.routing + 1 end
        if trans_battle_safe("aggregate.wavering", false, function() return unit:is_wavering() end) then a.wavering = a.wavering + 1 end
        if trans_battle_safe("aggregate.shattered", false, function() return unit:is_shattered() end) then a.shattered = a.shattered + 1 end
        if trans_battle_safe("aggregate.idle", false, function() return unit:is_idle() end) then a.idle = a.idle + 1 end
        if trans_battle_safe("aggregate.moving", false, function() return unit:is_moving() end) then a.moving = a.moving + 1 end
        if trans_battle_safe("aggregate.left_flank", false, function() return unit:is_left_flank_threatened() end)
            or trans_battle_safe("aggregate.right_flank", false, function() return unit:is_right_flank_threatened() end)
            or trans_battle_safe("aggregate.rear_flank", false, function() return unit:is_rear_flank_threatened() end) then a.flank = a.flank + 1 end
    end)
    for alliance_index, a in pairs(by_alliance) do
        trans_battle_emit("ALLIANCE_AGGREGATE", {
            {"time_ms", sample_time}, {"aggregate_index", trans_battle_aggregate_index},
            {"scheduler_source", scheduler_source or "DIRECT"},
            {"alliance_index", alliance_index}, {"local_alliance", alliance_index == trans_battle_local_alliance_index},
            {"observed_units", a.units}, {"men_alive", a.men}, {"kills", a.kills}, {"ammo", a.ammo},
            {"strategic_value_proxy", a.strategic_value}, {"units_in_melee", a.melee},
            {"units_under_missile_attack", a.missile}, {"units_routing", a.routing}, {"units_wavering", a.wavering},
            {"units_shattered", a.shattered}, {"units_idle", a.idle}, {"units_moving", a.moving},
            {"units_flank_threatened", a.flank}, {"hidden_enemy_units", hidden}, {"hierarchy_unit_total", total}
        })
    end
    trans_battle_last_aggregate_ms = sample_time
end

function transcendence_battle_probe_selection_handler(unit, is_selected)
    local alliance_index = trans_battle_safe("selection.alliance_index", -1, function() return unit:alliance_index() end)
    local army_index = trans_battle_safe("selection.army_index", -1, function() return unit:army_index() end)
    local observable, visibility_source = trans_battle_unit_is_observable(unit, alliance_index)
    if not observable then return end
    local unit_id = trans_battle_unit_identity(unit, alliance_index, army_index, -1)
    if is_selected then trans_battle_selected[unit_id] = true else trans_battle_selected[unit_id] = nil end
    trans_battle_emit("SELECTION", {
        {"time_ms", trans_battle_time_ms()}, {"unit_id", unit_id},
        {"alliance_index", alliance_index}, {"local_alliance", alliance_index == trans_battle_local_alliance_index},
        {"visibility_source", visibility_source}, {"selected", is_selected}
    })
end

local function trans_battle_selected_ids()
    local ids = {}
    for unit_id, selected in pairs(trans_battle_selected) do
        if selected then ids[#ids + 1] = unit_id end
    end
    table.sort(ids)
    return table.concat(ids, ",")
end

local function trans_battle_command_callback(context)
    trans_battle_command_index = trans_battle_command_index + 1
    local name = trans_battle_safe("command.get_name", "unknown", function() return context:get_name() end)
    local bool1 = trans_battle_try("unavailable", function() return context:get_bool1() end)
    local string1 = trans_battle_try("unavailable", function() return context:get_string1() end)
    local position = trans_battle_try(nil, function() return context:get_position() end)
    local target = trans_battle_try(nil, function() return context:get_unit() end)
    local selected_ids = trans_battle_selected_ids()
    local selected_count = 0
    if selected_ids ~= "" then
        selected_count = 1
        for _ in string.gmatch(selected_ids, ",") do selected_count = selected_count + 1 end
    end
    local fields = {
        {"time_ms", trans_battle_time_ms()}, {"command_index", trans_battle_command_index},
        {"command", name}, {"selected_unit_ids", selected_ids}, {"selected_unit_count", selected_count},
        {"bool1", bool1}, {"string1", string1}, {"target_unit_id", trans_battle_target_id(target)}
    }
    trans_battle_append(fields, trans_battle_vector_fields(position, "position"))
    trans_battle_emit("COMMAND", fields)
end

local function trans_battle_register_command(command_name)
    trans_battle_safe("battle.register_command_handler_callback." .. command_name, false, function()
        trans_battle_manager:register_command_handler_callback(
            command_name,
            trans_battle_command_callback,
            "TranscendenceBattleProbe_" .. command_name
        )
        return true
    end)
end

local function trans_battle_sampler_tick(source)
    if trans_battle_complete or trans_battle_sampler_lock then return end
    trans_battle_sampler_lock = true
    local ok, failure = pcall(function()
        if source == "MODEL" then
            trans_battle_model_tick_count = trans_battle_model_tick_count + 1
        else
            trans_battle_real_tick_count = trans_battle_real_tick_count + 1
        end
        local model_time = trans_battle_time_ms()
        if model_time >= 0 then
            if trans_battle_last_aggregate_ms < 0 or model_time - trans_battle_last_aggregate_ms >= TRANS_BATTLE_AGGREGATE_MS then
                trans_battle_aggregate_sample(source)
            end
            if trans_battle_last_detail_ms < 0 or model_time - trans_battle_last_detail_ms >= TRANS_BATTLE_SAMPLE_MS then
                trans_battle_detailed_sample("TIMER_" .. source, source)
            end
        end
        if source == "REAL" and trans_battle_real_tick_count % TRANS_BATTLE_HEARTBEAT_REAL_TICKS == 0 then
            trans_battle_emit("SAMPLER_HEARTBEAT", {
                {"time_ms", model_time}, {"model_tick_count", trans_battle_model_tick_count},
                {"real_tick_count", trans_battle_real_tick_count}, {"detail_sample_count", trans_battle_sample_index},
                {"aggregate_sample_count", trans_battle_aggregate_index}, {"last_detail_ms", trans_battle_last_detail_ms},
                {"last_aggregate_ms", trans_battle_last_aggregate_ms}
            })
        end
    end)
    trans_battle_sampler_lock = false
    if not ok and not trans_battle_capability_failures["battle.sampler_tick"] then
        trans_battle_capability_failures["battle.sampler_tick"] = true
        trans_battle_emit("CAPABILITY", {
            {"name", "battle.sampler_tick"}, {"available", false}, {"required", true}, {"error", failure}
        })
    end
end

local function trans_battle_stop_samplers()
    trans_battle_safe("battle.remove_callback.model", false, function()
        trans_battle_manager:remove_callback("TranscendenceBattleModelSampler")
        return true
    end)
    trans_battle_safe("battle.remove_real_callback.real", false, function()
        trans_battle_manager:remove_real_callback("TranscendenceBattleRealSampler")
        return true
    end)
end

local function trans_battle_phase(phase_name)
    trans_battle_emit("PHASE", {{"time_ms", trans_battle_time_ms()}, {"phase", phase_name}})
    trans_battle_detailed_sample("PHASE_" .. phase_name, "PHASE")
    if phase_name == "Complete" then
        trans_battle_complete = true
        trans_battle_stop_samplers()
        trans_battle_emit("BATTLE_COMPLETE", {
            {"time_ms", trans_battle_time_ms()},
            {"outcome_decided", trans_battle_safe("battle.battle_outcome_decided", false, function() return trans_battle_manager:battle_outcome_decided() end)},
            {"victorious_alliance", trans_battle_safe("battle.victorious_alliance", -1, function() return trans_battle_manager:victorious_alliance() end)},
            {"draw", trans_battle_safe("battle.is_draw", false, function() return trans_battle_manager:is_draw() end)},
            {"detail_samples", trans_battle_sample_index}, {"aggregate_samples", trans_battle_aggregate_index},
            {"model_tick_count", trans_battle_model_tick_count}, {"real_tick_count", trans_battle_real_tick_count},
            {"commands_observed", trans_battle_command_index}
        })
    end
end

local function trans_battle_setup()
    if trans_battle_started then return end
    trans_battle_started = true
    trans_battle_manager = rawget(_G, "bm")
    if not trans_battle_manager then
        local created, available = trans_battle_safe("battle_manager.new", nil, function() return battle_manager:new(empire_battle:new()) end, true)
        if available then trans_battle_manager = created; bm = created end
    end
    if not trans_battle_manager then
        trans_battle_emit("ERROR", {{"name", "battle_manager_unavailable"}})
        return
    end

    trans_battle_local_alliance_index = trans_battle_safe("battle.local_alliance", -1, function() return trans_battle_manager:local_alliance() end, true)
    trans_battle_local_army_index = trans_battle_safe("battle.local_army", -1, function() return trans_battle_manager:local_army() end, true)
    local alliances = trans_battle_safe("battle.alliances", nil, function() return trans_battle_manager:alliances() end, true)
    if alliances and trans_battle_local_alliance_index > 0 then
        trans_battle_local_alliance = trans_battle_safe("battle.local_alliance_object", nil, function() return alliances:item(trans_battle_local_alliance_index) end, true)
    end

    trans_battle_emit("PACK_LOADED", {
        {"probe_kind", "battle_replay_shadow"}, {"script", "transcendence_battle_probe"}, {"read_only", true},
        {"enemy_visibility_policy", "VISIBLE_TO_LOCAL_ALLIANCE_ONLY"},
        {"sample_interval_ms", TRANS_BATTLE_SAMPLE_MS}, {"aggregate_interval_ms", TRANS_BATTLE_AGGREGATE_MS},
        {"real_tick_interval_ms", TRANS_BATTLE_REAL_TICK_MS}, {"append_log", TRANS_BATTLE_RUNTIME_LOG}
    })
    trans_battle_emit("RUNTIME_BEGIN", {
        {"probe_kind", "battle_replay_shadow"}, {"runtime", "battle"}, {"append_log", TRANS_BATTLE_RUNTIME_LOG}
    })
    trans_battle_emit("BATTLE_START", {
        {"time_ms", trans_battle_time_ms()},
        {"from_campaign", trans_battle_safe("battle.is_from_campaign", false, function() return trans_battle_manager:is_from_campaign() end, true)},
        {"quest_battle", trans_battle_safe("battle.is_quest_battle", false, function() return trans_battle_manager:is_quest_battle() end)},
        {"multiplayer", trans_battle_safe("battle.is_multiplayer", false, function() return trans_battle_manager:is_multiplayer() end)},
        {"replay", trans_battle_safe("battle.is_replay", false, function() return trans_battle_manager:is_replay() end)},
        {"spectator", trans_battle_safe("battle.is_spectator", false, function() return trans_battle_manager:is_spectator() end)},
        {"siege", trans_battle_safe("battle.is_siege_battle", false, function() return trans_battle_manager:is_siege_battle() end)},
        {"ambush", trans_battle_safe("battle.is_ambush_battle", false, function() return trans_battle_manager:is_ambush_battle() end)},
        {"battle_type", trans_battle_safe("battle.battle_type", "unknown", function() return trans_battle_manager:battle_type() end, true)},
        {"unit_scale_factor", trans_battle_safe("battle.unit_scale_factor", -1, function() return trans_battle_manager:unit_scale_factor() end, true)},
        {"alliance_count", alliances and trans_battle_safe("alliances.count", 0, function() return alliances:count() end, true) or 0},
        {"local_alliance", trans_battle_local_alliance_index}, {"local_army", trans_battle_local_army_index}
    })

    for _, phase_name in ipairs({"Deployment", "Deployed", "VictoryCountdown", "Complete"}) do
        trans_battle_safe("battle.register_phase_change_callback." .. phase_name, false, function()
            trans_battle_manager:register_phase_change_callback(phase_name, function() trans_battle_phase(phase_name) end)
            return true
        end, true)
    end
    for _, command_name in ipairs({
        "Move", "Move Orientation Width", "Move Rotation Angle", "Change Speed",
        "Attack Unit", "Change Skirmish", "Change Melee", "Change Formation",
        "Attack Building", "Climb/Dock Building", "Special Ability", "Shot Type",
        "Fire At Will", "Withdraw", "Halt", "Double Click", "Battle Results"
    }) do
        trans_battle_register_command(command_name)
    end

    trans_battle_detailed_sample("INITIAL", "DIRECT")

    -- Register and disclose both clocks before taking the first aggregate.
    -- This makes setup failures diagnosable and prevents a single aggregate
    -- query defect from silently disabling all interval callbacks.
    local model_registered = trans_battle_safe("battle.repeat_callback.model_sampler", false, function()
        trans_battle_manager:repeat_callback(function() trans_battle_sampler_tick("MODEL") end, TRANS_BATTLE_AGGREGATE_MS, "TranscendenceBattleModelSampler")
        return true
    end, true)
    local real_registered = trans_battle_safe("battle.repeat_real_callback.real_sampler", false, function()
        trans_battle_manager:repeat_real_callback(function() trans_battle_sampler_tick("REAL") end, TRANS_BATTLE_REAL_TICK_MS, "TranscendenceBattleRealSampler")
        return true
    end, true)
    trans_battle_emit("SAMPLER_START", {
        {"time_ms", trans_battle_time_ms()}, {"detail_interval_ms", TRANS_BATTLE_SAMPLE_MS},
        {"aggregate_interval_ms", TRANS_BATTLE_AGGREGATE_MS}, {"real_tick_interval_ms", TRANS_BATTLE_REAL_TICK_MS},
        {"model_callback_registered", model_registered}, {"real_callback_registered", real_registered}
    })
    trans_battle_aggregate_sample("DIRECT")
end

local function trans_battle_setup_guarded()
    local ok, failure = pcall(trans_battle_setup)
    if not ok then
        trans_battle_emit("CAPABILITY", {
            {"name", "battle.setup"}, {"available", false}, {"required", true}, {"error", failure}
        })
    end
end

function transcendence_battle_probe() trans_battle_setup_guarded() end
trans_battle_setup_guarded()
