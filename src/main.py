# main.py
#
# Copyright 2025 Unknown
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import gi
import threading
import os

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gio, Adw
from .window import YtmusicripperWindow

from .ytmusicdl import AlbumDownloader
from .queue_item import QueueItem


class YtmusicripperApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id="io.github.Ethanscharlie.ytmusicripper",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            resource_base_path="/io/github/Ethanscharlie/ytmusicripper",
        )
        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)
        self.create_action("rip", self.on_rip)

    def on_rip(self, *args):
        win = self.props.active_window
        if not win or not hasattr(win, "url_entry"):
            print("No entry field found!")
            return

        url = win.url_entry.get_text()
        print(f"Entry says: {url}")

        folder_raw = win.download_folder_combo.get_selected_item().get_string()
        folder = os.path.join(os.path.expanduser("~"), folder_raw.replace(r"~/", ""))

        win.queue_container.add(QueueItem(url, folder))

        win.url_entry.set_text("")

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """

        win = self.props.active_window
        if not win:
            win = YtmusicripperWindow(application=self)
        win.present()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
            application_name="ytmusicripper",
            application_icon="io.github.Ethanscharlie.ytmusicripper",
            developer_name="Ethanscharlie",
            version="1.0.0",
            developers=["Ethanscharlie"],
            copyright="© 2025 Ethanscharlie",
        )
        # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
        about.set_translator_credits(_("https://github.com/Ethanscharlie"))
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        print("app.preferences action activated")

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = YtmusicripperApplication()
    return app.run(sys.argv)
