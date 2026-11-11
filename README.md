# Uncle Farmer (Mist Bot)

A free, open-source farming bot for Mist World, for Windows. It needs NVDA set as the game's default
speech.

This is Mist Bot, a modified version of [Uncle Farmer](https://github.com/afnannasir/uncle-farmer) by
its authors. It has been changed since 5 November 2026, it builds to a single exe, and it takes its
updates from this repository's releases. It stays under the same GPL v3 licence.

Uncle Farmer walks your character to the farming map, fights, drinks potions, looks after your pets,
sorts your bag, does your daily chores, and goes home when you tell it to. You don't need an account
or a subscription.

## Why it's free

The paid Mist World bots work well, and the people who make them put real work into them. They run
through an online account, though, and with a closed program inside your game you can't check what it
does. Some players who can't pay turn to cracked copies, which isn't fair to those makers and can bring
anything onto your computer.

Uncle Farmer is free, and all of its code is here: you can read it, check it and build it yourself. If
you're happy with a paid bot, keep using it.

## Privacy

- There's no account, no server, no licence check and no telemetry.
- When it starts, and every 6 hours while it's open, Uncle Farmer asks this repository's releases
  page whether there's a newer version.
  That request carries nothing about you or your game. Untick "Look for a new version when Uncle
  Farmer starts" in Settings and it never goes online; it works the same without internet.
- Character settings, plans, scripts, logs and results are plain files next to the program. Delete
  the folder and they're gone.
- The Java agent inside the game listens on `127.0.0.1` only, and refuses any connection that doesn't
  know the secret it makes up at each launch.
- The agent reads the game's network messages to know where you are and what's around you, but it
  doesn't write chats or packets to disk. The Chat window keeps chat in memory only. Private messages
  sent to your character while the bot runs are noted in your own log file in the `logs` folder, and
  go nowhere else.

## What it does

- Plans, without programming: pick maps, how long to farm each one, how to move around and which
  monsters to fight. Stop after a time, at a clock time, after a number of kills, or when an item runs
  low, then end where you choose.
- Scripts, in a small language with loops, conditions and stop rules, for anything a plan can't do.
- It scans each character itself: class, skills on every key, talents and combos, potions, fusion
  beasts and pets. You don't type them in.
- Fighting: each class fights from its own attack's distance and picks skills by cooldown, rage, marks
  and combos. It uses shields and heals when a pack is on it. Skills are pressed through the game
  itself, so keys you hold in another window don't get in the way.
- Potions: it reads when to drink from the potion's own text, so HP and MP stay near full without
  waste. Potions in the bag work too, even mid-fight.
- The bag: every shard and item goes to Throw away, Keep, Store or Sell. It refills potions and food
  from the storehouse or the shop, unloads or stops when the bag is full, and stops when the day's drop
  time runs out.
- Daily chores, once a game day each: bank income, hunting bounties, free pet rebirths, gang donation
  and construction, and sharing arnebia in the secret room.
- Gem Maker turns shards into gems and gems into higher ones; Equipment Enhancer enhances your gear
  with protection runes. Neither spends below your arnebia reserve.
- Pets and beasts: it keeps your favourite pet out, fed and healed, rides your fastest beast between
  maps and fights in your strongest one.
- Travel between any two of the game's 375 maps, using cable cars and airships, or just walk to a map
  or a dungeon entrance.
- Several games at once: each game window runs its own plan, and its title says which character it is.
- Teams: `come` and `follow` by private message, team navigation, and healers that heal the player they
  follow.
- Chat: read and write every channel, and play or send voice messages while you farm. It can answer
  strangers politely while you're away and take commands from friends you trust.
- Results: kills, contribution, experience, arnebia and every shard picked up (and how many were thrown
  away, sold or stored), for this run, today, this week or all time. Gem making and chores are counted
  apart from farming.
- It works with the game's language packs. The program itself is in English and Roman Urdu.

## Requirements

- Windows and Mist World.
- NVDA, set as the game's default speech.

## Getting started

1. Download `MistBot-<version>.zip` from this repository's [Releases](https://github.com/ernie96/mist-bot/releases)
   and unpack it where you want the bot to live. It holds `UncleFarmer.exe` in a `Mist Bot` folder;
   your settings, plans and results are kept in that folder. (`UncleFarmer.exe` is also on the
   release by itself, for the updater and for replacing an older copy by hand.)
2. Run `UncleFarmer.exe`. The first time, it opens Settings: choose your Mist World folder (or start
   the game and press Find the running game) and press Install.
3. Restart Mist World and log in. Make a plan in the Plans tab (pick a map and how long), then press
   Start on the Bot tab.

The Pause key starts and stops the bot from anywhere, even inside the game. Shift+Pause speaks your
results.

New versions: Uncle Farmer offers them when it starts, every 6 hours while it's open (once no bot is
running), or from Help, Check for updates, and installs them for you. If games are open, it asks first and closes them, because an open game holds the agent file;
start them again after the update. Releases are signed, and Uncle Farmer only installs one whose
signature checks. You can also put a newer `UncleFarmer.exe` in place of yours with every game and
Uncle Farmer closed. Your characters, plans and settings aren't part of a release, so they stay.

When the agent needs installing again (another tool removed it from the game, Uncle Farmer moved to
another folder, or an open game started without this version's agent), Uncle Farmer says why when it
starts. Press OK: it closes every Mist World window and reinstalls the agent. Then start the game
again.

The full guide is in [docs/USER_GUIDE.md](docs/USER_GUIDE.md), as README.html in the program's folder,
and in the program under Help (F1). Other guides, also under Help:

- [Writing scripts](docs/SCRIPTING.md): from your first three lines to full examples.
- [How the game works](docs/GAME_GUIDE.md): Mist World's rules and systems, from the game's own help
  and texts.
- [What to automate next](docs/ROADMAP.md): the plan, and where you can help.
- [Performance](docs/PERFORMANCE.md): where a decision's time goes, and how to rerun the benchmarks.
- [What's new](CHANGELOG.md): the changes in each version.

Install adds one line to the game's `mw.exe.vmoptions` and keeps the original as
`mw.exe.vmoptions.bak-unclefarmer`. Remove, in the same place, takes the line out again.

### Running from source

You need Windows, [uv](https://docs.astral.sh/uv/) (`winget install astral-sh.uv`), and a JDK 9 or
newer for the game agent. uv brings the right Python itself: 3.14, the only one Uncle Farmer supports.

```
uv sync
uv run python agent/build_agent.py
uv run python agent/java_tests.py       # the agent's own tests, then the random-byte parser check
uv run UncleFarmer.pyw
```

`uv sync` installs the exact versions pinned in `uv.lock` into `.venv`: the app's packages, the
checking tools and Nuitka. Every dependency is listed in `pyproject.toml`.

Without uv, pip installs the same pinned versions (with Python 3.14 from python.org):

```
py -3.14 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python agent/build_agent.py
.venv\Scripts\python UncleFarmer.pyw
```

`requirements.txt` is what the app needs to run; `requirements-dev.txt` adds the checking tools
(`python check.py`) and Nuitka (`python build_exe.py`).

`uv run python build_exe.py` builds one file, `dist\Uncle Farmer\UncleFarmer.exe`, with Nuitka.
Put it in a folder of its own: it unpacks itself to your cache folder, puts the game agent in an
`agent` folder beside itself, and keeps your settings, plans and results there too.
`uv run python build_native.py` builds the optional C module that makes map searches 10 to 24 times
faster; without it the same searches run in Python.

## How it works

```
Mist World (Java)                         Uncle Farmer (Python, wxPython)
+------------------------------+          +------------------------------+
| agent (unclefarmer-agent.jar)| loopback | link.py   talks to the agent |
|  World   reads the game's    |<-------->| engine/   bot, combat, travel|
|          network messages    |  secret  |           bag, potions, pets |
|  Keys    presses keys through|          | gui/      the windows        |
|          the game's own keys |          | data/     maps, NPCs, items  |
|  StateServer  127.0.0.1 only |          +------------------------------+
+------------------------------+
```

The game loads the agent itself (`-javaagent`). The agent keeps a model of the world from the game's
own messages and reads the game's own objects (your position, bag, target and dialogs). It presses
keys and skills through the same handlers the keyboard uses, so the game window doesn't need to be in
front. The Python app decides what to do next.

- `unclefarmer/` is the app: `engine/` (the bot), `gui/` (the windows), plus scanning and travel.
  The bot itself (`engine/bot.py`) is put together from one part per job in `engine/botparts/`:
  reading the game, keys, health and potions, walking, the bag, travel, NPC dialogs, fighting and
  farming. Skill choice is `engine/combat.py`, talent combos `engine/combos.py`, the results
  `stats.py`.
- `agent/src/` is the Java agent, with its own tests in `agent/test/`.
- `data/` is what the bot knows about the game: maps, walls, exits, NPCs, shops, skills and shards.
- `lang/unclefarmer.pot` holds every string, for translators. Translations are gettext catalogs.
- `tests/` checks it all without the game, against a pretend game that speaks the agent's protocol.

## Helping

You don't have to be a programmer to help:

- Report a bug: [open an issue](https://github.com/ernie96/mist-bot/issues) and say what you did,
  what you expected, and what happened. Attach the day's file from the `logs` folder if you can, and
  `logs/bootup.log` or `logs/teardown.log` if Uncle Farmer won't open or won't close.
- Send a fix. Pull requests of any size are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).
- Translate it: copy `lang/unclefarmer.pot` to `lang/<your language code>.po`, fill in the `msgstr`
  lines and run `python -m unclefarmer --strings` to compile them.
- Tell us about maps where the bot gets stuck, NPC menus it doesn't understand yet, good farming
  spots, and plans or scripts that work well.
- Try new versions and say how they went.

## Donations

Uncle Farmer is free. If you'd like to give something back, you can donate with
[PayPal](https://paypal.me/RefinnejLTD) or [Ko-fi](https://ko-fi.com/ernie96) (in the app: Help,
Donate).

## Contact

Email [ernesto@melendez.land](mailto:ernesto@melendez.land), or on Mastodon
[ernie@someplace.social](https://someplace.social/@ernie). Bugs are best reported as an
[issue](https://github.com/ernie96/mist-bot/issues), so everyone can see the fix. In the app, Help,
Contact the developer shows these too.

New versions are announced in the [Telegram channel](https://t.me/+-SHI1xTKJugwMzQ5) (in the app:
Help, Telegram updates channel).

## Play fair

Using a bot may be against Mist World's rules, so you use Uncle Farmer at your own risk. Don't use it
to harass other players, and please don't crack anyone's paid software.

## Licence

Copyright (C) 2026 the Uncle Farmer authors.

Uncle Farmer is free software under the GNU General Public License v3.0. You may use, change and share
it, and any version you share must stay open source under the same licence. See [LICENSE](LICENSE).

`nvdaControllerClient64.dll` is part of NVDA by NV Access and comes under its own licence; see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Thanks

To NV Access for NVDA, to the wxPython team, to everyone who has sent code, and to the players who
report bugs, translate and share maps.
