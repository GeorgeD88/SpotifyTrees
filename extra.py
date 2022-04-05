from datetime import datetime, timedelta
from datapipe import Datapipe
from myutils import MyUtils
from copy import copy
import spotipy


class Extra:

    def __init__(self, sp: spotipy.Spotify, utils: MyUtils) -> None:
        self.sp = sp
        self.utils = utils

# ⚠️ BUILD IN PROGRESS 🔨⚠️
    def identify_genres(self, links: list) -> dict:
        """
        Takes a list of track IDs and returns a dict of each track's lowest playlist locations; thereby finding its genre.

        Args:
            sp (spotipy.Spotify): Spotify API client
            links (list): List of track IDs to identify.

        Returns:
            dict: Returns a dict containing track IDs and a list of their corresponding playlist locations as values::
                {
                    "0U0ldCRmgCqhVvD6ksG63j": [NOTE: PLAYLIST IDDDasdhjasdjaois oiasjdoiahjsdiasd],
                    "0Vj2je2PLl1TU78DAMArat": [NOTE: PLAYLIST IDDDasdhjasdjaois oiasjdoiahjsdiasd]
                }
        """
        extracted_ids = self.utils.extract_many_id_link(links)
        id_locations = {}

        # TODO: recurses through playlist tree to bottom and check if any tracks in there
        # NOTE: whenever a song is found remove it from the searching list because that would be the lowest

        return id_locations

# ⚠️ BUILD IN PROGRESS 🔨⚠️
    def remove_from_tree(self, nodes: dict, track_id: str):
        """
        Recurses through tree and removes given track at every occurrence.

        Args:
            sp (spotipy.Spotify): Spotify API client
            nodes (dict): Subtree of playlist ID nodes and their children
            track_id (str): ID of the track to be removed
        """
        # NOTE: use below function to find all locations of the song first then remove them
        self.utils.pinpoint_song_in_tree()  # in myutils

    def album_cover(self, album_id: str) -> dict:
        """ Given album ID, returns dict containing links to the album's cover in 3 resolutions. """
        covers = self.sp.album(album_id)['images']
        images = {}
        for img in covers:
            images[img['height']] = img['url']  # defines new key with image height as key and link as the value
        return images

    def get_artist_link(self, search_artist: str) -> str:
        """ Gets artist link from given search query. """
        results = self.sp.search(q='artist:' + search_artist, type='artist', limit=1)
        return results['artists']['items'][0]['external_urls']['spotify']

# ⚠️ FUTURE BUILD 🔨⚠️
    # NOTE: DOPE IDEA TO GET ALL SONGS FROM ARTIST PAGE
    def pull_artist_releases(self, artist_id):
        """ Given an artist, returns a list of all the track from their artists page. """
        pass

    def print_locations(self, locations):
        """ Prints the names of the track IDs and their playlist locations. """
        for track, spots in locations.items():
            print(f"{self.sp.track(track)['name']}:\n=========================")
            for s in spots:
                print(f'  - {self.utils.playlist_name_from_id(s)}')
            print()

    # ===== TOP HEAVY =====
    def convert_count_topheavy(self, topheavy_info: dict, id_name_pairs: dict):
        """
        Calls the functions to convert topheavy info to names and count the missing tracks of each playlist.

        Args:
            sp (spotipy.Spotify): Spotify API client
            topheavy_info (dict): Topheavy info to convert
            id_name_pairs (dict): Dict of ID name pairs to convert IDs
        """
        self.ids2names_topheavy(topheavy_info, id_name_pairs)
        self.count_topheavy(topheavy_info)

    def ids2names_topheavy(self, topheavy_info: dict, id_name_pairs: dict):
        """
        Goes through the dict of topheavy info and converts the playlist & track IDs to names.

        Args:
            sp (spotipy.Spotify): Spotify API client
            topheavy_info (dict): Topheavy info to convert
            id_name_pairs (dict): Dict of ID name pairs to convert IDs
        """
        for subplaylist in topheavy_info.values():
            if type(subplaylist['child playlists']) is dict:
                self.ids2names_topheavy(subplaylist['child playlists'], id_name_pairs)
            elif subplaylist['child playlists'] is None:
                pass  # the key would've already been converted
            else:
                raise TypeError(
                    'expected dict, list, or None, got: ' + str(subplaylist['child playlists']))

        for playlist in copy(list(topheavy_info.keys())):
            # add key with new ID but same value
            new_key = id_name_pairs[playlist]
            topheavy_info[new_key] = topheavy_info[playlist]
            # pop the old pair with the key still being the name instead of ID
            topheavy_info.pop(playlist)

            ll_ink = topheavy_info[new_key]['missing tracks']
            if ll_ink is not None:
                for i in range(len(ll_ink)):
                    t_id = ll_ink[i]
                    ll_ink[i] = self.sp.track(t_id)['name']

    def count_topheavy(self, topheavy_info: dict):
        """ Goes through the dict of topheavy missing tracks and prints the number of missing tracks for each playlist. """
        for subplaylist in topheavy_info.values():
            if type(subplaylist['child playlists']) is dict:
                self.utils.count_topheavy(subplaylist['child playlists'])
            elif subplaylist['child playlists'] is None:
                pass  # the key would've already been converted
            else:
                raise TypeError(
                    'expected dict, list, or None, got: ' + str(subplaylist['child playlists']))

        for playlist in copy(list(topheavy_info.keys())):
            if topheavy_info[playlist]['missing tracks'] is not None:
                print(f'{playlist} has {len(topheavy_info[playlist]["missing tracks"])} songs')

    # ===== LINK SHARE =====
    def rolling_link_share(self, filename: str):
        """
        Takes a list of Spotify links through user input then prints
            each song's name & artist and writes it to a text file.

        Args:
            sp (spotipy.Spotify): Spotify API client
            filename (str): The filename of the text file to write to
        """
        rolling_ids = []
        buffer = input().strip()  # NOTE: MAKE THE ROLLING INPUT ITS OWN FUNCTION
        # while loop to accept links through user input
        while buffer != '':
            rolling_ids.append(self.utils.extract_id_link(buffer))
            buffer = input().strip()

        # building string block to print and write to file
        export = ''
        for t_id in rolling_ids:
            track_details = self.sp.track(t_id)
            artists = track_details['artists']
            recommendation = f"{track_details['name']} by {', '.join(art['name'] for art in artists)}"
            export += f'{recommendation}\n- \n\n'
        print(export := export[:-2])

        with open(filename + '.txt', 'w+') as out_file:
            out_file.write(export)

    def share_links(self, links: list):
        """ Takes a list of Spotify links and prints each song's name & artist. """
        extracted_ids = self.utils.extract_many_id_link(links)
        for t_id in extracted_ids:
            track_details = self.sp.track(t_id)
            artists = track_details['artists']
            print(f"{track_details['name']} by {', '.join(art['name'] for art in artists)}")
