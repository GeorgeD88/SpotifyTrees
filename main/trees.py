# Spotify API
from datapipe import Datapipe
import spotipy

# Constants & Creds
from constants import *
from creds import *

# Miscellaneous
from datetime import datetime


class Trees:

    def __init__(self):
        # Spotipy is initialized in datapipe because it handles the API/data stuff
        self.dp = Datapipe(CLIENT_ID, CLIENT_SECRET, SPOTIPY_REDIRECT_URI, SCOPES)
        self.sp = self.dp.sp  # pull Spotipy instance out incase we need to make direct calls
        self.utils = self.dp.utils  # use the same instance of utils in both datapipe and trees

    # === SPOTIFY TREES ===
    def update_playlist_tree(self, id_tree: dict) -> list:
        """ Combines all the function calls used to update the playlist tree into one function. """
        last_checked = self.get_time_checked()  # gets time of last program run (last checked)

        print('finding new songs!')
        print('='*18)

        self.dp.initialize_playlist_tracks_cache()  # initialize cache
        new_songs = self.update_playlists(id_tree, last_checked)  # updates tree and returns new songs found

        current_time = datetime.utcnow()  # gets current time to update time last checked
        self.record_time_checked(current_time)  # records the time finished checking to JSON

        self.dp.destroy_cache()  # destroys cache created during runtime
        # TODO: make sure that you can use the same playlist tracks state and that it's not important for it to keep calling
        # cause maybe it's significant for it to keep calling cause it needs the state of the playlist after adding shit during a recursion or something

        # NOTE: songs returned by function are only new to EDM I think,
        # so if it's new in a child but already in EDM it might not show up in the end I think :/
        # TODO: test this theory ^^

        # prints all new songs found
        if len(new_songs) > 0:
            to_print = f'{len(new_songs)} new songs found:'
            print(f"{'-'*len(to_print)}\n{to_print}")
            self.utils.print_track_names(new_songs)
        else:
            print('-'*19 + '\nno new songs found!')

        return new_songs

    # was: traverse_playlists()
    def update_playlists(self, forest: dict, last_checked: datetime) -> list:
        """ Repeatedly pushes newly added songs to all parent nodes. """
        new_tracks = []  # defines list for new tracks collectively found in this level

        # iterates through every tree in this forest level and recurses its children
        for root, children in forest.items():
            # root is a leaf, so grab the new songs and add to tracks found
            if children is None:
                leaf_tracks = self.newly_added_tracks(root, last_checked)
                self.utils.extend_nodupes(new_tracks, leaf_tracks)
            # else it has children so recurse down first before pushing this playlist's new tracks
            else:
                # [1] get new tracks from children
                children_new = self.update_playlists(children, last_checked)

                # [2] get new tracks of this node but hold it in a temp first
                here_new = self.newly_added_tracks(root, last_checked)
                """ TODO: I think technically LRU cache can deal with the caching
                for us because it will save the return of the function, the return value being the list of IDs. """

                """ FIXME: both newly_added_tracks and push_new_tracks pull the Spotify playlist's tracks,
                so we should only make it pull once using the cache. the problem is that newly added tracks doesn't just need
                a list of the track IDs, it needs the time added too so it has to do the crawling itself instead of using the method from datapipe.
                maybe just make an extra function that runs above step 2 and make it generate both stuff, then just pass that data to both functions. """

                # [3] push children's new tracks to this node
                if len(children_new) > 0:
                    self.push_new_tracks(root, children_new)

                # [4] combine new and child
                self.utils.extend_nodupes(children_new, here_new)  # children_new + here_new

                # [5] add combo of new and child to new_tracks
                self.utils.extend_nodupes(new_tracks, children_new)  # new_tracks + (children_new + here_new)

        return new_tracks

    # was: check_new()
    def newly_added_tracks(self, playlist_id: str, last_checked: datetime) -> list:
        """ Finds new tracks in playlist added after the playlist tree was last updated/checked. """
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

    # was: push new
    def push_new_tracks(self, playlist_id: str, tracks_add: list):
        """ Add tracks to Spotify playlists, while avoiding duplicates. """
        playlist_tracks = self.dp.get_playlist_tracks(playlist_id)
        # removes existing tracks in playlist from list tracks to add
        new_tracks_only = self.utils.filter_items(tracks_add, playlist_tracks)

        # checking if there are still any tracks to add after removing existing ones
        if len(new_tracks_only) > 0:
            # checks if tracks needs to be broken up into chunks to avoid API call limit
            if len(new_tracks_only) > ADD_MAX:  # NOTE: convert this into function
                tracks_chunks = self.utils.divide_chunks(new_tracks_only, ADD_MAX)
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

    # === TIME RECORDING ===
    def get_time_checked(self, filename: str = 'time_checked') -> datetime:
        """ Returns the time checked from the JSON file. """
        time_string = self.read_json(filename)[filename]
        return self.convert_from_isostring(time_string)

    def record_time_checked(self, time_checked: datetime, filename: str = 'time_checked'):
        """ Records the time checked into the JSON file. """
        time_string = self.convert_to_isostring(time_checked)
        self.write_json(filename, {filename: time_string})

"""
TODO: something interesting to try later
recommendations(seed_artists=None,
seed_genres=None, seed_tracks=None,
limit=20, country=None, **kwargs)
https://spotipy.readthedocs.io/en/2.16.1/#spotipy.client.Spotify.recommendations
"""