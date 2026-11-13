# What Mist Bot changes in Uncle Farmer

Mist Bot is a fork of [Uncle Farmer](https://github.com/afnannasir/uncle-farmer). Its `dev` branch
takes in Uncle Farmer's `dev` from time to time. This file lists what the fork changes, so a merge
keeps it, and says how each kind of conflict is settled.

## Merging from upstream

```
uv run python sync_upstream.py          what's new upstream, and which files would conflict
uv run python sync_upstream.py merge    merge, settle the usual conflicts, rebuild generated files
uv run pytest tests/test_fork.py        did the merge undo anything below?
uv run python check.py                  everything else
```

`sync_upstream.py merge` commits nothing. It settles these by itself:

- **Version** (`pyproject.toml`, `unclefarmer/__init__.py`, `uv.lock`): the fork's own numbers.
  Upstream numbers its releases differently (1.1.0 while the fork was at 1.0.6).
- **Requirements**: exported again from the merged `uv.lock`.
- **Translations**: upstream's `.pot`, `.po` and `.mo`, then the fork's own Roman Urdu put back
  where upstream's file has none (Donate, the Control tab), then rebuilt.
- **README.md and CONTRIBUTING.md**: the fork's. Upstream has rewritten both in a style the fork
  doesn't use. New facts in upstream's version are carried over by hand.

Left for a person:

- **CHANGELOG.md**: upstream sometimes adds its new entries to a section the fork has already
  released. They go under `## Unreleased`, above the fork's newest version.
- **docs/USER_GUIDE.md**: the fork's plain guide stays; upstream's new facts are written into it.
- **Code**: see below. Most of the fork's code is in files upstream doesn't have, so code
  conflicts are rare and small.

Upstream's tags are never fetched: it has its own `v1.0.1`.

## The fork's changes

Each is held by a test in `tests/test_fork.py`.

| What | Where |
|---|---|
| Updates from this fork's releases, one signed exe (Ed25519, `MistBot-update-v1`) | `unclefarmer/updater.py`, `release.py` |
| Releases also carry `MistBot-<version>.zip`, the exe in a `Mist Bot` folder | `release.py` |
| One exe build (Nuitka onefile) | `build_exe.py`, `unclefarmer/paths.py` |
| Contact, Telegram updates channel, donations (Ernesto's) | `unclefarmer/contact.py`, `unclefarmer/gui/contact.py`, Help menu in `unclefarmer/gui/main.py` |
| Update check every 6 hours while open | `unclefarmer/gui/mainparts/updates.py`, `first_run` in `editing.py` |
| Control by other programs (MCP) | new files `unclefarmer/control.py`, `unclefarmer/mcpserver.py`, `unclefarmer/gui/remote.py`; hooks listed below |
| Web page | `site/mistbot/index.html` (www.kurnal.tech/mistbot/) |

The MCP feature touches upstream's files only at these points, each a few lines:

- `unclefarmer/__main__.py`: `--mcp` starts `mcpserver.main()`.
- `unclefarmer/settings.py`: `mcp_control` and `mcp_raw_agent` in `APP_DEFAULTS` and `AppSettings`.
- `unclefarmer/gui/main.py`: `self.events`, `self.event_lock`, `self.event_seq`, `self.remote`, and
  `remote.stop()` in `on_close`.
- `unclefarmer/gui/mainparts/logpane.py`: `_append` numbers each log line into `self.events`.
- `unclefarmer/gui/mainparts/runs.py`: `errand_on(pid, ...)`, which `run_errand` now calls.
- `unclefarmer/gui/mainparts/editing.py`: `first_run` starts `self.remote`.
- `unclefarmer/gui/mainparts/base.py`: the declarations of the above.
- `unclefarmer/gui/setup.py`: the Control tab.

A new tool goes in `control.TOOLS` with a `t_<name>` method in `gui/remote.py`. It calls the
window's or the engine's own functions, so upstream's changes to those reach it without a merge.
