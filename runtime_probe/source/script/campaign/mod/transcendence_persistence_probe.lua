-- Transcendence Gate 0 save/reload probe.
-- Enabling this optional pack writes one project-owned integer to the savegame.

local TRANS_PROBE_SCHEMA = 1
local TRANS_PROBE_KIND = "persistence"
local TRANS_PROBE_PREFIX = "TRANS_PROBE"
local TRANS_PROBE_SAVE_KEY = "transcendence_gate0_probe_session_v1"

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

local function trans_probe_safe(callback, fallback)
    local ok, value = pcall(callback)
    if ok then
        return value
    end
    return fallback
end

local function trans_probe_persistence_first_tick()
    local previous = cm:get_saved_value(TRANS_PROBE_SAVE_KEY)
    local previous_found = previous ~= nil
    if not previous_found then
        previous = 0
    end

    local current = previous + 1
    cm:set_saved_value(TRANS_PROBE_SAVE_KEY, current)

    local campaign_name = trans_probe_safe(
        function() return cm:model():campaign_name_key() end,
        "unknown"
    )
    local turn = trans_probe_safe(
        function() return cm:model():turn_number() end,
        -1
    )
    local local_faction_name = trans_probe_safe(
        function() return cm:get_local_faction_name(true) end,
        "unknown"
    )
    local is_new_game = trans_probe_safe(
        function() return cm:is_new_game() end,
        false
    )
    local is_multiplayer = trans_probe_safe(
        function() return cm:model():is_multiplayer() end,
        false
    )
    local phase = "WRITE"
    if previous_found then
        phase = "RELOAD"
    end

    trans_probe_emit("PERSISTENCE_STATE", {
        {"probe_kind", TRANS_PROBE_KIND},
        {"phase", phase},
        {"campaign", campaign_name},
        {"turn", turn},
        {"local_faction", local_faction_name},
        {"is_new_game", is_new_game},
        {"is_multiplayer", is_multiplayer},
        {"key_version", 1},
        {"previous_found", previous_found},
        {"previous", previous},
        {"current", current}
    })
end

trans_probe_emit("PACK_LOADED", {
    {"probe_kind", TRANS_PROBE_KIND},
    {"script", "transcendence_persistence_probe"},
    {"writes_save_value", true}
})

cm:add_first_tick_callback_sp_each(trans_probe_persistence_first_tick)


-- WH3's generic mod loader attempts to invoke a function matching the filename.
function transcendence_persistence_probe()
    -- Lifecycle registration occurs at file load; this entrypoint intentionally does nothing.
end
