"""Control of the open Uncle Farmer by other programs: what `UncleFarmer.exe --mcp` (mcpserver.py) and
the open window (gui/remote.py) share.

The open Uncle Farmer listens on a named pipe of this Windows user. A connection must prove it knows
the secret the window writes at each start into the agent's run folder (a file only this user's
programs can read), and the window answers only while Settings, "Let other programs on this computer
control Uncle Farmer (MCP)" is on. Requests and answers are JSON: {"tool", "args"} in, {"ok",
"text", "data"} out. Nothing is pickled.

The texts here are for the program calling the tools, so they are English only.
"""

from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass, field
from multiprocessing.connection import Connection
from typing import Any

from . import paths

SECRET_FILE = os.path.join(paths.AGENT_RUN, "control.key")
LONGEST_WAIT = 300          # seconds a waiting tool (wait_for_log, wait_for_run) may be asked to wait
NOT_ALLOWED = ("Uncle Farmer is open but doesn't allow control by other programs. The player can turn it on in "
               "Uncle Farmer: File, Settings, Control, \"Let other programs on this computer control Uncle "
               "Farmer (MCP)\".")


def pipe_name() -> str:
    """The open Uncle Farmer's end: one per Windows user (one Uncle Farmer runs per session)."""
    user = "".join(c for c in os.environ.get("USERNAME", "") if c.isascii() and c.isalnum())
    test = os.environ.get("UNCLEFARMER_CONTROL_PIPE", "")       # tests use a pipe of their own
    return test or r"\\.\pipe\UncleFarmer-control-%s" % user


def new_secret(path: str | None = None) -> bytes:
    """A fresh secret for this start of the window, written where only this user's programs can read it."""
    path = path or SECRET_FILE
    key = secrets.token_hex(32)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="ascii") as f:
        f.write(key)
    os.replace(tmp, path)
    return key.encode("ascii")


def read_secret(path: str | None = None) -> bytes | None:
    try:
        with open(path or SECRET_FILE, encoding="ascii") as f:
            key = f.read().strip()
    except OSError:
        return None
    return key.encode("ascii") if key else None


def send(conn: Connection, obj: object) -> None:
    conn.send_bytes(json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"))


def receive(conn: Connection) -> Any:
    return json.loads(conn.recv_bytes(16 * 1024 * 1024).decode("utf-8"))


# ---------------------------------------------------------------------------------------- the tools
READ, ACT, RISKY = "read", "act", "risky"


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    properties: dict[str, Any] = field(default_factory=lambda: dict[str, Any]())
    required: tuple[str, ...] = ()
    kind: str = READ            # READ: only looks; ACT: changes something; RISKY: spends, throws away, sends or closes

    def schema(self) -> dict[str, Any]:
        out: dict[str, Any] = {"type": "object", "properties": self.properties}
        if self.required:
            out["required"] = list(self.required)
        return out

    def annotations(self) -> dict[str, Any]:
        return {"readOnlyHint": self.kind == READ, "destructiveHint": self.kind == RISKY,
                "openWorldHint": False}


def _s(description: str, **more: Any) -> dict[str, Any]:
    return {"type": "string", "description": description, **more}


def _i(description: str, **more: Any) -> dict[str, Any]:
    return {"type": "integer", "description": description, **more}


def _b(description: str) -> dict[str, Any]:
    return {"type": "boolean", "description": description}


GAME = {"game": {"type": ["string", "integer"],
                 "description": "Which game: the character's name as list_games shows it, or the game's pid. "
                                "May be left out when only one game is open."}}
CONFIRM = {"confirm": _b("Must be true. Ask the player first: this can't be undone or affects the game.")}
TOOL_NAMES = ("gem_maker", "enhance", "chores", "gather", "dungeon", "lose_xp", "restock", "sell_collection",
              "sell_shards", "clean_bag", "store_items", "update_shard_prices", "survey")
PERIODS = ("run", "today", "yesterday", "day", "week", "month", "all")
MEM_PARTS = ("all", "state", "self", "bag", "slots", "skills", "equipment", "beasts", "pets", "modes", "ui",
             "entities")

TOOLS: tuple[Tool, ...] = (
    # ---------------------------------------------------------------- looking
    Tool("status", "Uncle Farmer's version, the open games (pid, character, map, whether a bot runs, what it runs, "
                   "paused, its last log line), how many plans and scripts there are, the agent's install state "
                   "and whether raw agent commands are allowed. Start here."),
    Tool("list_games", "The open Mist World games with the agent: pid, character, server, map, and the run on each.",
         {"refresh": _b("Look for newly opened or closed games first.")}),
    Tool("game_state", "A game's live state read from the game itself. part=summary (default): map, position, HP, "
                       "MP, pet, bag load, drop time, nearby players and monsters. Other parts give the agent's raw "
                       "reading: all, state, self, bag, slots, skills, equipment, beasts, pets, modes, ui, entities.",
         {**GAME, "part": _s("summary or one of the agent's parts.", enum=["summary", *MEM_PARTS])}),
    Tool("read_log", "Lines the bot wrote to its Log tab (what every run does and says), oldest first. Each has a "
                     "number: pass the last number you saw as after to get only newer lines.",
         {"after": _i("Only lines after this number."), "limit": _i("At most this many (default 100, most 500)."),
          **GAME, "important_only": _b("Only the lines the bot also speaks.")}),
    Tool("wait_for_log", "Wait until the bot writes a log line after the given number (optionally one containing a "
                         "text), then return the new lines. Gives up after timeout seconds (default 30, most 300).",
         {"after": _i("The last line number you have."), "contains": _s("Wait for a line containing this text."),
          "timeout": _i("Seconds."), **GAME}, ("after",)),
    Tool("list_plans", "Every saved plan and script, with a one-line summary of each plan."),
    Tool("read_plan", "A saved plan: its settings as JSON (the format save_plan takes) and the script it runs as.",
         {"name": _s("The plan's name.")}, ("name",)),
    Tool("read_script", "A saved script's text.", {"name": _s("The script's name.")}, ("name",)),
    Tool("script_reference", "The script language: every command with its options, conditions, variables, and the "
                             "commands trusted players can send by private message. Read it before writing scripts."),
    Tool("check_script", "Check script text for errors without running it.", {"text": _s("The script.")}, ("text",)),
    Tool("list_characters", "Every character with settings: its profile name, display name and server."),
    Tool("get_character_settings", "A character's settings (fighting, potions, pets, travel, triggers, bag rules and "
                                   "supplies, tools' choices, keys). keys picks some; schema=true adds each setting's "
                                   "type and default.",
         {"character": _s("Profile name or display name; left out: the character in the given or only game."),
          **GAME, "keys": {"type": "array", "items": {"type": "string"}, "description": "Only these settings."},
          "schema": _b("Add every setting's type and default.")}),
    Tool("get_app_settings", "Uncle Farmer's own settings (game folder, speech, farming day, logging, updates, "
                             "private message and chat settings, the Sound Silencer list). schema=true adds types.",
         {"keys": {"type": "array", "items": {"type": "string"}}, "schema": _b("Add every setting's type.")}),
    Tool("list_schedules", "Every schedule: id, what it runs for which character, when, on or off, when it runs "
                           "next, and its history.", {"history": _b("Add each schedule's history.")}),
    Tool("results", "What a character earned: kills, contribution, experience, arnebia, shards, items, potions, "
                    "skills used, healing, time. period: run (this or the last run), today, yesterday, day (with "
                    "day=YYYY-MM-DD), week, month, all. kind: farming (default) or tools (Gem Maker, Enhancer, "
                    "chores...).",
         {"character": _s("Profile or display name; left out: the given or only game's character."), **GAME,
          "period": _s("Which period.", enum=list(PERIODS)), "day": _s("YYYY-MM-DD, for period=day."),
          "kind": _s("farming or tools.", enum=["farming", "tools"])}),
    Tool("result_days", "The days a character has results for, newest first.",
         {"character": _s("Profile or display name."), **GAME}),
    Tool("read_chat", "Chat lines a game has seen since it opened (kept in memory only). channel: global, map, "
                      "nearby, gang, team, international, private_channel, private (private messages), notice, or "
                      "all.",
         {**GAME, "channel": _s("Which channel (default all)."), "limit": _i("At most this many (default 100).")}),
    Tool("read_conversations", "A game's private conversations: who, their id, the last line, how many lines.",
         GAME),
    Tool("get_messages_settings", "The private-message settings: trusted players, the reply and goodbye lines for "
                                  "strangers, and when replies and speech happen."),
    Tool("get_sound_silencer", "The Sound Silencer's saved list: sound id, name, muted or not."),
    Tool("agent_status", "Whether the game agent is installed in the game folder, which games run without this "
                         "version's agent, and the game folder."),
    Tool("check_for_updates", "Ask GitHub for this channel's newest release; says whether it is newer than this copy."),

    # ---------------------------------------------------------------- doing
    Tool("select_game", "Select a game in the Games list (what the player's own keys then act on).", GAME, kind=ACT),
    Tool("start_plan", "Start a saved plan or script on a game, as the Start button does. Left out: what that "
                       "character ran last.",
         {**GAME, "name": _s("The plan or script."), "type": _s("plan or script (found by name when left out).",
                                                                enum=["plan", "script"])}, kind=ACT),
    Tool("stop", "Stop a game's run the safe way, as the Stop button does.", GAME, kind=ACT),
    Tool("stop_all", "Stop every running bot.", kind=ACT),
    Tool("pause", "Pause a game's run where it is (keys let go, the run not ended), so the player can play by hand.",
         GAME, kind=ACT),
    Tool("resume", "Let a paused run go on.", GAME, kind=ACT),
    Tool("run_script", "Run script text on a game now, without saving it. mode=job (default) runs it as the Tools "
                       "menu's jobs do: results kept, the end place and daily stop apply. mode=errand runs it as the "
                       "walking assistant does: it stays where it ends. Read script_reference first. Commands in it "
                       "can spend arnebia, sell, throw away or send messages: ask the player first when they do.",
         {**GAME, "text": _s("The script."), "title": _s("A name for it in the log."),
          "mode": _s("job or errand.", enum=["job", "errand"])}, ("text",), kind=RISKY),
    Tool("run_tool", "Run one of the bot's jobs on a game, as its Tools menu entry does, with the choices saved in "
                     "the character's settings (change them with set_character_settings first): gem_maker, enhance, "
                     "chores, gather, dungeon, lose_xp, restock, sell_collection, sell_shards, clean_bag, "
                     "store_items, update_shard_prices, survey. check_only reads prices and chances and spends "
                     "nothing (gem_maker, enhance, chores, gather, lose_xp). Spending, selling and throwing away "
                     "are real: confirm must be true for those.",
         {**GAME, "tool": _s("Which job.", enum=list(TOOL_NAMES)), "check_only": _b("Only look, spend nothing."),
          **CONFIRM}, ("tool",), kind=RISKY),
    Tool("follow_player", "The game's character follows a player, helps in their fights (and heals, as a Priest or "
                          "Sorceress) until unfollow_player. A run going is stopped first.",
         {**GAME, "player": _s("The player's name.")}, ("player",), kind=ACT),
    Tool("unfollow_player", "Stop following.", GAME, kind=ACT),
    Tool("follow_buffs", "While following, keep the character's buffs up (on) or not (off, the default).",
         {**GAME, "on": _b("Buffs on or off.")}, ("on",), kind=ACT),
    Tool("team", "Team actions in the game: accept a player's application to join our team, make a player the "
                 "team leader, or leave the team. Done between two steps of a run, or at once without one.",
         {**GAME, "action": _s("accept, leader or leave.", enum=["accept", "leader", "leave"]),
          "player": _s("The player, for accept and leader.")}, ("action",), kind=ACT),
    Tool("voice_message", "Voice messages: play one heard in chat (its voice name from read_chat), record from the "
                          "game's microphone, send the recording to team or gang (channel) or to a player (to), or "
                          "cancel the recording. Sending is as the player: ask first.",
         {**GAME, "action": _s("play, record, send or cancel.", enum=["play", "record", "send", "cancel"]),
          "voice": _s("For play: the voice name."), "channel": _s("For send: team or gang."),
          "to": _s("For send: a player's name or id."), "confirm": _b("For send: must be true.")},
         ("action",), kind=RISKY),
    Tool("scan_character", "Scan the game's character again: class, skills on keys, talents, potions, beasts, pets, "
                           "bag. Not while a bot runs on that game.", GAME, kind=ACT),
    Tool("wait_for_run", "Wait until the run on a game ends (default 60 seconds, most 300); returns whether it ended "
                         "and its last log lines.", {**GAME, "timeout": _i("Seconds.")}, kind=READ),
    Tool("save_plan", "Save a plan (create or replace), in the JSON format read_plan gives. Checked before saving.",
         {"plan": {"type": "object", "description": "The plan, with its name."},
          "replace": _b("Must be true to replace a saved plan of that name.")}, ("plan",), kind=ACT),
    Tool("save_script", "Save a script (create or replace). Checked before saving.",
         {"name": _s("The script's name."), "text": _s("The script."),
          "replace": _b("Must be true to replace a saved script of that name.")}, ("name", "text"), kind=ACT),
    Tool("delete_plan", "Delete a saved plan or script for good.",
         {"name": _s("Its name."), "type": _s("plan or script.", enum=["plan", "script"]), **CONFIRM},
         ("name", "type", "confirm"), kind=RISKY),
    Tool("export_plan", "Write a plan to a portable file another Uncle Farmer can import.",
         {"name": _s("The plan."), "path": _s("Where to write it (a full path).")}, ("name", "path"), kind=ACT),
    Tool("import_plan", "Import a plan from a file.", {"path": _s("The file."),
                                                       "replace": _b("Must be true to replace a plan of that name.")},
         ("path",), kind=ACT),
    Tool("set_character_settings", "Change a character's settings. values maps setting names to new values; each is "
                                   "checked against its type and nothing is saved when one is wrong. Read "
                                   "get_character_settings with schema=true first.",
         {"character": _s("Profile or display name; left out: the given or only game's character."), **GAME,
          "values": {"type": "object", "description": "Setting name -> new value."}}, ("values",), kind=ACT),
    Tool("set_app_settings", "Change Uncle Farmer's own settings (not the control switches). values maps names to "
                             "values, checked against their types. A new language needs a restart.",
         {"values": {"type": "object"}}, ("values",), kind=ACT),
    Tool("export_character_settings", "Write a character's choices to a portable file (no scan, no hearthstone home).",
         {"character": _s("Profile or display name."), **GAME, "path": _s("A full path.")}, ("path",), kind=ACT),
    Tool("import_character_settings", "Load a character-settings file into a character, replacing its choices.",
         {"character": _s("Profile or display name."), **GAME, "path": _s("The file."), **CONFIRM},
         ("path", "confirm"), kind=RISKY),
    Tool("add_schedule", "Add a schedule. repeat: once (date YYYY-MM-DD and time HH:MM), daily (time), weekly "
                         "(time and days, 0=Monday..6=Sunday).",
         {"character": _s("Profile or display name."), "name": _s("The plan or script."),
          "type": _s("plan or script.", enum=["plan", "script"]), "repeat": _s("once, daily or weekly.",
                                                                                enum=["once", "daily", "weekly"]),
          "time": _s("HH:MM."), "date": _s("YYYY-MM-DD, for once."),
          "days": {"type": "array", "items": {"type": "integer"}, "description": "0=Monday .. 6=Sunday."},
          "enabled": _b("On (default true).")}, ("character", "name", "repeat", "time"), kind=ACT),
    Tool("update_schedule", "Change a schedule; give only what changes (same fields as add_schedule).",
         {"id": _s("The schedule's id."), "fields": {"type": "object"}}, ("id", "fields"), kind=ACT),
    Tool("set_schedule_enabled", "Turn a schedule on or off.", {"id": _s("Its id."), "enabled": _b("On or off.")},
         ("id", "enabled"), kind=ACT),
    Tool("delete_schedule", "Delete a schedule and its history.", {"id": _s("Its id."), **CONFIRM},
         ("id", "confirm"), kind=RISKY),
    Tool("send_chat", "Send a line on a chat channel of the game, as the player. Ask the player first.",
         {**GAME, "channel": _s("global, map, nearby, gang, team, international or private_channel."),
          "text": _s("The line."), **CONFIRM}, ("channel", "text", "confirm"), kind=RISKY),
    Tool("send_private_message", "Send a private message to a player, as the player. Ask the player first.",
         {**GAME, "to": _s("The player's name or id."), "text": _s("The message."), **CONFIRM},
         ("to", "text", "confirm"), kind=RISKY),
    Tool("set_messages_settings", "Change the private-message settings: trusted (list of names or ids), replies and "
                                  "goodbyes (lists of lines), and any pm_ setting (see get_messages_settings).",
         {"trusted": {"type": "array", "items": {"type": "string"}},
          "replies": {"type": "array", "items": {"type": "string"}},
          "goodbyes": {"type": "array", "items": {"type": "string"}},
          "values": {"type": "object", "description": "pm_ settings."}}, kind=ACT),
    Tool("forget_answered", "Let every stranger get the automatic replies again.", kind=ACT),
    Tool("set_game_speech", "Mute or unmute a game's own speech (or every game's).",
         {**GAME, "talk": _b("true: unmute, false: mute."), "every": _b("Every game.")}, ("talk",), kind=ACT),
    Tool("speak_results", "Speak a game's one-line results summary through the screen reader.", GAME, kind=ACT),
    Tool("set_sound_silencer", "Replace the Sound Silencer's list and apply it to the open games.",
         {"rows": {"type": "array", "items": {"type": "object"},
                   "description": "Each {\"id\": 1-99999, \"name\": text, \"muted\": true/false}."}}, ("rows",),
         kind=ACT),
    Tool("open_game_window", "Start one more Mist World (the agent must be installed).", kind=ACT),
    Tool("close_game", "Close a game's window. Its run stops first.", {**GAME, **CONFIRM}, ("confirm",), kind=RISKY),
    Tool("install_agent", "Install (or reinstall) the agent in the game folder. Every open game closes first, and "
                          "must be started again. Not while a bot runs.",
         {"folder": _s("The Mist World folder; left out: the one in Settings."), **CONFIRM}, ("confirm",), kind=RISKY),
    Tool("remove_agent", "Take the agent out of the game's settings.", {"folder": _s("The game folder."), **CONFIRM},
         ("confirm",), kind=RISKY),
    Tool("install_update", "Download and install the newest release: Uncle Farmer closes and starts again (open "
                           "games close first). Not while a bot runs.", CONFIRM, ("confirm",), kind=RISKY),
    Tool("clear_log", "Empty the Log tab.", CONFIRM, ("confirm",), kind=RISKY),
    Tool("quit", "Close Uncle Farmer. Running bots stop first.", CONFIRM, ("confirm",), kind=RISKY),
    Tool("agent_command", "Send one raw command to a game's agent and return its answer (keys, typing, menus, any "
                          "agent command). Only when the player allowed raw agent commands in Settings. Can do "
                          "anything in the game: ask the player first.",
         {**GAME, "command": _s("The agent command line, e.g. \"mem self\" or \"key f1\"."), **CONFIRM},
         ("command", "confirm"), kind=RISKY),
)
BY_NAME = {t.name: t for t in TOOLS}


def setup_prompt(exe: str) -> str:
    """What Settings copies for the player to paste into their AI assistant."""
    config = json.dumps({"mcpServers": {"uncle-farmer": {"command": exe, "args": ["--mcp"]}}}, indent=2)
    return """Please connect yourself to Uncle Farmer (Mist Bot), a farming bot for the game Mist World on my Windows computer, so you can run it for me. Answer me in the language I write to you in, and keep your steps short and plain: I use a screen reader.

What to set up: a local MCP server (Model Context Protocol) that runs over standard input and output (stdio). It needs no download, no install and no API key; it is part of Uncle Farmer.
- Name: uncle-farmer
- Command: %(exe)s
- Arguments: --mcp

In the JSON format most apps use (claude_desktop_config.json, Cursor, Windsurf and others):

%(config)s

For Claude Code, the command is:
claude mcp add uncle-farmer -- "%(exe)s" --mcp

If you can change your own MCP settings, add the server yourself and tell me when it's done, and whether I need to restart you. If you can't, tell me step by step where I add it in the app I'm using you in. If your app only takes remote MCP servers (a web address), tell me plainly that it can't use Uncle Farmer as it is.

Good to know:
- Uncle Farmer answers only while its setting "Let other programs on this computer control Uncle Farmer (MCP)" is on (File, Settings, Control). I have turned it on.
- If Uncle Farmer isn't open, the server starts it.
- To check that it works, call the status tool and tell me which games are open.
- What you do is real, as if I had done it. Ask me before you spend arnebia, sell or throw away items, send messages to other players, close games or delete anything.""" % {
        "exe": exe, "config": config}
