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


@Gtk.Template(resource_path="/io/github/Ethanscharlie/albumripper/queue_item.ui")
class QueueItem(Adw.PreferencesGroup):
    __gtype_name__ = "queue_item"

    action_row = Gtk.Template.Child("action_row")
    status_label = Gtk.Template.Child()

    def __init__(self, url: str, download_folder: str, **kwargs):
        super().__init__(**kwargs)
        downloader = AlbumDownloader(
            self.action_row, self.status_label, url, download_folder
        )
        threading.Thread(target=downloader.download).start()
