# Spotify API
from datapipe import Datapipe
from trees import Trees
import spotipy

# Constants & Creds
from constants import *
from creds import *

# Miscellaneous
from datetime import datetime


class Maintain(Trees):
    """ Subclass of Tree for functions for helping maintain and fix the tree (like topheavy stuff).
        I'm subclassing it to separate the code a bit and keep it cleaner, same way I subclass in Minesweeper. """

    def __init__(self):
        # Spotipy is initialized in datapipe because it handles the API/data stuff
        self.dp = Datapipe(CLIENT_ID, CLIENT_SECRET, SPOTIPY_REDIRECT_URI, SCOPES)
        self.sp = self.dp.sp  # pull Spotipy instance out incase we need to make direct calls
        self.utils = self.dp.utils  # use the same instance of utils in both datapipe and trees

    # === MAINTAINING PLAYLIST TREE ===
    def check_topheavy(self, nodes: dict) -> tuple:
        """
        Traverses the playlist tree and finds out what tracks
            are missing from children playlists and what point they cut off.
            (ex: tracks in "Bass Music" playlist but absent from every playlist below that point).

        Args:
            sp (spotipy.Spotify): Spotify API client.
            nodes (dict): Subtree of playlist ID nodes and their children

        Returns:
            tuple: Returns a tuple containing a list of the accumulated tracks (for recursion purposes),
                and a dict of dicts containing the info on what tracks are missing from what playlist::

                [
                    "0QQwlREWKKxRUPPbpaKZJS",
                    "4rwpZEcnalkuhPyGkEdhu0",
                    "..."
                ]

                {
                    "694CE0Y64KwrjCXKShiCES": {
                    "missing tracks": [
                        "0U0ldCRmgCqhVvD6ksG63j",
                        "0Vj2je2PLl1TU78DAMArat",
                        "..."
                    ],
                    "child playlists": {...} <-- same thing repeats inside that dict
                }
        """
        accum_tracks = []  # the tracks found in here and below
        subtree = {}  # tree created for these nodes and below (gets connected to parent nodes)

        # iterates through every node (k) in this level and recurses its children (v)
        for k, v in nodes.items():
            if v is None:
                leaf_tracks = self.dp.get_playlist_tracks(k)  # [1]
                self.utils.filter_null(leaf_tracks)
                self.utils.extend_nodupes(accum_tracks, leaf_tracks)  # [2]
                subtree[k] = {'missing tracks': None, 'child playlists': None}  # [3]
            else:
                # [1] get all child accumulated tracks
                child_tracks, child_subtree = self.check_topheavy(v)

                # [2] get this playlist's tracks
                parent_tracks = self.dp.get_playlist_tracks(k)
                self.utils.filter_null(parent_tracks)

                # [3] find difference in playlists
                difference = self.utils.filter_items(parent_tracks, child_tracks)  # get every song in this playlist that's not below this playlist

                # [4] record difference tracks
                subtree[k] = {'missing tracks': difference, 'child playlists': child_subtree}

                # [5] add this playlist to master accumulated list
                self.utils.extend_nodupes(accum_tracks, parent_tracks)

        return accum_tracks, subtree

    # == playlist math
    def subtract_chunk(self, playlist_id: str, chunk: list):
        """
        Subtract a list of track IDs from a playlist.

        Args:
            sp (spotipy.Spotify): Spotify API client
            playlist_id (str): ID of the playlist being removed from
            chunk (list): List of tracks to remove from playlist
        """
        self.sp.playlist_remove_all_occurrences_of_items(playlist_id, chunk)
        print(f'removed {len(chunk)} songs from {self.utils.playlist_name_from_id(playlist_id)}')

    def minus_playlists(self, playlist_id: str, subtract_id: str):
        """
        Subtract a playlist's tracks from another playlist.

        Args:
            sp (spotipy.Spotify): Spotify API client
            playlist_id (str): ID of the playlist being removed from
            subtract_id (str): ID of the playlist to subtract
        """
        # TODO: make to check and only remove songs that are actually in the playlist to avoid errors
        chunk = self.dp.get_playlist_tracks(subtract_id)
        self.subtract_chunk(playlist_id, chunk)
        print(f'removed playlist "{self.utils.playlist_name_from_id(subtract_id)}" ({len(chunk)} songs) from playlist {self.utils.playlist_name_from_id(playlist_id)}')

    # ===== FINDING SONGS IN THE TREE =====
    def locate_songs(self, tracks: list, plist_tree: dict) -> dict:
        """ Given a list of tracks, checks every playlist in the tree and returns a dict of their locations. """
        track_locations = {tr: [] for tr in tracks}  # creates a dict of track locations, each track is given an empty list.
        self.pinpoint_song(tracks, plist_tree, track_locations)
        return track_locations

    def pinpoint_song(self, tracks: list, plist_tree: dict, locations: dict):
        """ Traverses the playlist tree and appends every playlist a track occurrence is found. """
        for k, v in plist_tree.items():
            if v is None:  # if this node is a leaf, then checks if any of the songs are in it
                plist_tracks = self.dp.get_playlist_tracks(k)
                for tr in tracks:
                    if tr in plist_tracks:  # if this track is in this playlist
                        locations[tr].append(k)
            else:  # else it has children so recurse down first then push the new tracks found
                self.pinpoint_song(tracks, v, locations)  # recurses into children and checks their locations first

                # after checking children, checks this playlist itself
                plist_tracks = self.dp.get_playlist_tracks(k)
                for tr in tracks:
                    if tr in plist_tracks:  # if this track is in this playlist
                        locations[tr].append(k)

# ⚠️ BUILD IN PROGRESS 🔨⚠️
    def lowest_pinpoint(self, track_id: str, plist_tree):
        """ Traverses tree and finds lowest position of song in the playlist tree."""
        pass

    # NOTE: find all locations of song
    #           VERSUS
    # NOTE: find lowest spot of song
    # this can maybe be done by taking the first found in all locations,
    # but I'm not sure if that works or I have to do it separately

    # === RANDOM COOL THING ===
    def cross_related_artists(self):
        """
            Goes through many artists and gets their related artists,
                then crosses all the artists and returns list of most
                seen artists across the pool of related artists and
                sorts them by frequency.
        """
        self.sp.artist_related_artists()
