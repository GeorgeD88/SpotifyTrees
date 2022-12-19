# Spotify API
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Utils & Constants
from utils import Utils
from constants import *

from datetime import datetime


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
    def get_user_playlists(self) -> list[str]:
        """ Returns all the user's playlists (IDs). """
        results = self.sp.current_user_playlists()  # initial API call
        playlists = []

        # define nested function to extract all IDs from current page of results
        def nested():
            playlists.extend([plist['id'] for plist in results['items']])

        self.utils.page_all_results(nested, results)
        """ nested()  # extract from initial results
        while results['next']:  # page as long as there are more results
            results = self.sp.next(results)
            nested()  # extract IDs from paged results
 """
        return playlists

    def get_user_playlist_names(self) -> list[str]:
        """ Returns a list of names of all of the user's playlists. """
        results = self.sp.current_user_playlists()  # initial API call
        playlists = []

        # define nested function to extract all names from current page of results
        def nested():
            playlists.extend([plist['name'] for plist in results['items']])

        self.utils.page_all_results(nested, results)
        """ nested()  # extract from initial results
        while results['next']:  # page as long as there are more results
            results = self.sp.next(results)
            nested()  # extract names from paged results
 """
        return playlists

    def playlists_name_id_pair(self) -> dict[str: str]:
        """ Returns a dict of name ID pairs for all of the user's playlists. """
        results = self.sp.current_user_playlists()  # initial API call
        playlists = {}

        # define nested function to extract all names & IDs from current page of results
        def nested():
            for plist in results['items']:  # iterate every playlist in result
                if plist['name'] in playlists:  # checks if duplicate playlist name was found
                    prev = playlists[plist['name']]  # grabs existing playlist's ID
                    # present option to decide between both playlists to user
                    print(f"playlist \"{plist['name']}\" already exists with ID \"{prev}\" (P) yet same name was found with ID \"{plist['id']}\" (N)")
                    while True:
                        choice = input('input the playlist letter you would like to use: P/N').upper()
                        if choice == 'P':  # keep previous (existing) playlist ID: do nothing
                            break
                        elif choice == 'N':  # use the newly found playlist ID: replace ID
                            playlists[plist['name']] = plist['id']
                            break
                        else:
                            print('unknown input, use P or N')
                else:  # else simply add this new found playlist
                    playlists[plist['name']] = plist['id']

        self.utils.page_all_results(nested, results)
        """ nested()  # extract from initial results
        while results['next']:  # page as long as there are more results
            results = self.sp.next(results)
            nested()  # extract names & IDs from paged results
 """
        return playlists

    def playlists_id_name_pair(self) -> dict[str: str]:
        """ Returns a dict of ID name pairs for all of the user's playlists. """
        results = self.sp.current_user_playlists()  # initial API call
        playlists = {}

        # define nested function to extract all IDs & names from current page of results
        def nested():
            for plist in results['items']:
                if plist['id'] not in playlists:
                    playlists[plist['id']] = plist['name']

        self.utils.page_all_results(nested, results)
        """ nested()  # extract from initial results
        while results['next']:  # page as long as there are more results
            results = self.sp.next(results)
            nested()  # extract IDs & names from paged results
 """
        return playlists

    # === PLAYLIST CREATION/MANAGEMENT ===
    def new_playlist(self, playlist_name: str) -> str:
        """ Creates a new playlist with given name and returns the new playlist's ID. """
        return self.sp.user_playlist_create(self.my_id(), playlist_name)['id']

    def add_playlist_tracks(self, playlist_id: str, tracks: list):
        """ Adds the given tracks to the given playlist. """
        tracks_chunks = self.utils.divide_chunks(tracks, ADD_MAX)
        # adds the tracks in chunks due to API limit
        for chunk in tracks_chunks:
            self.sp.playlist_add_items(playlist_id, chunk)

    # === PLAYLIST CONTENTS ===
    def get_playlist_tracks(self, playlist_id: str) -> list[str]:
        """ Returns all the tracks (IDs) in the given playlist. """
        results = self.sp.playlist_tracks(playlist_id)  # initial API call
        tracks = []

        # define nested function to extract all IDs from current page of results
        def nested():
            tracks.extend([track['track']['id'] for track in results['items']])

        self.utils.page_all_results(nested, results)
        """ nested()  # extract from initial results
        while results['next']:  # page as long as there are more results
            results = self.sp.next(results)
            nested()  # extract IDs from paged results
 """
        return tracks

    def get_playlist_track_names(self, playlist_id: str) -> list[str]:
        """ Returns all the tracks (names) in the given playlist. """
        results = self.sp.playlist_tracks(playlist_id)  # initial API call
        tracks = []

        # define nested function to extract all names from current page of results
        def nested():
            tracks.extend([track['track']['name'] for track in results['items']])

        self.utils.page_all_results(nested, results)
        """ nested()  # extract from initial results
        while results['next']:  # page as long as there are more results
            results = self.sp.next(results)
            nested()  # extract names from paged results
 """
        return tracks

    def get_playlist_tracks_dates(self, playlist_id: str) -> dict[str: datetime]:
        """ Returns a dict of all the tracks in the given playlist and when they were added. """
        results = self.sp.playlist_tracks(playlist_id)  # initial API call
        dates_added = {}

        # define nested function to extract all IDs & dates from current page of results
        def nested():
            for track in results['items']:
                dates_added[track['track']['id']] = self.utils.convert_from_isostring(track['added_at'])

        self.utils.page_all_results(nested, results)
        """ nested()  # extract from initial results
        while results['next']:  # page as long as there are more results
            results = self.sp.next(results)
            nested()  # extract IDs & dates from paged results
 """
        return dates_added

    def get_playlist_artists(self, playlist_id: str) -> list[str]:
        """ Given a playlist ID, returns a list of names for all of the artists in that playlist. """
        results = self.sp.playlist_tracks(playlist_id)  # initial API call
        artists = set()  # use set because we just want unique names, no dupes

        # define nested function to extract all IDs from current page of results
        def nested():
            artists.update(set(t['track']['artists'][0]['id'] for t in results['items']))

        self.utils.page_all_results(nested, results)
        """ nested()  # extract from initial results
        while results['next']:  # page as long as there are more results
            results = self.sp.next(results)
            nested()  # extract IDs from paged results
 """
        return list(artists)

    # def get_unsaved_tracks(self, playlist_id: str) -> dict:
    #     """ Finds out what songs in a playlist are not saved and returns a dict of track IDs and corresponding booleans.
    #     # FIXME: shorten that docstring maybe ^^ """
    #     playlist_tracks = self.get_playlist_tracks(playlist_id)
    #     if len(playlist_tracks) > GET_MAX:  # can only check 50 songs at a time
    #         tracks_exist = []
    #         tracks_chunks = self.utils.divide_chunks(playlist_tracks, GET_MAX)  # generator
    #         for chunk in tracks_chunks:
    #             tracks_exist.extend(self.sp.current_user_saved_tracks_contains(chunk))  # checks if these tracks are saved
    #     else:
    #         # list of booleans representing whether each track is saved or not
    #         tracks_exist = self.sp.current_user_saved_tracks_contains(playlist_tracks)

    #     # creates dict by zipping 2 lists together into key-value pairs
    #     resultant = dict(zip(playlist_tracks, tracks_exist))  # B)

    #     return resultant
