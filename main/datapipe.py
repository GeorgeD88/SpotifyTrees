# Spotify API
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Utils & Constants
from utils import Utils
from constants import *


class Datapipe:
    """ Wrapper that makes it clean and easy to retrieve Spotify data.
        (avoids you having you to deal with the mess of JSON data) """

    def __init__(self, client_id, client_secret, redirect_uri, scopes):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scopes
        ))
        self.utils = Utils(self.sp)

    def my_id(self) -> str:
        """ Returns ID of user logged into the API. """
        return self.sp.current_user()['id']

    # === USER PLAYLISTS ===
    def get_user_playlists(self) -> list:
        """ Returns a list of IDs of all of the user's playlists. """
        results = self.sp.current_user_playlists()
        playlists = []

        def nested():
            playlists.extend([p['id'] for p in results['items']])

        nested()
        while results['next']:
            results = self.sp.next(results)
            nested()

        return playlists

    def get_user_playlist_names(self) -> list:
        """ Returns a list of names of all of the user's playlists. """
        results = self.sp.current_user_playlists()
        playlists = []

        def nested():
            playlists.extend([p['name'] for p in results['items']])

        nested()
        while results['next']:
            results = self.sp.next(results)
            nested()

        return playlists

    def playlists_name_id_pair(self) -> dict:
        """ Returns a dict of name ID pairs for all of the user's playlists. """
        results = self.sp.current_user_playlists()
        playlists = {}

        def nested():
            for p in results['items']:
                if p['name'] in playlists:
                    prev = playlists[p['name']]
                    print(f"playlist \"{p['name']}\" already exists with ID \"{prev}\" (P) yet same name was found with ID \"{p['id']}\" (N)")
                    while True:
                        choice = input('input the playlist letter you would like to use: P/N').upper()
                        if choice == 'P':  # keep previous (existing) playlist ID: do nothing
                            break
                        elif choice == 'N':  # use the newly found playlist ID: replace ID
                            playlists[p['name']] = p['id']
                            break
                        else:
                            print('unknown input, use P or N')
                else:
                    playlists[p['name']] = p['id']

        nested()
        while results['next']:
            results = self.sp.next(results)
            nested()

        return playlists

    def playlists_id_name_pair(self) -> dict:
        """ Returns a dict of ID name pairs for all of the user's playlists. """
        results = self.sp.current_user_playlists()
        playlists = {}

        def nested():
            for p in results['items']:
                try:
                    playlists[p['id']]
                except KeyError:
                    playlists[p['id']] = p['name']

        nested()
        while results['next']:
            results = self.sp.next(results)
            nested()

        return playlists

    # === PLAYLIST CREATION/MANAGEMENT ===
    def new_playlist(self, playlist_name: str) -> str:
        """ Creates a new playlist with given name and returns the newly created playlist's ID. """
        self.sp.user_playlist_create(self.my_id(), playlist_name)
        return self.utils.playlist_id_from_name(playlist_name)

    def add_playlist_tracks(self, playlist_id: str, tracks: list):
        """ Adds the given tracks to the given playlist. """
        tracks_chunks = self.utils.divide_chunks(tracks, 100)
        for chunk in tracks_chunks:
            self.sp.playlist_add_items(playlist_id, chunk)

    # === PLAYLIST CONTENTS ===
    def get_playlist_tracks(self, playlist_id: str) -> list:
        """ Returns all the tracks (IDs) in the given playlist. """
        results = self.sp.playlist_tracks(playlist_id)
        tracks = []

        def nested():
            tracks.extend([t['track']['id'] for t in results['items']])

        nested()
        while results['next']:
            results = self.sp.next(results)
            nested()

        return tracks

    def get_playlist_track_details(self, playlist_id: str) -> dict[str, tuple[int, str]]:
        """ Given a playlist ID, returns a list of all of the tracks in that playlist with their respective info. """
        pass
        """results = self.sp.playlist_tracks(playlist_id)
        tracks = {}

        def nested():
            for t in results['items']:
                try:
                    tracks[t['track']['id']] = (int(['track']['album']['release_date'][:4]), t['track']['artists'][0]['id'])
                except SyntaxWarning:
                    print(t)"""

        nested()
        while results['next']:
            results = self.sp.next(results)
            nested()

        return tracks

    def get_playlist_artists(self, playlist_id: str) -> set[str]:
        """ Given a playlist ID, returns a list of names for all of the artists in that playlist. """
        results = self.sp.playlist_tracks(playlist_id)
        artists = set()

        def nested():
            artists.update(set(t['track']['artists'][0]['id'] for t in results['items']))

        nested()
        while results['next']:
            results = self.sp.next(results)
            nested()

        return artists

    def get_playlist_track_names(self, playlist_id: str) -> list:
        """ Given a playlist ID, returns a list of names for all of the tracks in that playlist. """
        results = self.sp.playlist_tracks(playlist_id)
        tracks = []

        def nested():
            tracks.extend([t['track']['name'] for t in results['items']])

        nested()
        while results['next']:
            results = self.sp.next(results)
            nested()

        return tracks

    def get_playlist_tracks_dates(self, playlist_id: str) -> dict:
        """ Given a playlist ID, returns a dict of IDs with corresponding dates of when they were added to the playlist. """
        # FIXME: shorten that docstring maybe ^^

        results = self.sp.playlist_tracks(playlist_id)
        dates_added = {}

        def nested():
            for t in results['items']:
                dates_added[t['track']['id']] = self.utils.convert_from_isostring(t['added_at'])

        nested()
        while results['next']:
            results = self.sp.next(results)
            nested()

        return dates_added

    def get_unsaved_tracks(self, playlist_id: str) -> dict:
        """
        Finds out what songs in a playlist are not saved and returns a dict of track IDs and corresponding booleans.
        # FIXME: shorten that docstring maybe ^^

        Args:
            sp (otipy.Spotify): Spotify API client
            playlist_id (str): ID of playlist to check

        Returns:
            dict: Returns dict of track IDs and corresponding booleans::
                {
                    "2W47TKGp5G0a5plyWg3HXp": True,
                    "4pCvnGkf7jveRMKHZosxxB": True,
                    "66MGk6BwVMx5O1TJqDAX4Y": False,
                    ...
                }
        """
        playlist_tracks = self.get_playlist_tracks(playlist_id)
        if len(playlist_tracks) > GET_MAX:  # can only check 50 songs at a time
            tracks_exist = []
            tracks_chunks = self.utils.divide_chunks(playlist_tracks, GET_MAX)  # generator
            for chunk in tracks_chunks:
                tracks_exist.extend(self.sp.current_user_saved_tracks_contains(chunk))  # checks if these tracks are saved
        else:
            # list of booleans representing whether each track is saved or not
            tracks_exist = self.sp.current_user_saved_tracks_contains(playlist_tracks)

        # creates dict by zipping 2 lists together into key-value pairs
        resultant = dict(zip(playlist_tracks, tracks_exist))  # B)

        return resultant
