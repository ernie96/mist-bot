# Uncle Farmer user guide

A farming bot for Mist World. It needs NVDA set as the game's default speech.

## What it does

Uncle Farmer walks your character to a farming map, fights the monsters there, drinks potions when
HP gets low, and stops by itself when a rule you set is reached (time, kills, potions running low).
It reads the game directly, so it knows exact positions, HP, your bag and every monster around you.
It works with the game in the background, and it needs no drivers and no virtual machine.

Important events are spoken through NVDA.

## Installing

1. Put UncleFarmer.exe in a folder of its own, for example in your Documents. Your settings,
   plans and logs will be kept beside it.
2. Start **UncleFarmer.exe**. The first time, it offers to open Settings.
3. In Settings, Game tab, choose your Mist World folder (the one with mw.exe), or start the game
   first and press **Find the running game**. Press **Install**. (Once the agent is installed,
   Uncle Farmer finds the game folder by itself, even if the setting is lost.)
4. Restart Mist World. That's all.

The installer adds one line to the game's file mw.exe.vmoptions and keeps a copy of the original
as mw.exe.vmoptions.bak-unclefarmer. **Remove**, in the same place, takes the line out again. If you
move the Uncle Farmer folder, install the agent again so the line points to the new place.

**When the agent needs installing again**, Uncle Farmer says so when it starts, and why: another
tool removed it from the game's settings, the game loads another Uncle Farmer's agent (an older
copy, or this one before it moved), or a game that is open started without this version's agent.
Press **OK**: Uncle Farmer closes every Mist World window and installs the agent again. Then start
the game: a game loads the agent only as it starts. Cancel leaves everything as it is. Pressing
Install in Settings while games are open offers the same.

## The main window

The main window has three tabs (Ctrl+1, Ctrl+2, Ctrl+3):

- **Bot:** your games, the plan to run, Start and Stop, and live status: what the bot is doing,
  where, HP, MP, your pet's HP and MP, the players near you (with how many steps away), the bag,
  the drop time and this run's kills.
- **Plans:** your plans and scripts, with a summary of the selected one.
- **Log:** everything the bot did, or only the important events.

Each game in the Games list has its own menu: select it and press the Applications key or
Shift+F10, or right-click it. It holds the Tools, Character and Run submenus described below. An
entry that can't be used right now, such as a job while that game's bot runs, is greyed out.

On the Plans tab, New plan and New script are buttons. Everything else for the selected plan or
script is in its menu: Run selected, Edit, Duplicate, Export, Delete, New plan, New script and
Import. Enter edits it and Delete deletes it. In the Log tab, select text and choose Copy
selection from the log's menu to copy it.

The menu bar has:

- **File:** Settings, the log and results folders, and Exit.
- **View:** the three tabs.
- **Game:** mute and unmute this game or every game, and Open another game window.
- **Messages:** Private messages, Chat, and Let everyone get replies again.
- **Plans:** New plan, New script, Edit, Duplicate, Delete, and Import or export plans.
- **Help:** the guides, keyboard shortcuts, script commands, commands for trusted players, Check
  for updates, contact, the Telegram updates channel, Donate, and About.

**Tools**, **Character** and **Run** are not on the menu bar. They are submenus of each game's own
menu in the Games list (select the game, then the Applications key or Shift+F10):

- **Tools:** Gem Maker, Gem Breaker, Equipment Enhancer, Daily chores, Hunting bounties,
  Construction scanner, Gathering, Dungeons, XP loser, Market searcher and buyer, Sound Silencer, and the jobs that run at once: Sell the collection now, Sell shards now, Clean the bag
  now, Store items now, Restock now and Update shard prices.
- **Character:** Settings, Bag and supplies, Scan now, Another character, and Export or Import
  character settings.
- **Run:** Start, Stop, Pause or go on, Stop every bot, Walk to a dungeon or map, Schedules, Results
  and Speak the results.

Their keys (F5, F6, Ctrl+G, Ctrl+P, Ctrl+B and the rest) work from the main window without opening
the menu. Where this guide says Tools, Character or Run, it means these submenus.

Entries that can't be used right now are greyed out: Start while the selected game's bot runs, or
Duplicate when a script, not a plan, is selected.

Help, Quick guide (F1) explains everything step by step, and Help, Keyboard shortcuts lists every
key. The **Pause** key starts and stops the bot from anywhere, including while you are playing.
To hold a run without ending it, use the **Pause** button on the Bot tab (or F6): the bot lets go of
every key and your own Shift, Ctrl and Alt work in the game again, so you can play by hand. **Go
on** (the same button, or F6 again) carries on where it stopped.

The kill count is the game's own: every monster that dies with one of your hits on it counts,
including the ones your area skills kill and the ones another player finishes.

Once an hour while farming, the log says where the time went: searching, walking to monsters,
selecting, fighting, resting, town trips. Few kills an hour with a lot of searching means the spot
is crowded, or its movement setting suits it badly.

Everything the bot did is also written to the program's `logs` folder, one file per day, and a
crash keeps its traceback in `errors.log` beside it. Settings, Logging chooses how much goes into
those files and how big they may grow before the oldest are dropped; the Log tab always shows the
run's lines whatever is chosen there.

Two more files there say how Uncle Farmer itself started and closed. `bootup.log` has a block for
each start: settings, language, the window, the hotkeys, the update check and the agent, each
"started" and then "done" or "FAILED" with the error, and an END line: "ready", or the step it
failed at. `teardown.log` does the same for each close: stopping the bots (one that doesn't end
within 5 seconds is noted), the message and chat readers, the hotkeys and the timer, then "closed".
If Uncle Farmer won't open, or hangs while closing, these two files say where. They are written
whatever Settings, Logging says, as `errors.log` is, and rotate the same way.

## Plans

A plan answers three questions, one tab each.

### Where to farm

One or more farming spots (map, movement, which monsters). With one spot it farms there until the
plan stops. With several it goes round them in turn, or through them once; each spot then says how
long before moving on.

Movement: wander at random, or walk a patrol loop. The short loop is the quickest lap that still
passes within 40 steps of nearly every spot, and the best choice in mazes such as turkey cave. On
any loop the bot goes after monsters within 40 walking steps and leaves the rest until the lap
brings it near them.

"My own points, in order, round and round" goes round up to 10 points you choose. Stand where a
point should be and press "Add where I stand", or type them in the Patrol points box as `x,y`,
separated by semicolons. The bot goes to each in turn, fighting what comes near, then starts again.

**No-go circles** (same tab) keep the bot out of parts of the map: no monster inside one is looked
for, and the patrol never heads into one. A monster that attacks from inside is still fought. Stand
in the middle, set "Radius of a new circle" and press "Add a circle around me", or type them as
`x,y,radius`, separated by semicolons.

**Sharing the day's drop time between spots.** A spot's minutes count from when it began, so a
restart starts them again. To split the day between maps (three hours on Underwater World, the rest
on Margit Rainforest), tick "A share of the day's drop time (kept across restarts)" on the first
spot's Farming tab and set "Minutes of drop time on this spot" to 180. The share counts on the
game's 7-hour drop time: the first spot farms until 4 hours are left, the next gets the rest, and a
restart after two hours farms only the first spot's last hour. Not tested in the game yet.

### When to stop

A time limit, a clock time, a kill count, an item running low. The drop time, the next level
coming close (if you ask for it), a full bag, the last death you allow, broken gear and the last
potion used up stop it by themselves (character settings). A plan can set its own drop time to
save, or stop before the next level, in place of the character's setting.

### Where to end

Back where you started the bot (the default; if monsters spawn there, the nearest map without
them), a place you choose (or "where I stand now", or a city square), home with the hearthstone,
the nearest map without monsters, or where it is. Every end goes there.

Plans made with older versions open in the new form by themselves: a single step's minutes become
the plan's time limit, and they end back where the run started.

## The farming day

The game's drop time resets at 00:00 GMT (05:00 in Pakistan). Farming past that spends the next
day's drop time, so every run stops at a set time of your computer's clock, whatever the plan says
and whatever the bot is doing, and ends where its plan says. No run starts between that time and the
reset. The time is in File, Settings, Farming day; by default it is the reset minus 10 minutes
(04:50 in Pakistan), to leave time to get away from the monsters.

### Autopilot: the whole day in one window

**Run → Autopilot: the whole day** (Ctrl+Shift+A) shows the logged-in character's day together:

1. the **Before farming** list (for example the day's chores, a cave, restocking), top to bottom;
2. the farming, until the plan ends or the daily stopping time;
3. the **After farming** list (for example selling shards, storing items, the Gem Maker), when the farming ended by itself.

The two lists are the same ones as **Character settings → Triggers**: change them in either place. Three choices decide how the day goes:

- **Farm with:** the character's plan (chosen under **Plan**), or the best map for the character's level. The best map is chosen when the day starts, from field maps whose monsters are 9 levels below to 5 above the character, so it follows the character as it levels up.
- **Run the day as:** the Triggers lists around the farming, or one script of the day. The script is written from the lists and the farming the first time; after that it is yours to read, change or schedule from the Plans tab, and **Write the script of the day now** writes it again from the window. Steps that farm (a cave) are left out of its After part, since the day's farming may be over by then.
- **Start:** only when you press **Start the day**, or every day at the time you write (HH:MM, this computer's clock). The daily start is an ordinary schedule in **Run → Schedules**; choosing "Only when I press Start" again takes it away.

**Save** keeps the choices; **Start the day** saves them and starts the day on that character's game now.

### A lost game, and runs that didn't finish

While a plan or a script runs, Uncle Farmer keeps note of where it is, every 20 seconds: the line it is on, the turn of each loop, how many minutes and kills the current farm has done, the run's own minutes and kills, and the script's `set` values.

**When the game is lost in the middle of a run** (it closed, crashed or froze, or the server logged the character out and logging back in failed), Uncle Farmer closes that game if it is still open, opens a new one, logs in to the same character and carries on where the run was. It says so each time. This happens at most 3 times a day of the game (00:00 GMT to 00:00 GMT) for each character; after that the run ends there. The character's account must be known: log in to it once by hand. To turn this off: **File → Settings → Farming day → When a game is lost during a run**.

When only the connection dropped (your internet for a few minutes), the game isn't closed at once:
Uncle Farmer logs back in inside the same game, again and again, for up to 5 minutes. Before each
try the log says what the game shows, and after a failed one why it failed. A game that came back
by itself while the run was ending is carried on in, not closed. A run never carries on as another
character: if a different character is logged in, it stops.

**When Uncle Farmer itself stopped under a run** (you closed it, an update restarted it, or the computer restarted), the next time it starts it shows the runs that didn't finish. They carry on where they were after 10 seconds; press **Carry on now** to start them at once, or **Don't carry on** (Escape) to forget them. A game is opened and logged in to when the character isn't in one, as a schedule does.

A run is carried on only the same day of the game, and only with the same plan or script: one you edited since starts from its beginning. Lines such as `stop_when` and `keep_drop` count again on the way, so a time limit still counts the minutes already farmed. A run you stopped with **Stop**, one that finished, or one that ended on an error is never carried on.

Each part of a run that was carried on is saved in the results as its own run; at the end, the results said and written in the log add all the parts up.

A slow game is waited for while it starts (up to 4 minutes) instead of a second one being opened beside it; one that never shows the agent in that time is closed.

### After farming

The same tab says what happens when farming stops by itself: the daily stop, the plan's time, the
drop time used up, a full bag, the last death. Never when you press Stop, and never after a run
that didn't farm (the Gem Maker, the Enhancer, Walk to, come, follow). The choices:

- Do nothing.
- Close the game.
- Shut down the computer. A shutdown waits until every running bot has finished and its game is
  closed, then runs Windows' own forced shutdown (shutdown /s /f /t 60, so no program can hold it
  up) after a warning you can cancel: the bot says it, and a window asks "Cancel the shutdown?"
  (Windows' shutdown /a).

## Your character

The bot scans each character by itself (class, skills, keys, potions, fusion beasts, pets).
Character, Settings (Ctrl+P) holds the choices that are yours: how to fight, which potions, which
beast, which pets. Keys and timings are under Advanced.

Advanced, Skills lists every skill the scan found, with its key and what kind of skill it is. For
each one you choose:

- **The bot decides** (the default): the bot picks when to press it.
- **Never**: the bot never presses it, never puts it on an empty key, and never asks you to.
- **Only when HP is low**: kept for bad moments (under the shield and defensive marks on the Low HP
  tab).
- **Whenever it's ready**: pressed in fights as soon as its cooldown allows, before the bot's own
  choice. Use it for a skill the bot leaves alone, such as a stun.

"Skills not in this list" says what happens to a skill you learn or put on a key later. Set it to
Never, and set the skills you want to The bot decides, and the bot uses only the skills you chose.

The other Advanced tabs hold the finer settings: how far to chase monsters on a patrol loop, how
far to keep from bosses, when to rest, when the defensive skills, shields and heal skill come out,
the pet's potions and Rice Rolls, how to travel
(walking, cable cars, airships, travel items, VIP), and the keys for dialogs, discarding and the
Action menu.

The way to anywhere mixes walking with cable cars and airships wherever a ride is shorter: from
Giant Rock City to Tulip City, say, down to its underground and the cable car, then up on foot.
A ride is planned only when it can be taken: transports and airships switched on, and a fare the
character can pay with the arnebia in the bag (rides are free for VIP); otherwise the way is on
foot. The nearest shop or craftsman is judged the same way.

**Bosses.** The bot knows the field bosses by name: Pig-Face Bat King, Man-wolf Caesar, Ice Queen
Los, Cat King Carter, Pharaoh Tar, Elven King Erth, Fire Lord, Whale Monster Bigger, Monkey King,
Barbarian Tyrant, Thunder Lord, Lich King, Meteor Queen Elsa, Dark Priest, Dracula and the rest of
that family, plain and Demonized (data\bosses.json). It never attacks one, nor anything within 40 steps of one, and when a boss
comes within 40 steps it walks to the spot furthest from it, then farms on. Change the 40, or turn
this off, in Advanced, Fighting. The game files don't say when a boss appears, so it reacts to the
bosses it sees.

Every character has its own settings. A character the bot has never seen gets them from its first
scan.

**Teleport skills.** A Mage's Teleportation (city squares) and an Elf's Elven Teleportation (Soul
Burial Village, mist gods Ruins and the other high-level lands) are used for travel whenever they
make the trip shorter; they cost only mana. The bot walks out of a town's safe zone first (no skill
or attack works inside one), deals with anything attacking it, since a hit breaks the 10-second
channel, gets off its fusion beast, and picks the place from the game's list. A skill on no key is
put on an empty skill key. The places are learned from the game's menu the first time. After three
broken tries it goes another way. Character, Settings, Travel, "Use the class's teleport skill
(Mage, Elf)" turns it off.

**Treasure chests.** Now and then the game announces a treasure chest on a farming map ("There's
a Shining Small Chest in Margit Rainforest..."); the first player to open it gets what's inside,
usually arnebia and shards. When one comes into sight while farming, the bot finishes any fight,
walks to it, selects it, presses Enter and chooses "Open the chest", says so, and the results
count it. It leaves a chest near a boss or more than 80 steps out of its way, and one that won't
open is left for five minutes. Advanced, Fighting, "Open the chests that turn up while farming"
turns it off.

**Drop time and the next level.** Character, Settings, Fighting, "Drop time and experience" holds
two reasons to end a run:

- "Stop when the day's drop time runs out" (on by default), with "Drop time to save (minutes)":
  the run ends while that much of the day's public area drop time is still left; 0 uses all of it.
- "Stop before the next level" (off by default), with "Stop when the next level needs less than
  (experience)" (100,000 by default), for a character you keep at its level. The bot reads how
  much experience the next level still needs after every kill; under your number it says so, goes
  somewhere safe and ends the run. It also checks before a run sets out and doesn't start farming
  when the next level is already that close. Inside a dungeon it never leaves (the visit would be
  lost): it says once that the level is close, and it doesn't go into a cave when it already is.

A run that ends this way ended by itself, so the After farming list runs next: put Lose experience
(the XP loser) there to win some experience back. A plan's When to stop page can set either one for
that plan only; in a script, `keep_drop` and `keep_level`.

**Resetting the fighting settings.** Advanced, Fighting, "Reset the fighting settings to their
defaults" puts back what a new character has: the pause between attack keys, the times and casts
to give up a fight, skill pressing, attack range, the chase, target keys, each skill's use, the
fight readings and the fighting boxes of the character window. Keys, bag, supplies and the rest
stay as they are. A profile keeps the values older versions saved in it, so this helps when fights
have become slow, without deleting the profile. Nothing is kept until you save.

**Copying settings from another character.** "Copy from another character", at the bottom of the
character window, takes one part of another character's settings: its Before farming or After
farming list, its fighting settings (never its keys), or its team settings. For the lists, choose
whether the other character's steps are added (the ones only here stay) or replace this list. Each
skill's use is copied only between characters of the same class; for another class the bot asks
first and copies the rest. Nothing is kept until you save. Bag lists are copied from Bag and
supplies.

**Demonized elites.** Some maps have demonized elites (demonized Boar, demonized black bear,
demonized Water Elf...), much stronger than the monsters around them. They are fought like any
other monster unless you tick "Leave demonized elites alone" (Advanced, Fighting); then the bot
never picks one, and only fights one that attacks it.

**When HP stays low.** Character settings, Low HP, "When HP stays low" says what to do when HP
stays under the Low HP mark (30%) for a few seconds (3) whatever the potions and heals did: fight
on (the default), stop so you can take over, or, while farming, go to town with the hearthstone,
heal to 90% (three minutes at most), restock and come back. A hit breaks the hearthstone's cast;
after three tries the bot fights on and doesn't try again for a minute. Without a hearthstone it
says so once and fights on. The third flee within 30 minutes ends the run in town: the map is too
hard for now. Never in a dungeon, on a trip or in town.

**Ride levels.** An airship out of a capital needs a level (26 for Giant Rock City to Sunset City,
up to 86 for Holy Blood City to Dark Night City), and so do the cable cars from Giant Rock City to
Tulip City (45) and to Holy Blood City (60). The bot plans those rides only from that level.

**Bosses that keep coming back.** The patrol keeps clear of bosses seen in the last minute and of
the boss zones in the map data. After three walk-offs from a boss in five minutes, or when there is
nowhere further to go, the bot leaves the map by the nearest door far from it, waits on the other
side (fighting back anything that attacks), and comes back; each time it has to leave again the
wait doubles (1 minute, then 2, 4...). Not tested in the game yet.

**When nothing is killed for a while.** After 10 minutes on the farm without a kill the bot walks
to the part of the farm furthest from where it is; after another 10, again; after 30 minutes it ends
the run the way a used-up drop time does. A farm that fights only some names never stops for this.
A kill, a trip away or a long pause starts the count again, and it never applies in a dungeon.
Advanced, Fighting, "When nothing is killed for a while, try elsewhere, then stop" sets the minutes
or turns it off.

## The bag

Character, Bag and supplies (Ctrl+B):

- **Shards:** sort every shard into Throw away, Keep, Store or Sell. A shard you never sorted is
  kept. Throwing away happens right where you farm; storing and selling happen on a bag trip, so
  for those choose "Sell and store by these lists" on the Full bag page. To make gems, use Tools,
  Gem Maker.
- **Other items:** Keep, Store, Sell or Throw away.
- **Supplies:** which potions and food are refilled, and from where.
- **Full bag:** what happens when the bag is full. (Stopping when the day's drop time runs out is
  in Character, Settings, Fighting, with the next level.)
  Full means full: the bot farms until the load reaches its limit (or stops rising just under it
  while monsters keep dying), unless you set a lower mark there.
- **Equipment picked up while farming:** one box per rarity (Crude, Common, Sophisticated,
  Perfect, Rare, Legendary), none ticked to start with. Pieces of a ticked rarity are thrown away
  where the character stands, every so many minutes of farming (30 to start with) and when the bag
  is full. Only pieces picked up during the run are thrown, never one that was in the bag before,
  and the log names each one with its rarity. With "Keep pieces with a bonus" ticked (the default)
  the bot first asks for each piece's details, as the G key does, and keeps one with a "plus:"
  bonus. Needs the agent that comes with this version: restart the game once after updating.
- **Copy from another character** (at the bottom of the window) takes another character's
  throw-away, sell, storehouse or keep list (each with what it leaves in the bag), its supplies, or
  its Full bag page. Either add to this character's lists (the items only here stay) or replace
  them (an item only here goes back to the bot's default). The window then says what changed, for
  example "Throw-away list: 23 put in, 4 already there". Nothing is kept until you choose Save.

### Storing items now

Store items now, in the game's menu in the Games list, puts into the storehouse what the bag manager's Store list
says (Character, Bag and supplies, "Move to storehouse"), keeping the number each rule keeps in the
bag, and nothing else: items on no list, or on another list, stay where they are. It walks to the
nearest storehouse, the same way a bag trip does. The log says what went in, what was only kept,
what wasn't in the bag, and what the storehouse didn't take (when it is full, whatever didn't fit
stays in the bag). The list is read when the job runs, so a change you just made counts.

A full storehouse still takes more of an item it already holds; one it holds none of is turned
away ("item storage is full"). The bot says which items stay in the bag and doesn't take them
back to the storehouse for the rest of the run, unless something is taken out of it.

### Triggers: jobs before and after farming

Character, Settings, **Triggers** has two lists, Before farming and After farming. The jobs:

- **Sell shards** (Sell shards now in the game's menu): the shards on the Sell list, at the nearest Shard Market.
- **Clean the bag** (Clean the bag now in the game's menu): throws away, where the character stands, only what
  is on the throw-away list.
- **Update shard prices** (Update shard prices in the game's menu).
- **Gathering**, as set in Tools, Gathering.
- **Store items** (Store items now in the game's menu): the Store list, as above.
- **Restock supplies** (Restock now in the game's menu): fills every supply switched on in
  Character, Bag and supplies up to its "fill up to" amount, from the storehouse first and then a
  shop, even when it isn't down to its refill point yet.

Each list runs from top to bottom, one step at a time. A step is one of these jobs or a saved
script; select it and use its menu to switch it off, move it up or down, or edit it. A step can
wait up to an hour after it succeeds before the next one starts ("Delay after success"), and can
be marked DETERMINISTIC: if it fails, the rest of the list is skipped, and in the Before farming
list farming doesn't start either. A step that farms (Dungeons, or a script with a farm or dungeon
line) keeps the daily stop. Profiles from before the lists keep their ticked jobs in their old
order.

"Skip this list when the run starts on its first farming map" is on by default now. Supplies and
the bag are still looked after while farming: the bot goes to town by itself when a supply is down
to its minimum or the bag is full. In these lists Update shard prices is skipped while the prices
are less than 8 hours old (on this PC, by any character), and the log says how old they are.

Above the Before farming list, "Skip this list when the run starts on its first farming map" (off
by default) is for stopping and starting again where the character was farming: a run that starts
on the map its plan farms first leaves the Before farming list out and farms at once, and the log
says so. A run that starts anywhere else, or goes into a dungeon first, runs the list as usual.

**Before farming** runs when a plan, or a script that farms, starts - after the character is
scanned and before the day's chores and the first farming line. **After farming** runs when a
farming run finishes by itself: its plan is done, a stop rule ended it (the drop time, a full bag
set to stop, deaths...), or the daily stop came - and before the game is closed or the computer
shut down if you chose that. Neither runs for a Tools job, the walking assistant, come or follow,
and After farming never runs after Stop or Pause.

The two lists are independent: tick a job in both and it runs once before and once after farming;
unticking one leaves the other as it is. Ticked jobs run one after the other in the order above,
each exactly as from the Tools menu, once per stage. A job that can't finish is said aloud and
logged with the reason, and the next job (and farming) still goes on; Stop ends them. Everything is
off until you tick it, and kept per character. The two after-farming boxes that used to be on the
Travel and pets tab are these same settings: what you had ticked there is ticked here. The Tools
menu items still work by hand whatever the boxes say, and running them by hand changes no setting.

## Fighting and staying alive

The bot stands and fights, however many monsters are on it. It never turns its back on a pack
(they follow as fast as it walks and keep hitting). With a pack on it and HP going, it uses the
class's shields and big heals as well as the potions. Damage shields (Formless...) go up on the way
into a fight and on the way out, not only while hitting. A melee character takes a monster with few
others round it before one in the middle of a pack. With nothing on it but HP low, it rests before
the next fight. Only monsters that attack are fought on the way somewhere.

What counts as a monster is the game's own call, the same one its target key makes: townsfolk,
shops, a town's ducks and hens are NPCs, guards and other players' summons are neither, and none of
them is fought. Before every fight the bot checks the target key (V) is on enemies and puts it back
if not; to talk to an NPC it switches to NPCs.

### Rage, marks and combos

A Warrior or Orc, a Hunter and an Assassin press the accumulation-points key (T) every second and a
half in fights. The game answers with rage, marked targets or combos (then fusion power, and the
pet's amiability), so Execute, Whirlwind Slash or Battle Cry are pressed only with the rage they
need, and Marked Shot when two or more targets carry marks (three or more even for a single
target).

On a busy map, a monster another player stands nearer to is often gone before you get there, so
when two monsters are about as far the bot takes the one nobody else is closer to: one another
player is nearer to counts as 15 steps further away.

### Potions and deaths

When the last red or blue potion is used, the run stops and ends at its end place (Character,
Settings, Potions), unless a restock rule refills that potion; it warns when 20 are left.

After the last death you allow (Character, Settings, Fighting), it respawns in the city first and
only then stops, so the character is never left lying dead. Untick "Stop after too many deaths"
there and it never stops for deaths: it respawns and goes back every time.

### Your own skills

The bot reads which skills you put on which keys (both pages, any keys you chose) and what each one
does from the game's own skill texts, then looks after you with them:

- **Heal:** a Sorceress or Priest heals itself with its quick heal (Healing Wave, Heal) below 85%
  HP, in fights and between them; red potions are then only a backup under half HP. A Priest's
  Recover has no cooldown, so it can go at every chance while HP stays under that mark. Advanced,
  Low HP, "Cast Recover (Priest) at most every this many seconds" sets a gap (16, say); 0, the
  default, means no gap. The gap also holds when Recover heals the pet or a teammate.
- **Buffs:** long ones (Strong-Arm Aura, Battle Cry, Requiem... lasting a minute or more) are kept
  up all the time, cast again when they run out or when the game says one was taken off you; short
  ones (Bull's Eye, Scorch, Winter Horn...) open hard fights and fights against packs.
- **Debuffs:** the R key's answer says how many debuffs are on you; a class with a dispel (Soul
  Purify, Holy Light, Purification, Dispel Magic) removes them. A debuff the dispel can't remove
  (poison, say) is left alone until something changes.
- **Bad moments** (HP under half, or three or more monsters on you under 75%): first a shield that
  doesn't stop you fighting (Formless, Ignore the Pain, Summon Spirit, Ice Shield...), then a big
  heal cast at once (Sorceress totems, Priest Light of Miracles). Under 30% HP, a shield that stops
  attacks is fine too (Turtle Guardian); one that stops you moving (Ice Barrier, Soul of
  Redemption) only as the last thing under 25%.

These skills are cast standing still, never walking you to a monster.

### Combos

Many talents make one skill set up the next. The bot reads which talents you have ACTIVATED (each
class has two paths that exclude each other; a talent on the other path does nothing) and uses
their combos whenever the skills they name are on your keys. The run's log lists them at the start
("combos: ..."), and Character, Overview shows them after a scan. Some of them:

- **Cleave Combo:** Sweep Attack right after Cleave. **Powerful Leap Attack:** Leap Slash to open,
  then the next skill at once (the global cooldown is halved).
- **Ice Finger:** Aqua Jet, an Ice Arrow into it to condense the target, then Ice Lance (3x damage).
  Without any talent: Ice Lance right after Frost Nova freezes, and Ice Arrow instead of Magic Sphere
  (its Ice Spikes add to Ice Lance). **Freezing Cold:** Ice Storm on its shorter cooldown.
- **Enhanced Explosion:** Corrosion Spell on the target, then Skeleton Explosion, which always crits
  on it. **Divine Whip:** Mind Whip kept on the target, Divine Nova while it is.
- **Steady Hands:** Aimed Shot just before Rapid Arrows or Marked Shot. Ignition once Pyroblast and
  Blazing Storm built three fire elements.
- **On a critical hit** (Call of the Wilderness, Flame Combo, Crisp Wisdom, Wisdom, Dead Toxin
  Surge, Enrage, Blazing Combo): the skill whose cooldown the crit ended goes next. These need
  agent 28 or newer, the version that tells the bot about critical hits.

Untick "Use the combos of the activated talents" (Character, Settings, Fighting) to fight without
them.

### Empty keys

When a run starts, the skills above and the items the bot uses (the chosen potions, the toolbox,
the hearthstone) that are on no key are put on EMPTY keys: a skill key with nothing on it, a hotkey
1 to = with nothing on it, the game's way (Ctrl+Alt+key in the skills panel, Ctrl+number in the
backpack). A key with anything on it is never changed, not even a hotkey kept for a potion you ran
out of.

The same happens during a run: when the red or blue potions on a hotkey are used up (or the game
puts something else on that key) and the backpack still holds red or blue potions of any size, the
bot says so and puts them on an empty hotkey between fights. With no empty hotkey, items are used
from the backpack between fights. With no empty skill key, the bot can't cast the skill at all (the
game only casts skills from skill keys), so it says which ones it is missing and which of your keys
repeat a skill that is also on another key, for you to decide. Turn it off on the Fighting page.

### Repairs

At the game's first warning that gear is about to break, the bot repairs everything you wear with
one toolbox (Small up to level 60, Large up to 80, Alloy any level; the cheapest that covers your
level), never pliers. If your level isn't known yet it reads the character sheet first, and if it
still can't tell it uses the Alloy Toolbox. A toolbox that can't do the job - the game turns it
down, its level limit is under yours, or something is still broken after it - is followed at once
by the next, stronger one you carry. A toolbox on a hotkey (1 to =) is pressed at once, even in a fight; one only
in the bag is used as soon as the fight is over. Without a toolbox it says so; if something has
broken and can't be repaired, it goes somewhere safe and stops. Both are on the Fighting page of
Character, Settings.

Only a warning that comes while the bot is running counts. The game keeps an item's last warning
for as long as it is open, so a warning from an earlier run (already repaired then) is left out:
Tools such as Sell shards, Update shard prices or Clean the bag now no longer spend a toolbox on
gear that is fine. Gear the game shows as broken is still repaired at once, whenever it broke.

### Fusion beasts and your pet in fights

A fusion beast goes on only after 6 seconds without an attack on you or your pet; every hit, or
any fall in your HP, starts the 6 seconds again. Getting off a Swift beast for a fight is never held
back, since its skills are off. When the game doesn't take a beast, the bot carries on and tries
it again later: after a minute, then two, four and so on up to ten minutes while it keeps refusing
(the walking assistant: from 15 seconds up to a minute). The log says so once, and again when the
beast is finally taken.

Your pet's HP is watched too. If it falls fast (2% of its HP within 3 seconds) the monsters right
next to it are treated as its attackers and fought first, even when the game didn't report who hit
it. A monster that is attacking you, or one nearly dead, is finished first. It stops once the pet's
HP hasn't fallen for 6 seconds. With the pet out of sight or no HP reading, nothing is assumed.

## Tools

### Keyboard Manager

Right-click a logged-in character and choose **Tools → Keyboard Manager**. Select **Capture current keys** to load the game's two combat skill pages, profession skills, number-row item slots, and quick phrases. Enter a name and choose **Save profile**. Use **New profile** to start with an empty draft, or enter a different name to save a copy.

Use **Edit binding** on each tab to change a slot. **Toggle preparation** on a bound self-buff or shield to cast it on yourself when the profile is applied. A slot marked **Leave unchanged** keeps its current game binding. An item needs to be in the bag when the profile assigns it to a new slot.

Choose **Apply profile** while out of combat and with game menus closed. For automation, add **Apply keyboard profile** under **Character settings → Triggers → Before farming** or **After farming**. The Before farming list can be skipped if you start on the farming map. Use that tab's checkbox to control when it runs. Schedules can run either trigger sequence or a saved script with a `keyboard_profile` command. Place that command at the point where your script needs a different layout.

### Sound Silencer

Tools, Sound Silencer (in the game's menu) mutes game sounds by their number. Type a sound's number
(1 to 99999) and press Add; in the Sounds list, the item's menu (Applications key or Shift+F10)
has Move to Mute List, Move to Sounds List, Rename and Remove. A name is optional. Nothing changes
until you press Save, which stores both lists in settings.json and mutes the Mute List's sounds in
the game at once; closing without saving drops the changes. The saved list is applied again each
time Uncle Farmer starts or a game connects. A sound that was already playing may finish before it
goes quiet. Scripts can wait for and mute sounds too (`sound_wait`, `sound_mute`, `sound_watch`;
see the script guide).

Both tools can use your own gang's craftsmen (gangs pay less), another gang's (type its name), or
the nearest city's; a gang's craftsmen stand in its base's Outer hall. They never spend below your
arnebia reserve, and have a **Check only** button that walks there, reads the real prices and
chances, says what it would do, and spends nothing.

### Gem Maker

Tools, Gem Maker (Ctrl+G) has three jobs:

- **Make a gem:** you choose which gem, its level and how many (or as many as it can). It makes them
  from the bag's gems and shards, and fetches more Level 1 shards itself from the storehouse or the
  Shard Broker, a bagful at a time: as many as the bag takes up to your "bag full at" load. The
  Shard Broker sells at most 2000 at a time, so it buys in batches of up to 2000, working out each
  batch again from the bag's room and the spare arnebia; the storehouse hands out a bagful at once.
- **Make the most of my bag:** every shard into gems, then every colour up as far as it goes.
- **Stock shards:** buys Level 1 shards of the chosen gem from the Shard Broker and puts them in the
  storehouse, so a later Make a gem takes them from there instead of shopping. Set "Number of
  shards to stock"; the price limit works as in Make a gem. It buys a bagful at a time (at most
  2000 per purchase), stores it, and repeats. Level 1 shards of that gem already in the bag are
  stored first and count toward the number. It keeps no arnebia back for craftsman fees, since
  nothing is made. It stops at the number, at your arnebia reserve, at a price over your limit,
  when the broker has no more, or when the storehouse is full. Check only reads the price and buys
  nothing.

Make a gem and Make the most of my bag go goes on until it is done or something stands in the way, and says what: the arnebia at
your reserve, no protection rune left, nothing left to make from, no more shards to be had, or the
Gem Craftsman making nothing for three rounds in a row although there is still something to combine
(a round that made nothing because of a slow answer or a menu that didn't open is tried again).

"Make a gem" can make this many more, as many as it can, or until the bag holds this many (the
gems already there count, so starting again after an interruption doesn't make too many). From
level 2 the shards a failed combine leaves are kept for the +20% on the next combines, and become
gems only at the level asked for. Nothing is spent until the craftsman's page names the gem being
made; if the game makes nothing of a batch, the Gem Maker asks for half as many before giving up.

"Put finished gems in the storehouse" (off by default) keeps the bag from filling with finished
gems: gems of the level asked for go to the storehouse just before more shards are fetched and when
the job ends, however it ends. Gems of that level already in the bag go too, and stored gems still
count toward your number. If the storehouse is full they stay in the bag, storing is switched off
for the rest of that job, and the job goes on.

### Gem Breaker

Open **Tools, Gem Breaker** or press **Ctrl+Shift+B**. It uses the Gem Craftsman's **break into shards**. Breaking can't be undone, so nothing is ticked at first, the window shows what would go, and **Start** asks once more.

A gem breaks into 3 gems of the level below, for free, and a Level 1 gem into 3 Level 1 shards. So a Level 2 gem ends up as 9 shards and a Level 3 gem as 27. That is less than it took to make them.

- **Gems to break**: the colours that may be broken.
- **Highest gem level to break**: gems above it are left alone. It starts at 2, so the gems you put in your equipment are safe until you raise it. Gems at or below it are broken all the way down.
- **Break down to**: shards, or gems of a level you choose.
- **Keep at least**: how many gems of each colour and level stay.
- **Enhance Crystals**: Weapon and Equipment crystals have their own boxes, their own highest level and their own number to keep, off at first. They turn straight into shards and cost arnebia, as their page says; the arnebia you keep is never spent.
- **Sell shards by the bag manager's rules**: off at first. Does what **Sell shards now** does: gem and crystal shards marked to sell go to the Shard Market, and what you keep or store stays.

What a break leaves can weigh more than what it took: when the game says "overweight", the Gem Breaker asks for fewer. If not even one fits, it sells when that box is ticked and carries on; otherwise, or when nothing sells, it stops with a message.

### Potion Maker

Open **Tools, Potion Maker** or press **Ctrl+Shift+O**. It uses the Pharmacist in a gang base's outer hall: **Make Medicine** turns Bloods and Pelts into a batch of 50 (or 45) potions for a fee in arnebia (lower in your own gang), and **Fuse Medicine** turns 5 potions of a size into 1 of the next for free (Small to Medium to Large, red and blue, for you and for pets), up to 100 at a time.

- **Potions** and **Pet potions**: how many of each to have in the bag. 0 means it isn't made. The window shows how many you have now.
- **Make them** (Medium and Large potions): from Small ones, fused up, or each from its own recipe. Fusing is usually cheaper: 25 Small Red Potions (one Lesser Blood and half a fee) make 1 Large one.
- **Fuse spare potions up to**: after making, fuse what is over your numbers up to Medium or Large, keeping at least the Small and Medium ones you say.
- **Pharmacist**: your own gang's, or another gang's by its name. Arnebia below your reserve is never spent, and each fee is read on the Pharmacist's page before anything is paid.
- **Take them from**: missing Bloods and Pelts come from only the bag, the town storehouse, the market, or the storehouse and then the market.
- **Most gold coins a piece**: for each material, the most the market may charge. The cheapest lots are always bought first; with 0 any price is fine, still cheapest first. **Most gold coins to spend on materials in one run** caps the whole buy.

- **Put the potions made into the town storehouse**: then it works a bagful at a time: it fills the bag with Bloods and Pelts up to its full mark (Character settings, the bag's full mark), makes and fuses, puts the potions in the storehouse and goes again until your numbers are there. Your numbers then count what the storehouse holds too, and the potions you had in the bag before stay in the bag. Making and fusing still work when the bag is over its full mark: only the materials brought in are held to it.

**Check only** walks to the Pharmacist, reads the real fees and says what it would make, fuse and buy, without spending anything.

### Equipment Enhancer

Tools, Equipment Enhancer (Ctrl+Shift+E) enhances your equipment up to the level you choose (+12 at
most), with protection runes. It makes its Enhance Crystals from crystal shards out of the
storehouse or bought at the Shard Broker: a stock of crystals before it starts, and a set number
more when they run out.

### Hunting bounties

Open **Tools, Hunting bounties** after your character has landed the killing blow on a boss. Each officer pays for bosses of his own, so tick the officers you want: Guard Captain Suke, Chancellor Bren, General Paul, or Colonel Demar. The bot visits them from nearest to farthest and tells you what each one answered. **Check only** walks there and reads the menus without collecting.

This is not a daily chore, so you can run it whenever you have something to collect. In a script, use `bounties` or `bounties check`.

### Construction scanner

**Tools, Construction scanner** shows how far your gang's constructions are: the Magic Cannon and Supply Camp being built, and the Crystal Turret and Wall barricade of every highland. **Scan the constructions** visits each one without repairing or building anything. Open the window again afterwards to read the result, the least complete first.

**Copy** puts the short report on the clipboard. A gang elder can also **Publish** it as a gang announcement, a broadcast (which plays a sound) or a system message. The bot always asks first. A new announcement replaces only the older reports published by the same character, never another elder's.

Tick **Put each highland on its own line** to publish a gang announcement as a list: the title first, then a line for each camp and each highland, with a highland's turret and wall together ("highland 80: turret 95.0%, wall 98.0%"). The setting is kept for all your characters and also applies to a scheduled announcement. A script can choose for one line with `lines=yes` or `lines=no` after `publish=announcement` or `auto=announcement`. A broadcast and a system message turn a line break into a space, so they are always one line. The game's agent must be up to date; if it is too old, the announcement goes out as one line and the log says so.

To do this automatically, open **Run, Schedules**, go to the **Tools** tab and add one of the three "scanning the constructions" tasks for your elder. At the set time the bot scans and publishes without asking. It publishes nothing when everything is at 100%, or when the report is the same as the last one this character sent that way.

In a script, use `construction_scan`, `construction_scan publish=broadcast` to send the last report, or `construction_scan auto=broadcast` to scan and send it if there is something new. The kinds are `announcement`, `broadcast` and `system`.

### Daily chores

Tools, Daily chores (Ctrl+Shift+D) does what a character can do once a game day (the game's day
starts at 00:00 GMT). Each chore is done once a day: the bot writes down what it did, so starting
it again doesn't donate twice.

- **Bank:** the deposit income and every Value Product card's daily income.
- **Pet rebirth:** the day's free rebirths of the pet you choose (the name from the character
  scan works, though the Pet Trainer may call the kind a little differently: "Eagle" there is
  "Wild Eagle"). Rebirths that cost diamonds are never used.
- **Gang:** the once-a-day donation you choose (10,000 or 20,000 arnebia, or 20 diamonds, never
  below your arnebia reserve) and the day's construction: the game allows two builds a day,
  builds and repairs together ("you've already built twice today"). Building costs nothing: each
  one pays gang contribution, gang points and, from a colonel's rank up, arnebia (3,000/3,000/6,000
  for a general). Tick the places it may use; it goes through them in this order and stops
  once the day's builds are made: your gang's highlands under 100% (every one listed under Occupied
  Highlands: a damaged Crystal Turret or Wall barricade is repaired, back by the Teleportation
  circle), the Magic Cannon or Supply Camp being built, the East and West posts that are open, then
  highlands at 100% (the game rewards those repairs too). On the day a character joins a gang the
  game allows neither donating nor building.
- **Animal Shed:** feeds the gang's breed beast once a day (500 gang contribution, 500 gang
  points and 2,000 arnebia), apart from the two builds.
- **Secret room, sharing arnebia:** sharing works once in each half hour of the clock (from :00
  and from :30), 5 times a day, and both players get arnebia. So the bot doesn't stay: it goes in
  a little before the half hour (10:28, say), shares, shares again once 10:30 comes, and leaves.
  While farming it does that by itself: it leaves the farm a few minutes before a half hour whose
  share isn't made yet (10 minutes by default, the walk there included) and comes back, about once
  an hour, until the 5 are made. It shares with the players you name first, or anyone in the room.
  Practising there (an assistant kills for you) is a separate setting, 0 minutes by default: time
  inside comes out of the day's public-area drop time.
- **Contribution Chests:** at Guard Captain Suke on Tuneful Wetland, top-level contribution (not
  gang contribution) for Contribution Chests, 5,000 each, two a day. Off until you tick it on the
  City tab; a chest counts once it is in the bag.

Check only walks to each NPC and reads the menus without collecting, spending or entering. Tick
"at the start of the first farming run" and the first farming run of each game day does the chores
first. In a script: `chores`, `chores check`, or `chores only=bank,donation`.

### Gathering

Tools, Gathering (Ctrl+Shift+F) fishes, mines or collects herbs: whichever of the three the
character has learned (a character learns one, at the gang's Guru Elder or Master Pepper). The
window says which skill the last scan found and its rank, from Newbie to Grand Master.

- **Gangs' areas first:** a gang's Lake, Mining Area or Herbal Garden gives more than the open
  world, the higher its level and saturation. On the Gangs tab, list the gangs to gather in, in
  order: your own gang ("Add our own gang") and any other gang by its name ("Add a gang by name",
  as the Gang Entrance's list shows it), for players who gather in a friend's or an allied gang.
  The bot goes to each in turn: into the gang's base (another gang is found through the Gang
  Entrance's "all gangs" list), talks to the entrance for your skill, reads its level, saturation
  and fee, and goes in, for a fee up to the limit you set and never below your arnebia reserve.
  Each gang's area once a game day. After half an hour the game puts you back outside and the bot
  goes on to the next gang. It sells what you carry before each one, since that half hour can't
  be left and taken up again.
- **Then outside:** at one of your own places, or one where the game has been seen letting players
  gather. To add a place, stand where you fish, mine or collect herbs by hand and press "Add where
  I stand": the bot stands on that very spot. With "The best for this character" it takes the
  highest-level area whose monsters are at most a few levels above you (5 by default). A place
  where the game never starts gathering is remembered and left alone until the skill's rank rises.
- **Starting and while gathering:** the bot does what you do: Right Ctrl on the skill in the bag's
  Profession skills panel, "Start", then "Confirm". From then on the game gathers by itself every
  two seconds until it is stopped or another skill or item is used. In a gang's area the bot
  leaves it to the game for the half hour. Outside, monsters come, so it looks after you the whole
  time: potions and heals as in any fight, fighting whatever attacks you, then back onto the spot
  and starting again.
- **The bag's load first:** before it sets out to a gang's area or a place, the bot looks at the
  bag's load. With less than 1,000 left (900 to 1,000 is safe; Selling tab) it says the bag is
  full, sells first if you let it, and only goes when there is room. No gang's area is entered
  without that room, since its half hour can't be left to sell.
- **Selling:** when the bag is full outside it walks to the nearest Aquaculture, Ore or Herb Buyer,
  sells, and comes back (or stops, if you choose). Everything the buyer lists is sold, except what
  you keep in Bag and supplies (an item set to Keep, or the number you keep of it). It sells once
  more at the end.
- **Selling before going out:** with "Always Sell Gathering Before Going Outside" ticked
  (Selling tab), the bot sells the gang collection and checks the bag before it travels to an
  outside spot, even with ordinary selling off. If a sale leaves items behind it tries again while
  it can sell more; if the sale can't be finished, outside gathering stops.
- **When it stops:** when Vitality runs out for the day (more costs diamonds, which the bot never
  spends), or after the minutes you set. Outside you can also keep some Vitality for later: "stop
  when Vitality is down to" (When to stop tab) reads the Vitality on the character sheet while it
  gathers, and doesn't set out at all when it is already that low.

Check only reads the gang area's entrance and says where it would gather. Sell the collection now, in the game's
menu in the Games list, sells to all three buyers from wherever you are. In a script: `gather`,
`gather check`, `sell_collection` or `sell_collection fish`.

### Shard prices

Shard Market prices change. Update shard prices, in the game's menu in the Games list, walks to the nearest Shard Broker, reads
its list and keeps the prices in `data\shards.json`, the price list the bag manager and the
results use. A price is kept only when the price the list shows and the price its row sends to the
game are the same, sane number; any other row, and any shard the list doesn't show, keeps its old
price, and the log says which. Nothing else in the file changes. In a script:
`update_shard_prices`. An update of Uncle Farmer brings its own price list, so run it again after
updating.

### Shops and the Shard Market by index

With agent 53, the Shard Broker's list, its buy and sell menu, and a potion seller's list are
chosen in by their rows instead of walking down the list a key at a time. The agent knows these
menus as the game showed them in every city they were seen in. It first checks that the whole menu
is that one, that the row holds the item's own number in the game, and that buy is buy and sell is
sell; if anything differs it chooses nothing and says why. The bot then goes by the menu's text as
before, except in a buy or sell menu that came up for the wrong shard: there it chooses nothing at
all. Other shops (the grocer's) are always chosen in by text.

Once the bot has found an item there, it picks that item by its number after that, without reading
the list again; the agent still checks the whole menu first.

### Every other menu

With agent 55, an NPC's menu entry is chosen where it is, in one step: the bot finds the entry by
its text in one reading of the menu, and the agent chooses it as Enter would, once it has checked
the menu is still the one read. There is no walk down the list, and the game doesn't speak each
entry on the way. When that can't be done (an older agent, or the menu changed), the bot walks to
the entry with the keys the shorter way round: the game's menus wrap, so an entry near the bottom is
reached by going up past the top.

### Dungeons

Tools, Dungeons (Ctrl+Shift+G) runs the experience cave a character can enter once a game day:
Spider cave (level 40, entered at water curtained cave), Scorpion Cave (level 60, thousand miles of
rivers), the Bottomless pit (level 80, Valley of Luxuriant forests; not tested yet) or the White
Bone Cave (level 90, ancient Sealed Land, reached by cable car). The game lets each character into
one of them a day, not one of each. The visit gives 15 minutes inside; the aim is as many kills as
those minutes give. A dungeon run started while the character is already inside one of the caves
hunts on until the game moves it out. When the day's visit is already used, the bot says so.

- **Caves tab:** choose the cave, or "The highest cave my level lets in" (the default). Below it
  the window says whether this character has had its cave today. A cave above your level isn't
  tried; the bot says so.
- **Supplies tab:** what to have before setting out: the pet's blue potions (25 by default), Pet
  Rice Rolls (3), your own blue potions (50) and red potions (30). Each row uses the potion on your
  hotkey (else the strongest in the bag) unless you choose one; 0 means don't look. What is short
  is taken from the storehouse, then bought, before the bot sets out.
  If something is still short it doesn't go (or goes anyway, if you choose). The pet's rows count
  only with a pet ticked in Character, Settings.
- **Inside:** the bot rides to the entrance, chooses "Enter the dungeon", and from the cave's
  safe landing it never stops: it takes the nearest monster it can walk to within 90 steps, and
  only walks its loop round the cave when there is none. A character that fights from afar shoots
  whatever comes into reach on the way, without stopping, and walks on to the next one the moment
  the game reports a kill. It uses area skills as soon as two monsters would be hit (you can raise
  that). For every class it counts what each area skill would really hit, by the skill's own
  shape: an arc in front (Multi Shot, Ice Storm, Fire Surge, Holy Light Wave...), straight ahead
  (Sweep Attack, Flesh Cleave), a ring round you (Whirlwind Slash, Frost Nova, Divine Nova) or an
  area where it lands (Blizzard, Skeleton Explosion). Shots on the way use instant skills only,
  since walking on breaks a channel. Monsters come back about 30 seconds after
  they die, at random anywhere in the cave. In simulated visits on the caves' real walls, which
  loop it walks hardly mattered, but chasing 90 steps instead of farming's 40 gave a caster 5
  to 13% more kills. It drinks instead of resting, keeps the pet out, its HP and MP up, and its
  amiability up with Rice Rolls. With no pet ticked in Character, Settings, it looks after the
  pet that is out for the visit. Nothing sends it out early: no restocking trip, no full-bag
  trip, no secret room visit, since a visit can't be taken up again.
- **Kills:** the bot counts your pet's kills as yours, as the game does in the report it shows
  when you come out ("Monsters Killed").
- **The end:** after 15 minutes the game moves you out by itself (if it ever doesn't, the bot
  leaves through the Action menu). Then it goes to the place on the Where to end tab: back where you started it (the default), a place you choose, home with the hearthstone,
  or where it is.

Check only says what is short and which cave it would go to. In a script: `dungeon` or
`dungeon check` (put `end_at` first to choose where it ends).

### Market searcher and buyer

Tools, Market searcher and buyer (Ctrl+Shift+K) is a window for the player market, the Ansible
Space-time Marketplace, with two tabs (Ctrl+Tab): Search and Results. After a search the character
stays at the marketplace, so the next one starts at once.

The Search tab lists what is for sale by category (My list, All items, or one of the game's 14):
how many lots, how many in all, the cheapest and the usual price, and how many sellers. "Refresh
the market list" walks to the nearest marketplace and reads every category (a minute or two);
"Also count sellers" looks at every lot's details too (about ten minutes the first time, then only
new lots). Each server has its own list.

Enter on an item finds all its lots. "Search for" can also be cheapest first (with "Most a unit",
it stops at the first page that costs more), by seller ID (it stops once all 10 lots a seller can
have are found), or a whole category; "Pages at most" limits how far it reads. Lots appear in
Results while the bot reads, each in its place by price; Stop keeps what was found.

To buy, tick lots in Results with Space, set how many of each, and press "Buy the ticked lots":
one question names the lots and the gold coins in all, and nothing is bought before you say Yes.
Lots in their first hour on display are never bought, "Spending limit" stops the buying before
more would be spent, and "Check only" says what it would buy. "Save as CSV" writes the results to
a file. In a script: `market` (see the script guide).

## Walking

Run, Walk to a dungeon or map (Ctrl+W):

- **Dungeon entrance:** the dungeons whose entrance NPC the bot knows (a teleport circle or the NPC
  at the cave mouth). It walks up to the NPC and, if you like, opens its menu so you choose.
- **Map:** any map of the open world (the ones you can walk to and back from; closed maps and the
  maps inside dungeons aren't listed), or a cell on it.

Show the route says the way before you go. The whole way it rides your fastest Swift fusion beast,
in towns and through monster ground alike, and it doesn't stop to fight; potions still keep your HP
up. Pause stops it.

A Mage or an Elf also casts its teleport skill when that is the shorter way (an Elf's Elven
Teleportation to West Sealing Tower lands near White Bone Cave, for example): it gets off the beast,
casts, and gets back on. Short of MP, it drinks a blue potion first. A monster attacking right then
is fought first, since a hit breaks the cast. To walk instead, untick "Use the class's teleport
skill (Mage, Elf)" on the Travel page of Advanced settings.

### Polson Wetland and its poison

Polson Wetland's poisoned ground hurts anyone on it, unless they have activated the General talent
Poison Immunity or are on a fusion beast (any kind). Without the talent:

- A trip through it (the only way to the Underground Water Cave and the sailing port beyond) gets on
  a fusion beast before stepping in and stays on it all the way across, without stopping to fight.
  Your fastest Swift beast goes on first, else your strongest Fierce one, whatever your travel beast
  setting says. If no beast will go on, it waits out a fight that just ended; if there's still none,
  the run stops before the step in, and the log says why.
- A trip that ends there (farming, gathering) goes, and says once that Poison Immunity isn't
  activated: every fight there is on foot, in the poison.
- Leaving Polson Wetland is never refused.

### Lava

The volcanic caves' lava lake and magma can be walked on, but a character standing in them loses
HP. The bot treats them as walls: it walks, stands and fights only on the islands and bridges. A
monster out in the lava is fought from the shore when it is within your attack's reach, and left
alone when it isn't. On the two maps where lava is the only way between parts of the map (Deep
underground and Demon Castle), it stays walkable.

## Several games at once

Only one Uncle Farmer runs per Windows session: starting it again brings the open window forward
instead of opening a second one. While it runs, it keeps your settings, plans, profiles, scripts,
message files and results open, so Windows refuses to delete or move them; close Uncle Farmer first
if you want to clean those files by hand.

Game, Open another game window (Ctrl+O), or just start Mist World again. The agent lets every copy
run, however many you open (each needs about 1 GB of memory). Each game window is named after its
character, such as "Mist World - YourName".

Choose a game in the Games list, choose its plan and press Start, then do the same for the next
game. Inside a game window, Pause starts and stops that game's bot. Run, Stop every bot
(Ctrl+Shift+S) stops them all.

## Schedules

Run, Schedules (Ctrl+Shift+H) starts a plan or script for a character at a set time: once (a date
and a time), every day, or on the days of the week you tick. The list shows each schedule, when it
runs next and whether it is on. Add is a button; Edit, Turn on or off, Delete and History are in
the selected schedule's menu (Applications key, Shift+F10, or right-click). Enter edits a schedule
and Delete deletes it. Changes are saved straight away, in `schedules.json` beside the settings (an update never
replaces it).

Besides plans and scripts, a schedule can run one Tools job, or a character's whole Before farming
or After farming list, on its own (the Tools and Triggers tabs of the schedule editor).

- A scheduled plan starts as the Start button would, in the game that character is logged in to:
  the same log, results, farming day and end place.
- Each time runs once. A time that came round while Uncle Farmer was closed, or while the schedule
  was off, is not made up for later: History says "missed".
- One run per game. If the character's game is busy with another run (yours, or another
  schedule's) or isn't open, the schedule waits up to 15 minutes and then gives that time up
  ("skipped", with why). A run already going is never stopped for a schedule.
- History keeps when each time was due, when it started and how it ended: finished, stopped, or
  an error, with the reason and the run's results line.

## Results

Run, Results (Ctrl+R) shows what each character earned farming: time and kills, contribution,
experience and levels, arnebia, every shard picked up (with its Shard Broker value, and how many of
it were thrown away, sold or put into the storehouse), other items picked up, what was bought or
taken out of the storehouse, and the potions used. It covers the current run (or the last one),
today, yesterday, a day you pick from the Day list (each date with its weekday and how many days
ago it was), the last 7 or 30 days, or all time.

**Skills used** lists every skill the character cast: how many times, its damage and share of all
your skills' damage, its critical hits and misses, and what it healed, the most damage first. For
classes that heal (Priests and Sorcerers, for example), **Healing** says how much your own healing
skills healed you, your pet and anyone else; potions aren't counted there. Skills and healing are
counted from version 1.0.5 on, and older runs say they weren't counted.

For a run it shows **Time used** (farming time, hours:minutes; a pause or a job on the way is not
counted) and **Time remaining** until the run ends by itself: the plan's time limit, its stop time
or the daily stop, whichever comes first. These are clock times, so a pause doesn't move them (a
plan's time limit counts from the start, pauses included). With none of them set it says so. A
finished run shows its time used and 00:00 remaining. Both update while the window is open.

It also shows the money: **Earnings so far** (arnebia picked up or got from selling, including the
run's own Sell shards and Clean bag jobs), **Total expenses** (the items used up, at their stored
prices, as listed further down) and **Net earnings** (the one less the other). A purchase is neither
an earning nor an expense: a potion bought counts as an expense once it is drunk, and what was paid
at shops and for fares is shown on its own line. Runs saved by older versions kept only the bag's
net arnebia change, and their earnings are counted from that.

Only farming counts there. Show can switch to the Gem Maker, Equipment Enhancer and chores instead:
what each of them made, used and cost, kept apart because shards made into gems are not loot. Those
jobs are kept apart inside a farming run too (chores before farming, `gem_maker` in a script).
While a run is paused nothing is counted: what you kill or pick up by hand is yours, not the bot's.

Arnebia spent on items used up: for each item used up (potions drunk, shards made into gems) its
unit price, how many were used and what they cost, then the total. Shop items are at the shop's
fixed price from the game data; shards are at the Shard Market price last read, which changes, so
those are marked as estimates. What was bought is not counted as used. An item with no stored price
is named and not counted. Each run keeps the prices it was costed at, so later price changes don't
rewrite old results.

It also shows the fight itself, from the game's own hit reports: damage given and received, hits
and misses, critical hits and defence breaks (with the best and the last of each), the best normal
hit, the last monster killed, and the monsters that hurt you most. Anything the game did not report
is shown as `null`. These numbers need agent 28 or newer, like the crit-timed combos.

When a run farmed two maps or more, its results add a Map by map part: for each map the time
farmed there, kills and kills an hour, the arnebia and shards gained, the chests opened and the
deaths. A day's or week's results add the maps up the same way.

Shift+Pause speaks a one-line summary of the game in front, from anywhere, and Ctrl+Shift+R in
Uncle Farmer speaks it for the game selected in the Games list. When a run ends one short line is
spoken; Settings can add a line every few minutes, or turn it off. The summary starts with how long
the character has farmed and how much of today's drop time is left, then kills, contribution,
experience and any level ups, for example "farmed 2 h 15 min, drop time left 3 h 20 min, 340
kills, 4,183 contribution, 12,000 experience". The drop time is left out until the game has shown
the character sheet. Damage and loot are in the Results window. The records are in the
results folder, one file per character.

## The game's own voice

While a bot runs, the game's speech is muted so you can use the computer (sounds still play): every
line, the combat announcer's damage numbers too, whichever voice the game uses (screen reader, SAPI
or its own voices). Settings chooses: while a bot runs, always, or never.

By hand, Ctrl+M mutes the game selected in the Games list and Ctrl+U lets it talk again, each game
on its own (the Game menu also has Mute every game and Unmute every game). A run that ends keeps a
game muted if you muted it.

## Quick phrases and teammates

Quick phrases (Shift+1 to Shift+=, set up with Shift+Backspace): each character has its own. A
phrase starting with a code does something instead of chatting (see the game's help, "Quick Phrase
Controls"):

| Code | What it does |
| --- | --- |
| /6 | targets the next teammate on this map |
| /5 | targets what is attacking you |
| /4 | targets what is attacking your target |
| /3 | targets what your target attacks |
| /7, /8 | target the weakest teammate within 20 or 30 yards |
| /0, /1, /2 | set or cancel the team's navigation target |

At the start of a run the log lists what each of the character's phrases does (never the chat lines
themselves), and Character, Scan shows them. Codes the character has on no phrase (/6, /5, /4, and
/7 for a Priest, Sorceress or Witcher) go on EMPTY phrase slots only; a phrase with anything in it
is never changed (profile setting fill_empty_phrases). This needs the game restarted once so it
loads the new agent.

Finding and reaching teammates: the bot presses the /6 phrase to learn where a teammate it can't
see is on the map (the game answers with their position), and Shift+P teleports it to the team
leader: only on the same map, from further than 20 yards, once per about 50 seconds. `come` and
`follow` use both when the player they go to leads the team.

**Leading a team.** Character settings has a Team tab; nothing on it does anything until ticked,
and each character keeps its own choices. "Accept requests to join my team" lets in only the
players you allow (your trusted players, your friends in the game, or names and ids you type);
anyone else is left waiting and named once in the log. "Remove members who go offline" checks each
member with the game's info key (G) every few minutes, or only in towns, and asks twice before
removing one. The run can also hand the team over to the first player of your list when it ends,
create your team (with its name) when it starts, leave a team another player leads, or stay in
town managing the team after the run; a script does that with `manage_team`. If another player
disbands the team or becomes its leader, the bot stops managing it and says so.

## Chat

Messages, Chat (Ctrl+T) reads and writes the game's chat while the bot farms, without the game's keys:
what you send goes through the game itself, as if typed there, so the bot's keys and your chat
never get in each other's way. Two tabs, as in the game (Ctrl+Tab moves between them):

**Channels**
- **Channel:** All, Team, Gang, Nearby, Map, Global, International, Private channel (the channel
  you joined in the game) and Notices (loot and events). Ctrl+1 to Ctrl+9 jump straight to one. A
  channel with new messages says how many.
- **Messages:** that channel's messages, newest last.
- **Message:** Enter sends it to the channel; the label says where it goes. In All it goes to the
  channel of the selected message, so you can answer whatever you are reading.

The game lets you be in several international rooms and several private channels at once. Each
gets its own line in the channel list, in place of International and Private channel, such as
"International: French" or "Private channel: room 136"; no line mixes the rooms. A room shows up once
the game has shown it, and by its name once you have switched to it in the game (until then by its
number). A message typed in a room's line goes into that room, whichever room the game has up, and
a reply goes back into the room of the message you answer. A room you switch away from stays
joined. Needs the agent that comes with this version: restart the game once after updating.

**Private chats** (private messages, one player to another)
- **People:** only the people you have talked with, the latest first, with how many new messages.
- **Messages:** your conversation with the person picked, both sides ("you: ..." for yours, also
  the ones you typed in the game itself).
- **Message:** Enter sends it to that person.
- **New chat with:** type a name or the player's id and press Enter, or pick one from its list (Alt+Down
  Arrow): the people you have talked with and the players in sight. A name works for anyone in sight
  or anyone you have messaged with this session; an id works for anyone.

**Voice messages.** Both tabs have the same two buttons beside Send. A voice message shows as "voice
message" in Messages; Play (Alt+Y), or Enter on it, plays it. Record voice (Alt+V) records from the
microphone the game uses; press it again (it now reads "Stop and send voice") to send what you said,
or press Escape to throw it away. The game takes voice messages only on Team and Gang and in private
chats, so on other channels the button says so.

It sounds better than the game's own recording: the low hum and the silence before and after are
taken out, a quiet or loud microphone comes out at an even level, and it is sent at twice the game's
quality, in the game's own sound format - so other players hear it in their normal game. The game
takes at most 20 seconds in one voice message, so a longer recording goes as several, of about the
same length (45 seconds: three of 15), one after the other, the way a long text goes in parts. A
recording stops by itself after 5 minutes. Voice needs agent 42: restart the game once after
updating.

The game's own auto-play has a fault: with two games open, one of them now and then starts playing
every voice message slow and deep, until it is closed. The agent mends that (agent 51). If you would
rather keep the deep voices, untick "Fix the speed of voice messages the game plays by itself" in
File, Settings, Speech and language: every open game plays as the game does at once, and ticking it
again mends them, no restart needed.

**Settings**
- **Read new messages:** only while the Chat window is open (to start with), always, or never; and
  which channels (Team, Gang and Nearby to start with).
- **Tones:** a private message to you plays a tone - one for your trusted players (the names and
  ids in Private messages), another for everyone else, so you know who it is before you look. Pick
  "No tone" for either. Private messages are read out as set in Private messages.
- **Times:** show the time after each message or not, with a 24-hour or 12-hour clock.

**Sending, and the game's limits.** The game takes one line every 2 seconds (3 on Global) - for
every channel and private message together - and drops a line sent sooner. So everything Uncle
Farmer sends (the Chat window, the auto replies, answers to trusted players) waits its turn as the
game allows, also after lines you type in the game itself, and a line the game dropped anyway is
sent again. A message longer than the game's 200 characters goes in parts, cut at a space, one after
the other.

Nothing is read out and no tone plays while that game's own window is in front.

**Replying.** In either chat tab, a message's menu (Applications key or Shift+F10) has Reply: the
text box gets the sender's `@name` in front, and the reply goes to that channel or conversation
even if you move to another one. Escape or Cancel reply leaves reply mode and keeps what you typed.

**Chat filters.** A message's menu also has "Add to filter list", which hides every message with
exactly that text, in every game's Chat window. "Chat filters" in either tab lists the hidden
messages and the rules; a rule matches the exact message, text it contains, or a pattern with `*`
and `?`, with or without matching case, and "Test filter" tries one on a sample. Changes there
count when you press Save. Filters only hide lines in the Chat window: speech, tones, voice
messages and private-message replies go on as before, and nothing is deleted.

Chat is never saved: it is kept in memory while Uncle Farmer runs, and gone when you close it.

## Private messages

Messages, Private messages (Ctrl+Shift+M). While a bot runs, strangers who message the character get a
few lines from your reply list at once (never the same line twice), then one goodbye line and
silence for an hour. Edit the lines there; a few polite ones are there to start with. Write {name}
in a line to put the player's name there ("Hi {name}, I'm away"); with "Call them by their name"
ticked, a line without {name} starts with their name ("Kim, I'm busy right now").

Trusted players can be listed by name or by the game's id, mixed ("Kim, 2001"): either works for
commands, team invites and being read out. An entry followed by `@` and a server, such as
`Kim@S1` or `2001@S2`, is trusted on that server only; names and ids you add get the server of the
character selected in the Games list. An entry without a server is trusted on every server, so add
the server to the ones you listed before.

While the game's own window is in front, you are in the game and read your messages there: Uncle
Farmer doesn't read them out or play a tone (they still show in its log and Chat window), and sends
no away note. Trusted players' commands still work then unless you untick "Take their commands while
the game window is in front". A trusted player never gets the strangers' replies.

Trusted players can send a command as the whole message: help, status, where, players (who is
near, nearest first; also "who"), pet (its HP and MP), results, today, bag,
drop, pause, resume, stop, start [plan], home, come, follow, unfollow, buff, add (take their team
application), leader (make them team leader), leave (also "quit" or "quit team"), mute, unmute,
quit game (closes the game). wait [minutes] (log out for a while, then back in; off
unless ticked, see below). "help" answers with the list; "help" and a command's name ("help
follow") answers with what that command does. Their team invites are accepted; anyone else's are
declined with Escape while a bot runs.

One action at a time: while one is under way (a wait, a walk home, come), another action is answered
"Busy, one command at a time. Still on: ...". Questions (status, where, results and so on) and stop,
pause, resume and quit game are always answered.

### wait

"wait 45" logs the character out for 45 minutes, then logs the same character back in, and the run
goes on where it was (the minutes logged out don't count in its results). "wait" alone waits the
minutes set in Private messages. It works only with "They may log me out for a while and back in
(wait)" ticked there; otherwise it answers that the command is turned off on this character.

The bot logs out as you would (the setting menu, F1, then Switch account) and back in with the
game's saved account, so the character must have been logged in once with Uncle Farmer open. While
logged out no private message reaches it. The Games list says "Logged out for a while" with the
minutes left, and the Pause button (F6) reads "Log back in now": press it to end the wait early.
Stop during the wait leaves the character logged out. If logging back in fails five times, a minute
apart, the run stops.

### come

Walk up to them. If they are one of the characters running in this Uncle Farmer, it knows where
they are and travels there; otherwise it looks where any of your games last saw them (up to 10
minutes ago).

Best: press E in the game (your location), copy it with Shift+C and send "come" followed by what
you copied. The bot reads the map and the x, y from it and walks to that spot. "come" followed by a
map's name works too. A farming run stops there, beside them, and waits; while following them it
just comes closer and keeps following.

### follow

Stay with them: catch up when they move off, fight what attacks, help with the monsters near them
that they are fighting, and go along when they change map (anywhere for our own characters, through
the exit they took for anyone else). A run that was going stops first. After a minute without any
sign of them it stops and says so.

While following, it casts no buffs (heals, shields and dispels still go). Send "buff" to have it
keep its buffs up for the rest of this follow, and "buff off" to stop again. Each new "follow"
starts with buffs off.

### unfollow

Stop following.

## Control by an AI assistant (MCP)

An AI assistant that supports MCP (the Model Context Protocol), such as Claude, can run Uncle Farmer
for you: start and stop plans, pause, run the Tools jobs, read the log, the game's state and the
results, write plans and scripts, change settings, schedules and the private-message lists, read
and send chat (in one international room or private channel too), and log the character out for a
while in the middle of a run and back in, as the private message wait does. It acts as if you had
done it, through the same code as the window.

It is off until you turn it on. In File, Settings, **Control**:

- "Let other programs on this computer control Uncle Farmer (MCP)" turns it on. Only programs of
  your own Windows account can connect, and they must know a secret Uncle Farmer makes up each time
  it starts.
- "Also let them send raw commands to the game agent" lets the assistant press keys, type and send
  any of the agent's commands in the game. Leave it off unless you need it.
- "Copy setup instructions for an AI assistant" copies a text with this copy's path and the
  commands to add it; paste it into your assistant. For Claude Code it is
  `claude mcp add uncle-farmer -- "<path to UncleFarmer.exe>" --mcp`.

The assistant starts `UncleFarmer.exe --mcp`, which has no window: it passes each request to the
open Uncle Farmer, and starts Uncle Farmer if it isn't open. While the setting is off, every request
is refused with a message saying where to turn it on.

Requests that spend arnebia, sell or throw away items, send chat or private messages, log the character out for a while, delete a plan
or schedule, close games, reinstall the agent, install an update or close Uncle Farmer only work when
the assistant says it asked you first (confirm). The control switches themselves can only be
changed by you. Every request is written to the day's log as "control by another program".

## Updates

When it starts, and again every 6 hours while it is open, Uncle Farmer asks its GitHub releases
page whether there is a newer version, and offers it with what changed; Help, Check for updates
asks at any time. The check while it is open says nothing when there is no new version, and it
waits to offer one until no bot is running and no dialog of Uncle Farmer's is open. Say yes and it downloads the
release, checks it, and restarts as the new version. If games are open, it asks first: the update
replaces the agent they have loaded, so press **OK** and it closes every Mist World window, then
updates; start the games again afterwards. The request carries nothing about you or your
game. Settings, Updater, "Look for a new version when Uncle Farmer starts" turns both checks
off; then it never goes online.

Settings, **Updater** holds everything about updates: this copy's version and where its updates
come from, the check at start, the release channel, "Offer version ... again" when you said no to
a release, and **Save and check for updates now**, which saves the settings and does what Help,
Check for updates does.

### Release channel

Settings, Updater, **Release channel** says where updates come from:

- **Master: stable releases** (the default, and what every copy used before the setting existed):
  the releases made by hand, the same ones the README links to.
- **Dev: development builds**: a build of the `dev` branch, made by GitHub each time it changes.
  It has the newest changes before they are a release, and it can break. Its version says it is a
  development build: 0.9.0-dev.57 is the 57th build, made after 0.9.0.

The choice is saved with the other settings and kept after a restart. Each channel only ever
offers its own builds: Master never offers a development build, and Dev never offers a stable
release. Going back from Dev to Master keeps your development build until a stable release newer
than it is out (Help, Check for updates says so); to go back at once, put a stable release's
UncleFarmer.exe in place of yours by hand.

### What an update leaves behind

An update is one file, the new UncleFarmer.exe, with a signature. Uncle Farmer downloads it into
the `update` folder beside the app and checks that signature: a file that isn't signed by this
project is deleted and never run. Then Uncle Farmer closes, a small helper puts the new exe in
place of the old one, and starts it. If the old one can't be replaced, it is kept, and Uncle
Farmer says so when it starts. The old exe, kept as UncleFarmer.exe.old during the update, is
removed at the next start, and the `update` folder is emptied. Every step (the check, the
download, the signature, installing, cleaning) is written to `logs/update.log`.

You can also update by hand: close Uncle Farmer and the games, and put a newer UncleFarmer.exe
in place of yours. Either way your characters, plans, scripts, settings and logs stay as they are,
since a release never carries them.

## The game in another language

Uncle Farmer works with any of the game's language packs (language\lang.txt), not only English.
The game translates names and menus as they arrive; the bot reads the same language files the game
does and turns what it sees back into English, so it finds the same potions, skills, monsters,
pets and menus. The English it turns them into is the wording of the game's own **english** pack,
which renames some of the server's texts ("Shard Broker" for the server's "Shard Marketplace",
"Pet Bone Cookie" for "Bone Cookie"). Whatever a pack leaves untranslated is English already.
Players' names are never changed.

Pick the language in the game as usual; after changing it, restart the game.

## Contact

Help, Contact the developer shows the developer's email and Mastodon addresses, for questions
or ideas, with buttons to write an email or copy the address. Bugs are best
reported as a GitHub issue, so everyone can see the fix.

Help, Telegram updates channel opens the Telegram channel where every new version is announced
(https://t.me/+-SHI1xTKJugwMzQ5). The Contact the developer window has a button for it too.

Help, Donate has buttons to donate with PayPal (https://paypal.me/RefinnejLTD) or Ko-fi
(https://ko-fi.com/ernie96). Uncle Farmer stays free either way.

## Things to know

- If the bot says it can't find the game: other tools that clean the game's settings (such as
  mwMod) remove the agent line. Restart Uncle Farmer and press OK when it offers to reinstall the
  agent (or open File, Settings and press Install), then start the game again.
- Your character settings, plans, scripts and logs are stored in this folder (profiles, plans,
  scripts, logs). Copy them to keep a backup.
- Translations: copy `lang\unclefarmer.pot` to `lang\<language code>.po`, fill in the `msgstr`
  lines and run `uv run python -m unclefarmer --strings` to compile it. It then appears under Language in
  Settings.
- Urdu is provided as Roman Urdu in `lang\ur.po`: write it in Latin letters, not Nastaliq or other
  Arabic script. Uncle Farmer keeps wx in its English, left-to-right mode for it.
