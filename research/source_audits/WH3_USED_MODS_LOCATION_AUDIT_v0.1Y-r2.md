# WH3 `used_mods.txt` Location Audit — v0.1Y-r2

## Question

Where should the SFO preflight obtain the exact active pack order after the owner configures the current WH3 launcher?

## Evidence

- Owner observation: the legacy Steam AppData path did not exist after the launcher displayed exactly SFO plus the read-only Transcendence probe.
- Shazbot/WH3-Mod-Manager, pinned GitHub revision `2ef8069abbffa143ac8f8cca6d00b87c313c2d56`, uses `used_mods.txt` as WH3 launch state.
- The manager's Workshop documentation states that it imports `used_mods.txt` from the WH3 folder.
- TW Lua Debugger documentation locates the file relative to the WH3 executable.
- Existing Total War configuration conventions retain platform-specific AppData script directories for Steam, EOS, and GDK installations.

## Decision

Search exact supported candidates in this priority order:

1. WH3 game root;
2. Steam AppData scripts;
3. EOS AppData scripts;
4. GDK AppData scripts.

Parse every candidate that exists. Multiple copies are accepted only when their case-insensitive ordered pack lists agree. Conflicting copies stop preparation before any runtime log or watcher mutation.

## Privacy

The public environment profile records the source kind and SHA-256 only. Exact paths remain private.

## Limitation

This audit does not prove that a configured pack successfully loads in WH3. Runtime markers remain required.
