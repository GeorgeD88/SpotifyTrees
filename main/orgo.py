from datetime import datetime
from datapipe import Datapipe
from random_tools import Extra
from creds import *
from constants import *
import spotipy


class Orgo:

    # API Call Limits
    ADD_MAX = 100
    DEL_MAX = 50

    def __init__(self) -> None:
        self.datapipe = Datapipe(CLIENT_ID, CLIENT_SECRET, SPOTIPY_REDIRECT_URI)
        self.sp = self.datapipe.sp
        self.utils = self.datapipe.utils
        self.extra = Extra(self.sp, self.utils)

    # ===== MAIN ORGOMASTER FUNCTION =====
    def update_playlist_tree(self, tree_of_ids: dict) -> list:
        """
        Combines all the function calls used to update the playlist tree into one function.

        Args:
            sp (spotipy.Spotify): Spotify API client
            tree_of_ids (dict): Tree of playlist IDs

        Returns:
            list: Returns a list of the new tracks found within the whole playlist tree::

                [
                    "0QQwlREWKKxRUPPbpaKZJS",
                    "4rwpZEcnalkuhPyGkEdhu0",
                    "4Loz57Oql0UYKtdRoGCumT",
                    "..."
                ]
        """
        last_checked = self.utils.get_time_checked()  # gets time of last program run (last checked)
        print('finding new songs!')
        new_songs = self.traverse_playlists(tree_of_ids, last_checked)  # updates tree and returns new songs found
        current = datetime.utcnow()  # gets current time to update time last checked
        self.utils.record_time_checked(current)  # records to JSON the time finished checking

        # NOTE: songs returned by function are only new to EDM I think,
        # so if it's new in a child but already in EDM it might not show up in the end I think :/

        # prints all new songs found
        if len(new_songs) > 0:
            print(f'-----------------\n{len(new_songs)} new songs found:')
            self.utils.print_track_names(new_songs)
        else:
            print(f'-----------------\nno new songs found!')

        return new_songs


    def check_new(self, playlist_id: str, last_checked: datetime) -> list:
        """
        Finds new tracks in playlist added after the playlist tree was last updated/checked.

        Args:
            sp (spotipy.Spotify): Spotify API client
            playlist_id (str): ID of the playlist being checked
            last_checked (datetime): Time the playlists were last updated/checked

        Returns:
            list: Returns a list of the new tracks found within this playlist::

                [
                    "0QQwlREWKKxRUPPbpaKZJS",
                    "4rwpZEcnalkuhPyGkEdhu0",
                    "4Loz57Oql0UYKtdRoGCumT",
                    "..."
                ]
        """
        results = self.sp.playlist_tracks(playlist_id)  # first pull of tracks from playlist
        new_tracks = []  # defines list for new tracks found

        def nested():
            for tr in results['items']:
                # if the time the track was added is greater than the time last checked
                if self.utils.convert_from_isostring(tr['added_at']) > last_checked:
                    new_tracks.append(tr['track']['id'])  # then add the track ID to list of new tracks

        nested()
        while results['next']:
            results = self.sp.next(results)
            nested()

        return new_tracks


    def traverse_playlists(self, nodes: dict, last_checked: datetime) -> list:
        """
        Traverses the playlist tree and pushes all new songs found up the tree.

        Args:
            sp (spotipy.Spotify): Spotify API client
            nodes (dict): Subtree of playlist ID nodes and their children
            last_checked (datetime): Time the playlists were last updated/checked

        Returns:
            list: Returns a list of the new tracks found within the whole playlist tree::

                [
                    "0QQwlREWKKxRUPPbpaKZJS",
                    "4rwpZEcnalkuhPyGkEdhu0",
                    "4Loz57Oql0UYKtdRoGCumT",
                    "..."
                ]
        """
        new_tracks = []  # defines list for new tracks collectively found in this level

        # iterates through every node (k) in this level and recurses its children (v)
        for k, v in nodes.items():
            if v is None:  # if this node is a leaf, then grab the new songs and add to tracks found
                leaf_tracks = self.check_new(k, last_checked)
                self.utils.extend_nodup(new_tracks, leaf_tracks)
            else:  # else it has children so recurse down first then push the new tracks found
                # [1] get new tracks from child nodes
                children_new = self.traverse_playlists(v, last_checked)

                # [2] get new tracks of this node but hold it in a temp first
                here_new = self.utils.not_in(self.check_new(k, last_checked), new_tracks)

                self.utils.filter_null(children_new)  # removes all Nones from list first cause that's a new problem idk why,
                                                         # I think it's cause of the new local files it's starting to include those in the list ig

                # [3] push children's new tracks to this node
                if len(children_new) > 0:
                    self.push_new(k, children_new)

                # [4] combine new and child
                self.utils.extend_nodup(children_new, here_new)  # children_new + here_new
                # [5] add combo of new and child to new_tracks
                self.utils.extend_nodup(new_tracks, children_new)  # new_tracks + (children_new + here_new)

        self.utils.filter_null(new_tracks)
        return new_tracks


    def push_new(self, playlist_id: str, tracks_add: list):
        """
        Add tracks to Spotify playlists, while avoiding duplicates.

        Args:
            sp (spotipy.Spotify): Spotify API client
            playlist_id (str): ID of the playlist being added to
            last_checked (datetime): Time the playlists were last updated/checked
        """
        playlist_tracks = self.datapipe.get_playlist_tracks(playlist_id)
        # removes existing tracks in playlist from list tracks to add
        new_tracks_only = self.utils.not_in(tracks_add, playlist_tracks)

        # checking if there are still any tracks to add after removing existing ones
        if len(new_tracks_only) > 0:
            # checks if tracks needs to be broken up into chunks to avoid API call limit
            if len(new_tracks_only) > add_MAX:  # NOTE: convert this into function
                tracks_chunks = self.utils.divide_chunks(new_tracks_only, add_MAX)
                for chunk in tracks_chunks:
                    self.sp.playlist_add_items(playlist_id, chunk)
            else:
                try:
                    self.sp.playlist_add_items(playlist_id, new_tracks_only)
                except Exception as e:
                    print(e)
                    print('\n\n\n')
                    print(self.utils.playlist_name_from_id(playlist_id))
                    print(new_tracks_only)

        else:
            print('new items in sub playlists already in: ' + self.utils.playlist_name_from_id(playlist_id))


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
                leaf_tracks = self.datapipe.get_playlist_tracks(k)  # [1]
                self.utils.filter_null(leaf_tracks)
                self.utils.extend_nodup(accum_tracks, leaf_tracks)  # [2]
                subtree[k] = {'missing tracks': None, 'child playlists': None}  # [3]
            else:
                # [1] get all child accumulated tracks
                child_tracks, child_subtree = self.check_topheavy(v)

                # [2] get this playlist's tracks
                parent_tracks = self.datapipe.get_playlist_tracks(k)
                self.utils.filter_null(parent_tracks)

                # [3] find difference in playlists
                difference = self.utils.not_in(parent_tracks, child_tracks)  # get every song in this playlist that's not below this playlist

                # [4] record difference tracks
                subtree[k] = {'missing tracks': difference, 'child playlists': child_subtree}

                # [5] add this playlist to master accumulated list
                self.utils.extend_nodup(accum_tracks, parent_tracks)

        return accum_tracks, subtree


    # ===== PLAYLIST MATH =====
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
        chunk = self.datapipe.get_playlist_tracks(subtract_id)
        self.subtract_chunk(playlist_id, chunk)
        print(f'removed playlist "{self.utils.playlist_name_from_id(subtract_id)}" ({len(chunk)} songs) from playlist {self.utils.playlist_name_from_id(playlist_id)}')


    def cross_related_artists(self):
        """
            Goes through many artists and gets their related artists,
                then crosses all the artists and returns list of most
                seen artists across the pool of related artists and
                sorts them by frequency.
        """
        self.sp.artist_related_artists()


    # ===== FINDING SONGS IN TREE =====
    def locate_songs(self, tracks: list, plist_tree: dict) -> dict:
        """ Given a list of tracks, checks every playlist in the tree and returns a dict of their locations. """
        track_locations = {tr: [] for tr in tracks}  # creates a dict of track locations, each track is given an empty list.
        self.pinpoint_song(tracks, plist_tree, track_locations)
        return track_locations

    def pinpoint_song(self, tracks: list, plist_tree: dict, locations: dict):
        """ Traverses the playlist tree and appends every playlist a track occurrence is found. """
        for k, v in plist_tree.items():
            if v is None:  # if this node is a leaf, then checks if any of the songs are in it
                plist_tracks = self.datapipe.get_playlist_tracks(k)
                for tr in tracks:
                    if tr in plist_tracks:  # if this track is in this playlist
                        locations[tr].append(k)
            else:  # else it has children so recurse down first then push the new tracks found
                self.pinpoint_song(tracks, v, locations)  # recurses into children and checks their locations first

                # after checking children, checks this playlist itself
                plist_tracks = self.datapipe.get_playlist_tracks(k)
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
    # but I'm not sure if that works or I have to do it seperately


# TODO: CHECK FOR MULTIPLE PLAYLISTS W/ SAME NAME AND RAISE THE CONFLICT
# TODO: SEARCH FOR SONGS NOT IN EDM
# TODO: SOMETHING ELSE I FORGOT FOR FIXING PAST JUNK


"""
recommendations(seed_artists=None,
seed_genres=None, seed_tracks=None,
limit=20, country=None, **kwargs)
https://spotipy.readthedocs.io/en/2.16.1/#spotipy.client.Spotify.recommendations
"""