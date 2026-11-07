"""Help, Contact the developer: the address to write to, with buttons to write an email or copy it,
the Telegram channel where updates are announced (also Help, Telegram updates channel), and the
ways to donate (also Help, Donate)."""

from __future__ import annotations

import webbrowser
from collections.abc import Callable

import wx

from .. import __version__, contact
from ..i18n import _
from .common import Dialog, copy_text, error, labeled


def message() -> str:
    return (_("Questions or ideas? Write to the developer at {email}, or on Mastodon at {mastodon}. Bugs are best "
              "reported on GitHub, so everyone can see the fix: {issues}", email=contact.EMAIL,
              mastodon=contact.MASTODON, issues=contact.ISSUES)
            + "\n\n" + _("Every update is announced in the Telegram channel: {link}", link=contact.TELEGRAM)
            + "\n\n" + donate_message())


def donate_message() -> str:
    return _("Uncle Farmer is free. If it helps you and you'd like to give something back, you can donate "
             "with PayPal ({paypal}) or Ko-fi ({kofi}).", paypal=contact.PAYPAL, kofi=contact.KOFI)


def join_telegram(parent: wx.Window | None) -> None:
    """Help, Telegram updates channel (and its button here): the channel's invite link in the
    browser, which hands it to the Telegram app when one is installed."""
    if not webbrowser.open(contact.TELEGRAM):
        error(parent, _("No browser opened. The Telegram channel is at {link}", link=contact.TELEGRAM))


def donate(parent: wx.Window | None, link: str) -> None:
    """A donation page (PayPal or Ko-fi) in the browser."""
    if not webbrowser.open(link):
        error(parent, _("No browser opened. You can donate at {link}", link=link))


def write_email() -> bool:
    """Open the player's email program on a new message to the developer."""
    return webbrowser.open(contact.mailto("Uncle Farmer %s" % __version__))


def donate_buttons(parent: wx.Window) -> list[tuple[str, Callable[[wx.CommandEvent], None]]]:
    return [(_("Donate with &PayPal"), lambda e: donate(parent, contact.PAYPAL)),
            (_("Donate with &Ko-fi"), lambda e: donate(parent, contact.KOFI))]


class ContactDialog(Dialog):
    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent, title=_("Contact the developer"))
        root = wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer(wx.VERTICAL)
        about = wx.StaticText(self, label=message())
        about.Wrap(460)
        box.Add(about, 0, wx.TOP, 4)
        self.address = labeled(self, box, _("&Email address:"),
                               lambda p: wx.TextCtrl(p, value=contact.EMAIL, style=wx.TE_READONLY))
        row = wx.BoxSizer(wx.HORIZONTAL)
        for label, handler in [(_("&Write an email"), self.on_write), (_("&Copy the address"), self.on_copy),
                               (_("&Telegram updates channel"), self.on_telegram), *donate_buttons(self)]:
            b = wx.Button(self, label=label)
            b.Bind(wx.EVT_BUTTON, handler)
            row.Add(b, 0, wx.RIGHT, 8)
        row.AddStretchSpacer()
        row.Add(wx.Button(self, wx.ID_CANCEL, _("&Close")))
        box.Add(row, 0, wx.EXPAND | wx.TOP, 12)
        root.Add(box, 1, wx.EXPAND | wx.ALL, 12)
        self.SetSizerAndFit(root)
        self.address.SetFocus()

    def on_telegram(self, evt: wx.CommandEvent) -> None:
        join_telegram(self)

    def on_write(self, evt: wx.CommandEvent) -> None:
        if not write_email():
            error(self, _("No email program opened. Write to {email} from your email.", email=contact.EMAIL))

    def on_copy(self, evt: wx.CommandEvent) -> None:
        if copy_text(contact.EMAIL):
            wx.MessageBox(_("Copied {email}.", email=contact.EMAIL), _("Contact the developer"), wx.OK, self)
        else:
            error(self, _("Couldn't copy it. The address is {email}", email=contact.EMAIL))


class DonateDialog(Dialog):
    """Help, Donate: one sentence and a button for each way to give."""

    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent, title=_("Donate"))
        root = wx.BoxSizer(wx.VERTICAL)
        about = wx.StaticText(self, label=donate_message())
        about.Wrap(460)
        root.Add(about, 0, wx.ALL, 12)
        row = wx.BoxSizer(wx.HORIZONTAL)
        first: wx.Button | None = None
        for label, handler in donate_buttons(self):
            b = wx.Button(self, label=label)
            b.Bind(wx.EVT_BUTTON, handler)
            row.Add(b, 0, wx.RIGHT, 8)
            first = first or b
        row.AddStretchSpacer()
        row.Add(wx.Button(self, wx.ID_CANCEL, _("&Close")))
        root.Add(row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        self.SetSizerAndFit(root)
        if first:
            first.SetFocus()
