# queue_item.py
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

from gi.repository import Adw
from gi.repository import Gtk

from .ytmusicdl import AlbumDownloader
import threading

from collections.abc import Callable

@Gtk.Template(resource_path="/io/github/Ethanscharlie/albumripper/queue_item.ui")
class QueueItem(Adw.PreferencesGroup):
    __gtype_name__ = "queue_item"

    action_row = Gtk.Template.Child("action_row")
    status_label = Gtk.Template.Child()

    on_finish = lambda self: None


    def set_on_finish(self, run: Callable[["QueueItem"], None]):
        self.on_finish = run
        return self

    def __init__(self, url: str, download_folder: str, **kwargs):
        super().__init__(**kwargs)

        self.action_row.set_title(url)
        self.action_row.set_subtitle(download_folder)
        self.status_label.set_label("Waiting")

        self.downloader = AlbumDownloader(
            url, download_folder

        ).set_set_status_text(
            lambda text: self.status_label.set_label(text)

        ).set_set_action_row_text(
            lambda title, subtitle: (
                self.action_row.set_title(title),
                self.action_row.set_subtitle(subtitle)
            )

        ).set_on_url_error(
            lambda url, error: (
                self.action_row.set_title(error),
                self.action_row.set_subtitle(url),
                self.status_label.set_label("Failed"),
                self.on_finish(self)
            )

        ).set_on_finish(
            lambda: self.on_finish(self)
        )

    def start_download(self):
        threading.Thread(target=self.downloader.download).start()
