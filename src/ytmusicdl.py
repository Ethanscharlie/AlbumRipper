#!/usr/bin/env python3

"""
Written by Ethanscharlie
https://github.com/Ethanscharlie
"""

import json
import os
import concurrent.futures
import shutil
from dataclasses import dataclass
import time
import sys
import urllib
from urllib.parse import urlparse
from collections.abc import Callable

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

import yt_dlp


class URLIsNotAlbum(Exception):
    pass


@dataclass
class Track:
    title: str
    url: str
    index: int  # Starting at 1


@dataclass
class Album:
    album: str
    artist: str
    year: int
    tracks: list[Track]
    coverArtUrl: str


class AlbumDownloader:
    def __init__(self, url: str, folder: str):
        self.url = url
        self.folder = folder

        self.set_status_text = lambda text: None
        self.set_action_row_text = lambda title, subtitle: None
        self.on_url_error = lambda url, error: None
        self.on_finish = lambda: None

        self.finishedDownloading = 0
        self.totalToDownload = 0

    def set_set_status_text(self, run: Callable[[str], None]):
        self.set_status_text = run
        return self

    def set_set_action_row_text(self, run: Callable[[str, str], None]):
        self.set_action_row_text = run
        return self

    def set_on_url_error(self, run: Callable[[str, str], None]):
        self.on_url_error = run
        return self

    def set_on_finish(self, run: Callable[[], None]):
        self.on_finish = run
        return self

    def download(self):
        download_start_time = time.time()
        self.finishedDownloading = 0
        self.totalToDownload = 0

        self.set_status_text("Getting album info")

        parsedUrl = urlparse(self.url)
        hostname = parsedUrl.hostname or ""
        isCorrectDomain = "music.youtube.com" in hostname.lower()

        if not isCorrectDomain:
            self.on_url_error(self.url, "URL not from music.youtube.com")
            return

        try:
            album = self.__get_album_from_url(self.url)
        except URLIsNotAlbum:
            self.on_url_error(self.url, "URL is not an album")
            return
        except yt_dlp.utils.ExtractorError:
            self.on_url_error(self.url, "Extractor Error")
            return
        except yt_dlp.utils.DownloadError:
            self.on_url_error(self.url, "Download Error")
            return

        self.set_action_row_text(album.album, f"{album.artist} · {self.folder}")
        self.set_status_text("Starting Download")

        self.totalToDownload = len(album.tracks)

        self.__createDirsFromFolderWithAlbum(self.folder, album)
        album_folder = os.path.join(self.folder, album.artist, album.album)

        self.__download_cover_art_to_folder(album.coverArtUrl, album_folder)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for track in album.tracks:
                executor.submit(
                    self.__downloadTrackAndWriteMetadata, album_folder, album, track
                )

        download_time = time.time() - download_start_time
        print(f"Download took {download_time:.2f} seconds")
        self.set_status_text(f"Finished in {download_time:.2f} seconds")
        self.on_finish()

    def __downloadTrackAndWriteMetadata(
        self, albumFolder: str, album: Album, track: Track
    ):
        self.__download_content_to_folder(track.url, albumFolder, track.title)

        trackFile = os.path.join(albumFolder, f"{track.title}.mp3")
        self.__writeTextMetadataToExistingFile(album, track, trackFile)

        coverArtFile = os.path.join(albumFolder, "cover.jpg")
        self.__writeCoverArtToExistingFile(coverArtFile, trackFile)

        self.finishedDownloading += 1

        self.set_status_text(
            f"Downloading content {self.finishedDownloading}/{self.totalToDownload}"
        )

    def __filterChars(self, text: str) -> str:
        return (
            text.replace("\\", "_")
            .replace("/", "_")
            .replace(":", "_")
            .replace("*", "_")
            .replace("?", "_")
            .replace('"', "_")
            .replace("<", "_")
            .replace(">", "_")
            .replace("|", "_")
        )

    def __download_cover_art_to_folder(self, url: str, folder: str):
        urllib.request.urlretrieve(url, os.path.join(folder, "cover.jpg"))

    def __get_track_list_from_entries_json(self, entriesJson: str) -> list[Track]:
        tracks = []
        for i, data in enumerate(entriesJson):
            tracks.append(Track(self.__filterChars(data["title"]), data["url"], i + 1))

        return tracks

    def __get_album_from_url(self, url: str) -> Album:
        ydl_opts = {
            "quiet": True,
            "extract_flat": True,
            "force_generic_extractor": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            if not "entries" in info_dict:
                raise URLIsNotAlbum("No entries key found")

            return Album(
                self.__filterChars(info_dict["title"].replace("Album - ", "")),
                self.__filterChars(info_dict["entries"][0]["uploader"]),
                2020,
                self.__get_track_list_from_entries_json(info_dict["entries"]),
                info_dict["thumbnails"][1]["url"],
            )

        raise Exception("Could not get album info from ytdlp")

    def __createDirsFromFolderWithAlbum(self, folder: str, album: Album):
        if not os.path.exists(os.path.join(folder, album.artist)):
            os.makedirs(os.path.join(folder, album.artist))

        albumPath = os.path.join(folder, album.artist, album.album)
        if os.path.exists(albumPath):
            shutil.rmtree(albumPath)
        os.makedirs(albumPath)

    def __download_content_to_folder(self, track_url, folder, track_title):
        current_directory = os.getcwd()
        os.system(f"cd '{folder}'")

        ydl_opts = {
            "quiet": True,
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }
            ],
            "outtmpl": f"{folder}/{track_title}.%(ext)s",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([track_url])

        os.system(f"cd '{current_directory}'")

    def __writeTextMetadataToExistingFile(self, album: Album, track: Track, file: str):
        if not os.path.exists(file):
            raise Exception(f"File for track {track}, at {file} doesn't exist")

        audio = EasyID3(file)
        audio.delete()
        audio["title"] = track.title
        audio["album"] = album.album
        audio["artist"] = album.artist
        audio["tracknumber"] = str(track.index)
        audio.save()

    def __writeCoverArtToExistingFile(self, coverArtFile: str, file: str):
        if not os.path.exists(file):
            raise Exception(f"File for track {file} doesn't exist")

        if not os.path.exists(coverArtFile):
            raise Exception("Cover art file doesn't exit")

        id3audio = MP3(file, ID3=ID3)
        id3audio_tags: mutagen.id3.ID3 = id3audio.tags
        id3audio_tags.add(
            APIC(
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=open(coverArtFile, "rb").read(),
            )
        )
        id3audio.save()
