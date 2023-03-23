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

        new_songs = self.update_playlists(id_tree, last_checked)  # updates tree and returns new songs found

        current_time = datetime.utcnow()  # gets current time to update time last checked
        self.record_time_checked(current_time)  # records the time finished checking to JSON

        # TODO: make sure that you can use the same playlist tracks state and that it's not important for it to keep calling
        # cause maybe it's significant for it to keep calling cause it needs the state of the playlist after adding shit during a recursion or something

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
                leaf_new_tracks, playlist_tracks = self.newly_added_tracks(root, last_checked)
                self.utils.extend_nodupes(new_tracks, leaf_new_tracks)
            # else it has children so recurse down first before pushing this playlist's new tracks
            else:
                # [1] get new tracks from children
                children_new = self.update_playlists(children, last_checked)

                # [2] get new tracks of this node but hold it in a temp first
                root_new_tracks, playlist_tracks = self.newly_added_tracks(root, last_checked)
                # we also grabbed playlist tracks as a set for use by push_new_tracks

                # [3] push children's new tracks to this node
                if len(children_new) > 0:
                    self.push_new_tracks(root, playlist_tracks, children_new)

                # [4] combine new and child
                self.utils.extend_nodupes(children_new, root_new_tracks)  # children_new + root_new_tracks

                # [5] add combo of new and child to new_tracks
                self.utils.extend_nodupes(new_tracks, children_new)  # new_tracks + (children_new + root_new_tracks)

        return new_tracks

    # was: check_new()
    def newly_added_tracks(self, playlist_id: str, last_checked: datetime) -> tuple[list, set]:
        """ Finds new tracks in playlist added after the playlist tree was last updated/checked. """
        results = self.sp.playlist_tracks(playlist_id)  # first pull of tracks from playlist
        playlist_tracks = set()  # stores all playlist tracks
        new_tracks = []  # defines list for new tracks found

        def nested():
            for tr in results['items']:
                # ignores null IDs this way so that you don't have to filter them later
                if tr['track']['id'] is not None:
                    playlist_tracks.add(tr['track']['id'])  # adds track to all playlist tracks
                    # if the time the track was added is greater than the time last checked
                    if self.utils.convert_from_isostring(tr['added_at']) > last_checked:
                        new_tracks.append(tr['track']['id'])  # then add the track ID to list of new tracks

        nested()
        while results['next']:
            results = self.sp.next(results)
            nested()

        return new_tracks, playlist_tracks

    # was: push new
    def push_new_tracks(self, playlist_id: str, playlist_tracks: set, tracks_add: list):
        """ Add tracks to Spotify playlists, while avoiding duplicates. """
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

    # === TIME RECORDING ===
    def get_time_checked(self, filename: str = 'time_checked') -> datetime:
        """ Returns the time checked from the JSON file. """
        time_string = self.utils.read_json(filename)[filename]
        return self.utils.convert_from_isostring(time_string)

    def record_time_checked(self, time_checked: datetime, filename: str = 'time_checked'):
        """ Records the time checked into the JSON file. """
        time_string = self.utils.convert_to_isostring(time_checked)
        self.utils.write_json(filename, {filename: time_string})

"""
TODO: something interesting to try later
recommendations(seed_artists=None,
seed_genres=None, seed_tracks=None,
limit=20, country=None, **kwargs)
https://spotipy.readthedocs.io/en/2.16.1/#spotipy.client.Spotify.recommendations
"""