-- Transcendence v0.1R read-only action-authority and feasibility probe.
-- This script observes game command events and local unit state only.
-- It creates no unitcontrollers, issues no orders, changes no speed, writes no saves,
-- and never labels state matching as acknowledgement or causal execution.

local TRANS_ACTION_SCHEMA = 1
local TRANS_ACTION_PREFIX = "TRANS_ACTION"
local TRANS_ACTION_LOG = "transcendence_runtime_log.txt"
local TRANS_ACTION_SAMPLE_REAL_MS = 250
local TRANS_ACTION_WINDOW_MS = 5000

local trans_action_bm = nil
local trans_action_local_alliance_index = -1
local trans_action_units = {}
local trans_action_selected = {}
local trans_action_windows = {}
local trans_action_command_index = 0
local trans_action_window_index = 0
local trans_action_project_issue_attempt_count = 0
local trans_action_direct_ack_count = 0
local trans_action_started = false
local trans_action_complete = false

local function trans_action_value(value)
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

local function trans_action_append(line)
    local opened, handle = pcall(io.open, TRANS_ACTION_LOG, "a")
    if not opened or not handle then return false end
    local wrote = pcall(function()
        handle:write(line .. "\n")
        handle:flush()
        handle:close()
    end)
    return wrote
end

local function trans_action_emit(event_name, fields)
    local parts = {TRANS_ACTION_PREFIX, tostring(TRANS_ACTION_SCHEMA), trans_action_value(event_name)}
    if fields then
        for index = 1, #fields do
            local field = fields[index]
            parts[#parts + 1] = trans_action_value(field[1]) .. "=" .. trans_action_value(field[2])
        end
    end
    local line = table.concat(parts, "|")
    trans_action_append(line)
    if ModLog then ModLog(line) elseif out then out(line) elseif trans_action_bm then trans_action_bm:out(line) end
end

local trans_action_capability_seen = {}
local function trans_action_safe(name, fallback, callback, required)
    local ok, value = pcall(callback)
    if ok then return value, true end
    if not trans_action_capability_seen[name] then
        trans_action_capability_seen[name] = true
        trans_action_emit("CAPABILITY", {
            {"name", name}, {"available", false}, {"required", required == true}, {"error", value}
        })
    end
    return fallback, false
end

local function trans_action_try(fallback, callback)
    local ok, value = pcall(callback)
    if ok then return value end
    return fallback
end

local function trans_action_time_ms()
    if not trans_action_bm then return -1 end
    return trans_action_safe("battle.time_elapsed_ms", -1, function() return trans_action_bm:time_elapsed_ms() end, true)
end

local function trans_action_unit_id(unit)
    local alliance = trans_action_safe("unit.alliance_index", -1, function() return unit:alliance_index() end, true)
    local unique_ui_id = trans_action_safe("unit.unique_ui_id", -1, function() return unit:unique_ui_id() end, true)
    if tonumber(unique_ui_id) and tonumber(unique_ui_id) >= 0 then
        return tostring(alliance) .. ":u" .. tostring(unique_ui_id), alliance
    end
    local army = trans_action_safe("unit.army_index", -1, function() return unit:army_index() end)
    return tostring(alliance) .. ":a" .. tostring(army) .. ":unknown", alliance
end

local function trans_action_target_id(unit)
    if not unit then return "none" end
    local unit_id, alliance = trans_action_unit_id(unit)
    if alliance == trans_action_local_alliance_index then return unit_id end
    local alliances = trans_action_safe("battle.alliances", nil, function() return trans_action_bm:alliances() end, true)
    local local_alliance = alliances and trans_action_safe("battle.local_alliance_object", nil, function() return alliances:item(trans_action_local_alliance_index) end, true) or nil
    local visible = local_alliance and trans_action_safe("unit.is_visible_to_alliance", false, function() return unit:is_visible_to_alliance(local_alliance) end, true) or false
    if visible then return unit_id end
    return "hidden"
end

local function trans_action_position_fields(vector, prefix)
    if not vector then
        return {{prefix .. "_available", false}, {prefix .. "_x", -1}, {prefix .. "_y", -1}, {prefix .. "_z", -1}}
    end
    return {
        {prefix .. "_available", true},
        {prefix .. "_x", trans_action_safe(prefix .. ".get_x", -1, function() return vector:get_x() end)},
        {prefix .. "_y", trans_action_safe(prefix .. ".get_y", -1, function() return vector:get_y() end)},
        {prefix .. "_z", trans_action_safe(prefix .. ".get_z", -1, function() return vector:get_z() end)}
    }
end

local function trans_action_append_fields(target, additions)
    for index = 1, #additions do target[#target + 1] = additions[index] end
end

local function trans_action_selected_ids()
    local ids = {}
    for unit_id, selected in pairs(trans_action_selected) do
        if selected and trans_action_units[unit_id] then ids[#ids + 1] = unit_id end
    end
    table.sort(ids)
    return ids, table.concat(ids, ",")
end

function transcendence_action_authority_selection_handler(unit, is_selected)
    local unit_id, alliance = trans_action_unit_id(unit)
    if alliance ~= trans_action_local_alliance_index then return end
    if is_selected then trans_action_selected[unit_id] = true else trans_action_selected[unit_id] = nil end
    trans_action_emit("SELECTION", {
        {"time_ms", trans_action_time_ms()}, {"unit_id", unit_id},
        {"local_alliance", true}, {"selected", is_selected}
    })
end

local function trans_action_register_local_units()
    local alliances = trans_action_safe("battle.alliances", nil, function() return trans_action_bm:alliances() end, true)
    if not alliances or trans_action_local_alliance_index < 1 then return end
    local alliance = trans_action_safe("battle.local_alliance_object", nil, function() return alliances:item(trans_action_local_alliance_index) end, true)
    local armies = alliance and trans_action_safe("alliance.armies", nil, function() return alliance:armies() end, true) or nil
    local army_count = armies and trans_action_safe("armies.count", 0, function() return armies:count() end, true) or 0
    for army_index = 1, army_count do
        local army = armies:item(army_index)
        local units = trans_action_safe("army.units", nil, function() return army:units() end, true)
        local unit_count = units and trans_action_safe("units.count", 0, function() return units:count() end, true) or 0
        for unit_index = 1, unit_count do
            local unit = units:item(unit_index)
            local unit_id, alliance_index = trans_action_unit_id(unit)
            trans_action_units[unit_id] = unit
            trans_action_emit("UNIT_STATIC", {
                {"time_ms", trans_action_time_ms()}, {"unit_id", unit_id},
                {"alliance_index", alliance_index}, {"army_index", army_index}, {"unit_index", unit_index},
                {"local_alliance", true}, {"visibility_source", "LOCAL_ALLIANCE"},
                {"unit_type", trans_action_safe("unit.type", "unknown", function() return unit:type() end)},
                {"unit_class", trans_action_safe("unit.unit_class", "unknown", function() return unit:unit_class() end)}
            })
            trans_action_safe("battle.register_unit_selection_callback", false, function()
                trans_action_bm:register_unit_selection_callback(unit, transcendence_action_authority_selection_handler)
                return true
            end)
        end
    end
end

local function trans_action_vector_near(a, b, tolerance)
    if not a or not b then return false end
    local ax = trans_action_try(nil, function() return a:get_x() end)
    local az = trans_action_try(nil, function() return a:get_z() end)
    local bx = trans_action_try(nil, function() return b:get_x() end)
    local bz = trans_action_try(nil, function() return b:get_z() end)
    if ax == nil or az == nil or bx == nil or bz == nil then return false end
    local dx = tonumber(ax) - tonumber(bx)
    local dz = tonumber(az) - tonumber(bz)
    return (dx * dx + dz * dz) <= tolerance * tolerance
end

local function trans_action_close_window(window_id, reason)
    local window = trans_action_windows[window_id]
    if not window then return end
    trans_action_emit("ACTION_WINDOW_CLOSE", {
        {"time_ms", trans_action_time_ms()}, {"window_id", window_id}, {"reason", reason},
        {"sample_count", window.sample_count}, {"project_issue_attempted", false},
        {"direct_ack_observed", false}
    })
    trans_action_windows[window_id] = nil
end

local function trans_action_sample_actor(window_id, window, unit_id, unit)
    local controllable = trans_action_safe("unit.is_controllable", false, function() return unit:is_controllable() end)
    local player_controlled = trans_action_safe("unit.is_player_controlled", false, function() return unit:is_player_controlled() end)
    local ai_controlled = trans_action_safe("unit.is_ai_controlled", false, function() return unit:is_ai_controlled() end)
    local script_controlled = trans_action_safe("unit.is_script_controlled", false, function() return unit:is_script_controlled() end)
    local moving = trans_action_safe("unit.is_moving", false, function() return unit:is_moving() end)
    local idle = trans_action_safe("unit.is_idle", false, function() return unit:is_idle() end)
    local leaving = trans_action_safe("unit.is_leaving_battle", false, function() return unit:is_leaving_battle() end)
    local routing = trans_action_safe("unit.is_routing", false, function() return unit:is_routing() end)
    local shattered = trans_action_safe("unit.is_shattered", false, function() return unit:is_shattered() end)
    local ordered_position = trans_action_safe("unit.ordered_position", nil, function() return unit:ordered_position() end)
    local current_target = trans_action_safe("unit.current_target", nil, function() return unit:current_target() end)
    local current_target_id = trans_action_target_id(current_target)
    local reachability = "NOT_APPLICABLE"
    if window.position then
        local reachable, available = trans_action_safe("unit.can_reach_position", false, function() return unit:can_reach_position(window.position) end)
        if available then reachability = reachable and "QUERY_TRUE" or "QUERY_FALSE" else reachability = "UNAVAILABLE" end
    end
    window.sample_count = window.sample_count + 1
    local fields = {
        {"time_ms", trans_action_time_ms()}, {"window_id", window_id}, {"sample_index", window.sample_count},
        {"unit_id", unit_id}, {"local_alliance", true}, {"controllable", controllable},
        {"player_controlled", player_controlled}, {"ai_controlled", ai_controlled}, {"script_controlled", script_controlled},
        {"moving", moving}, {"idle", idle}, {"leaving", leaving}, {"routing", routing}, {"shattered", shattered},
        {"reachability", reachability},
        {"ordered_position_match", trans_action_vector_near(ordered_position, window.position, 3.0)},
        {"current_target_match", window.target_unit_id ~= "none" and current_target_id == window.target_unit_id},
        {"current_target_id", current_target_id}
    }
    trans_action_append_fields(fields, trans_action_position_fields(ordered_position, "ordered_position"))
    trans_action_emit("ACTION_SAMPLE", fields)
    if shattered then return "SHATTERED" end
    if routing then return "ROUTED" end
    if not controllable then return "CONTROL_LOST" end
    return nil
end

local function trans_action_sampler_tick()
    if trans_action_complete then return end
    local now = trans_action_time_ms()
    local ids = {}
    for window_id, _ in pairs(trans_action_windows) do ids[#ids + 1] = window_id end
    table.sort(ids)
    for _, window_id in ipairs(ids) do
        local window = trans_action_windows[window_id]
        if window then
            local close_reason = nil
            for _, unit_id in ipairs(window.actor_ids) do
                local unit = trans_action_units[unit_id]
                if unit then
                    local reason = trans_action_sample_actor(window_id, window, unit_id, unit)
                    if reason then close_reason = reason end
                end
            end
            if close_reason then
                trans_action_close_window(window_id, close_reason)
            elseif now - window.opened_ms >= TRANS_ACTION_WINDOW_MS then
                trans_action_close_window(window_id, "WINDOW_TIMEOUT")
            end
        end
    end
end

local function trans_action_close_actor_windows(actor_ids)
    local actor_lookup = {}
    for _, unit_id in ipairs(actor_ids) do actor_lookup[unit_id] = true end
    local ids = {}
    for window_id, window in pairs(trans_action_windows) do
        for _, unit_id in ipairs(window.actor_ids) do
            if actor_lookup[unit_id] then ids[#ids + 1] = window_id; break end
        end
    end
    table.sort(ids)
    for _, window_id in ipairs(ids) do trans_action_close_window(window_id, "SUBSEQUENT_COMMAND") end
end

local function trans_action_command_callback(context)
    trans_action_command_index = trans_action_command_index + 1
    local command = trans_action_safe("command.get_name", "unknown", function() return context:get_name() end)
    local position = trans_action_try(nil, function() return context:get_position() end)
    local target = trans_action_try(nil, function() return context:get_unit() end)
    local target_unit_id = trans_action_target_id(target)
    local actor_ids, selected_text = trans_action_selected_ids()
    trans_action_close_actor_windows(actor_ids)
    local fields = {
        {"time_ms", trans_action_time_ms()}, {"command_index", trans_action_command_index}, {"command", command},
        {"selected_unit_ids", selected_text}, {"selected_unit_count", #actor_ids},
        {"command_origin", "GAME_COMMAND_EVENT_ORIGIN_UNRESOLVED"},
        {"project_issue_attempted", false}, {"direct_ack_available", false},
        {"target_unit_id", target_unit_id}
    }
    trans_action_append_fields(fields, trans_action_position_fields(position, "target_position"))
    trans_action_emit("COMMAND_OBSERVED", fields)

    trans_action_window_index = trans_action_window_index + 1
    local window_id = "w" .. tostring(trans_action_window_index)
    trans_action_emit("ACTION_WINDOW_OPEN", {
        {"time_ms", trans_action_time_ms()}, {"window_id", window_id},
        {"command_index", trans_action_command_index}, {"selected_unit_ids", selected_text},
        {"issue_classification", "OBSERVED_COMMAND_EVENT_NOT_PROJECT_ISSUE"},
        {"project_issue_attempted", false}, {"direct_ack_available", false}
    })
    trans_action_windows[window_id] = {
        opened_ms = trans_action_time_ms(), actor_ids = actor_ids, position = position,
        target_unit_id = target_unit_id, sample_count = 0
    }
    if #actor_ids == 0 then
        trans_action_close_window(window_id, "UNBOUND_SELECTION")
    else
        for _, unit_id in ipairs(actor_ids) do
            local unit = trans_action_units[unit_id]
            if unit then trans_action_sample_actor(window_id, trans_action_windows[window_id], unit_id, unit) end
        end
    end
end

local function trans_action_register_command(name)
    trans_action_safe("battle.register_command_handler_callback." .. name, false, function()
        trans_action_bm:register_command_handler_callback(name, trans_action_command_callback, "TranscendenceActionAuthority_" .. name)
        return true
    end)
end

local function trans_action_complete_battle()
    trans_action_complete = true
    local ids = {}
    for window_id, _ in pairs(trans_action_windows) do ids[#ids + 1] = window_id end
    table.sort(ids)
    for _, window_id in ipairs(ids) do trans_action_close_window(window_id, "TERMINAL") end
    trans_action_emit("BATTLE_COMPLETE", {
        {"time_ms", trans_action_time_ms()},
        {"project_issue_attempt_count", trans_action_project_issue_attempt_count},
        {"direct_ack_count", trans_action_direct_ack_count},
        {"commands_observed", trans_action_command_index}
    })
end

local function trans_action_setup()
    if trans_action_started then return end
    trans_action_started = true
    trans_action_bm = rawget(_G, "bm")
    if not trans_action_bm then
        local created, available = trans_action_safe("battle_manager.new", nil, function() return battle_manager:new(empire_battle:new()) end, true)
        if available then trans_action_bm = created; bm = created end
    end
    if not trans_action_bm then
        trans_action_emit("CAPABILITY", {{"name", "battle_manager"}, {"available", false}, {"required", true}})
        return
    end
    trans_action_local_alliance_index = trans_action_safe("battle.local_alliance", -1, function() return trans_action_bm:local_alliance() end, true)
    trans_action_emit("PACK_LOADED", {
        {"probe_kind", "action_authority_shadow"}, {"read_only", true}, {"gameplay_mutation", false},
        {"project_orders_enabled", false}, {"unitcontrollers_created", false},
        {"command_origin_policy", "GAME_COMMAND_EVENT_ORIGIN_UNRESOLVED"},
        {"direct_ack_policy", "UNAVAILABLE_NOT_OBSERVED"}, {"append_log", TRANS_ACTION_LOG}
    })
    trans_action_emit("RUNTIME_BEGIN", {{"time_ms", trans_action_time_ms()}, {"runtime", "battle"}})
    trans_action_emit("BATTLE_START", {
        {"time_ms", trans_action_time_ms()}, {"local_alliance", trans_action_local_alliance_index},
        {"multiplayer", trans_action_safe("battle.is_multiplayer", false, function() return trans_action_bm:is_multiplayer() end, true)},
        {"replay", trans_action_safe("battle.is_replay", false, function() return trans_action_bm:is_replay() end, true)}
    })
    trans_action_register_local_units()
    for _, command_name in ipairs({
        "Move", "Move Orientation Width", "Move Rotation Angle", "Change Speed",
        "Attack Unit", "Change Skirmish", "Change Melee", "Change Formation",
        "Attack Building", "Climb/Dock Building", "Special Ability", "Shot Type",
        "Fire At Will", "Withdraw", "Halt", "Double Click", "Battle Results"
    }) do trans_action_register_command(command_name) end
    trans_action_safe("battle.repeat_real_callback.action_sampler", false, function()
        trans_action_bm:repeat_real_callback(trans_action_sampler_tick, TRANS_ACTION_SAMPLE_REAL_MS, "TranscendenceActionAuthoritySampler")
        return true
    end, true)
    trans_action_safe("battle.register_phase_change_callback.Complete", false, function()
        trans_action_bm:register_phase_change_callback("Complete", trans_action_complete_battle)
        return true
    end, true)
end

local function trans_action_setup_guarded()
    local ok, failure = pcall(trans_action_setup)
    if not ok then
        trans_action_emit("CAPABILITY", {{"name", "battle.setup"}, {"available", false}, {"required", true}, {"error", failure}})
    end
end

function transcendence_action_authority_probe() trans_action_setup_guarded() end
trans_action_setup_guarded()
