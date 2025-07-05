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

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

import yt_dlp


@dataclass
class Track:
    title: str
    url: str


@dataclass
class Album:
    album: str
    artist: str
    year: int
    tracks: list[Track]


def filterChars(text: str) -> str:
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


def downloadCoverArtToFolder(url: str, folder: str):
    urllib.request.urlretrieve(url, os.path.join(folder, "cover.jpg"))

def getCoverArtUrlFromUrl(url: str) -> str:
    art_url = r"https://i9.ytimg.com/s_p/OLAK5uy_lJvbSWPW4g9-u1Cs1I1zkfylSG0KBFpOo/sddefault.jpg?sqp=CMiJosMGir7X7AMICJzHuL0GEAE=&rs=AOn4CLCnVEDk2attTi_T3Er6zf557N6NqA&v=1739465628"

    # os.system(f"yt-dlp {url} --write-info-json --flat-playlist")
    # TODO

    #filepath = ""
    #for file in os.listdir("."):
    #    if not file.endswith(".info.json"):
    #        continue
#j
    #    filepath = file

    #with open(filepath, "r") as f:
    #    data = json.loads(f.read())
    #    cover_art_url = data["thumbnails"][1]["url"]
    #    art_url = cover_art_url

    #os.remove(filepath)
    return art_url


def getTrackListFromEntriesJson(entriesJson: str) -> list[Track]:
    tracks = []
    for data in entriesJson:
        tracks.append(Track(filterChars(data["title"]), data["url"]))

    return tracks


def getAlbumFromURL(url: str) -> Album:
    ydl_opts = {
        'quiet': True,  # Suppress standard output
        'extract_flat': True,  # Equivalent to --flat-playlist
        'force_generic_extractor': True,  # Ensure it's using the generic extractor if necessary
    }

    album = None
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)

        tracks = getTrackListFromEntriesJson(info_dict["entries"])

        album = Album(
            filterChars(info_dict["title"].replace("Album - ", "")),
            filterChars(info_dict["entries"][0]["uploader"]),
            2020,
            tracks,
        )

    return album


def prepare_directory(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def createDirsFromFolderWithAlbum(folder: str, album: Album):
    if not os.path.exists(os.path.join(folder, album.artist)):
        os.makedirs(os.path.join(folder, album.artist))

    prepare_directory(os.path.join(folder, album.artist, album.album))


def download_and_assign_metadata_to_track(
    folder: str, album: Album, track: Track, index: int
):
    print(f"Name: {track.title}, Url: {track.url}, index: {index}")

    # Download video
    current_directory = os.getcwd()
    os.system(f"cd '{folder}'")

    command = (
        f'yt-dlp -x --audio-format mp3 -o "{folder}/{track.title}.%(ext)s" {track.url}'
    )
    print(command)
    os.system(command)
    os.system(f"cd '{current_directory}'")

    # Assign metadata
    audio_file = os.path.join(folder, f"{track.title}.mp3")
    tracknumer = index + 1

    audio = EasyID3(audio_file)

    audio.delete()
    audio["title"] = track.title
    audio["album"] = album.album
    audio["artist"] = album.artist
    audio["tracknumber"] = str(tracknumer)
    audio.save()

    # Set Cover art
    id3audio = MP3(audio_file, ID3=ID3)
    id3audio_tags: mutagen.id3.ID3 = id3audio.tags
    id3audio_tags.add(
        APIC(
            mime="image/jpeg",
            type=3,
            desc="Cover",
            data=open(os.path.join(folder, "cover.jpg"), "rb").read(),
        )
    )
    id3audio.save()


def main():
    download_start_time = time.time()

    #url = sys.argv[1]

    url = 'https://music.youtube.com/playlist?list=OLAK5uy_lJvbSWPW4g9-u1Cs1I1zkfylSG0KBFpOo'
    folder = os.path.join(os.path.expanduser("~"), "MusicT")
    #if len(sys.argv) > 2:
    #    folder = sys.argv[2]

    album = getAlbumFromURL(url)
    cover_art_url = getCoverArtUrlFromUrl(url)

    createDirsFromFolderWithAlbum(folder, album)
    album_folder = os.path.join(folder, album.artist, album.album)

    downloadCoverArtToFolder(cover_art_url, album_folder)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for i, track in enumerate(album.tracks):
            executor.submit(
                download_and_assign_metadata_to_track, album_folder, album, track, i
            )

    download_time = time.time() - download_start_time
    print(f"Download took {download_time:.2f} seconds")

