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



HOME_MUSIC_FOLDER = os.path.join(os.path.expanduser("~"), "MusicT")
TESTING_URL = (
    r"https://music.youtube.com/playlist?list=OLAK5uy_lJvbSWPW4g9-u1Cs1I1zkfylSG0KBFpOo"
)


class AlbumDownloader:
    def __init__(
        self,
        action_row,
        status_label,
        url: str = TESTING_URL,
        folder: str = HOME_MUSIC_FOLDER,
    ):
        self.action_row = action_row
        self.status_label = status_label

        self.url = url
        self.folder = folder

        self.finishedDownloading = 0
        self.totalToDownload = 0

    def download(self):
        download_start_time = time.time()
        self.finishedDownloading = 0
        self.totalToDownload = 0

        self.status_label.set_label("Getting album info")

        parsedUrl = urlparse(self.url)
        hostname = parsedUrl.hostname or ""
        isCorrectDomain = "music.youtube.com" in hostname.lower()

        if not isCorrectDomain:
            self.action_row.set_title(f"Invalid url: {self.url}")
            self.action_row.set_subtitle("URL not from music.youtube.com")
            self.status_label.set_label("Failed")
            return

        try:
            album = self.__getAlbumFromURL(self.url)
        except URLIsNotAlbum:
            self.action_row.set_title(f"Invalid url: {self.url}")
            self.action_row.set_subtitle("URL is not an album")
            self.status_label.set_label("Failed")
            return
        except yt_dlp.utils.ExtractorError:
            self.action_row.set_title(f"Invalid url: {self.url}")
            self.action_row.set_subtitle("Extractor Error")
            self.status_label.set_label("Failed")
            return
        except yt_dlp.utils.DownloadError:
            self.action_row.set_title(f"Invalid url: {self.url}")
            self.action_row.set_subtitle("Download Error")
            self.status_label.set_label("Failed")
            return

        self.action_row.set_title(album.album)
        self.action_row.set_subtitle(f"{album.artist} * {self.folder}")
        self.totalToDownload = len(album.tracks)

        self.status_label.set_label("Creating Dirs")

        self.__createDirsFromFolderWithAlbum(self.folder, album)
        album_folder = os.path.join(self.folder, album.artist, album.album)

        self.status_label.set_label("Downloading album art")

        self.__downloadCoverArtToFolder(album.coverArtUrl, album_folder)

        self.status_label.set_label("Downloading content")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for track in album.tracks:
                executor.submit(
                    self.__downloadTrackAndWriteMetadata, album_folder, album, track
                )

        download_time = time.time() - download_start_time
        print(f"Download took {download_time:.2f} seconds")
        self.status_label.set_label(f"Finished in {download_time:.2f} seconds")

    def __downloadTrackAndWriteMetadata(
        self, albumFolder: str, album: Album, track: Track
    ):
        self.__download_content_to_folder(track.url, albumFolder, track.title)

        trackFile = os.path.join(albumFolder, f"{track.title}.mp3")
        self.__writeTextMetadataToExistingFile(album, track, trackFile)

        coverArtFile = os.path.join(albumFolder, "cover.jpg")
        self.__writeCoverArtToExistingFile(coverArtFile, trackFile)

        self.finishedDownloading += 1

        self.status_label.set_label(
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
    
    
    def __downloadCoverArtToFolder(self, url: str, folder: str):
        urllib.request.urlretrieve(url, os.path.join(folder, "cover.jpg"))
    
    
    def __getTrackListFromEntriesJson(self, entriesJson: str) -> list[Track]:
        tracks = []
        for i, data in enumerate(entriesJson):
            tracks.append(Track(self.__filterChars(data["title"]), data["url"], i + 1))
    
        return tracks
    
    
    def __getAlbumFromURL(self, url: str) -> Album:
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
                self.__getTrackListFromEntriesJson(info_dict["entries"]),
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
