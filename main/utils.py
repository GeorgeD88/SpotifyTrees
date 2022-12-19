# Spotify API
import spotipy

# Other
from datetime import datetime, timedelta
from copy import copy
import json


class Utils:

    def __init__(self, sp: spotipy.Spotify):
        self.sp = sp

    # === API/AUTH ===
    def generate_scope_string(self, list_of_scopes: list) -> str:
        """ Given a list of scopes, returns a string of all of them concatenated (for auth). """
        scope_string = ''
        for scp in list_of_scopes:
            scope_string += scp + ' '
        # print(scope_string := scope_string[:-1])
        return scope_string

    # === PAGE ALL RESULTS ===
    def page_all_results(self, nested_func, results: dict):
        """ Automatically pages through data from API call and runs given function on every result. """
        nested_func()
        while results['next']:
            results = self.sp.next(results)
            nested_func()

    def page_next_results(self, nested_func, results: dict):
        """ Automatically pages through data from API call and runs given function on every result, (w/o initial call). """
        while results['next']:
            results = self.sp.next(results)
            nested_func()

    # === JSON READ/WRITE ===
    def read_json(self, filename: str) -> dict:
        """ Given a filename (without .json), loads data from JSON file and returns it. """
        with open(filename + '.json', 'r') as in_file:
            data = json.load(in_file)
        return data

    def write_json(self, filename: str, data: dict, indent: int = 4):
        """ Given a filename (without .json) and dict, writes dict to JSON file. """
        with open(filename + '.json', 'w+') as out_file:
            json.dump(data, out_file, indent=indent)

    # === ISOSTRING STUFF ===
    def convert_from_isostring(self, isostring: str) -> datetime:
        """ Converts ISO string to datetime object. """
        # return datetime.strptime(isostring, "%Y-%m-%dT%H:%M:%SZ")
        return datetime.fromisoformat(isostring[:-1])  # ISO 8601

    def convert_to_isostring(self, datetime_obj: datetime) -> str:
        """ Converts datetime object to ISO string. """
        if datetime_obj.microsecond >= 500_000:  # rounds the milliseconds to the nearest second
            datetime_obj += timedelta(seconds=1)
        datetime_obj = datetime_obj.replace(microsecond=0)  # then trims off milliseconds

        return datetime.strftime(datetime_obj, "%Y-%m-%dT%H:%M:%SZ")

    # === LIST TOOLS ===
    def not_in(self, pulling_from: list, avoding: list) -> list:
        """ Returns a list without the items in the avoiding list. """
        return [item for item in pulling_from if item not in avoding]

    def extend_nodup(self, orig: list, new: list):
        """ Performs the list.extend() on the list itself (by reference) but avoids duplicates. """
        orig.extend(self.not_in(new, orig))

    def divide_chunks(self, track_list: list, n: int):
        """ Generator that given a list will yield chunks of size n. """
        for i in range(0, len(track_list), n):
            yield track_list[i:i + n]

    # === PLAYLIST NAME/ID CONVERSION ===
    def playlist_name_from_id(self, playlist_id: str) -> str:
        """ Given the playlist ID, returns the playlist name. """
        return self.sp.playlist(playlist_id)['name']

    def playlist_id_from_name(self, playlist_name: str) -> str:
        """ Given the playlist name, returns the playlist ID. """
        results = self.sp.current_user_playlists()  # gets all of user's playlists

        # Contiously traverses the playlists until the playlist whose names matches is found and returns its ID.
        for pl in results['items']:
            if pl['name'] == playlist_name:
                return pl['id']

        # can't use auto_results() because using return statement
        while results['next']:
            results = self.sp.next(results)
            for pl in results['items']:
                if pl['name'] == playlist_name:
                    return pl['id']

    # === ID EXTRACTION FROM LINK ===
    def extract_id_link(self, link: str) -> str:
        """ Extracts the ID from a Spotify link and returns the ID. """
        id_garble = link.split('/')[4]  # splits link at slashes and grabs the last bit (ID + query)
        return id_garble.split('?')[0]  # splits garble at ? and saves first part only (ID)

    def extract_many_id_link(self, links: list) -> list:
        """ Extracts the IDs from a list of spotify links and returns the IDs as a list. """
        extracted_ids = []
        for l in links:
            extracted_ids.append(self.extract_id_link(l))
        return extracted_ids

    # === ID TREE GENERATION ===
    def gen_id_tree(self, name_tree: dict, name_id_pairs: dict, id_tree_file: str):
        """ Runs function to generate ID tree and then writes it to JSON file. """
        self.rec_gen_id(name_tree, name_id_pairs)
        self.write_json(id_tree_file + '_ids', name_tree)

    def rec_gen_id(self, name_tree: dict, name_id_pairs: dict):
        """ Recurses through tree of playlist names and converts each name into an ID. """
        for subplaylist in name_tree.values():
            if type(subplaylist) is dict:
                self.rec_gen_id(subplaylist, name_id_pairs)
            elif subplaylist is None:
                pass  # the key would've already been converted
            else:
                raise TypeError(
                    'expected dict, list, or None, got: ' + str(subplaylist))

        for playlist in copy(list(name_tree.keys())):
            # add key with new ID but same value
            name_tree[name_id_pairs[playlist]] = name_tree[playlist]
            # pop the old pair with the key still being the name instead of the ID
            name_tree.pop(playlist)

    # === ID TREE REVERSAL === (for checking if ID tree is right)
    def reverse_id_tree(self, id_tree: dict, id_tree_file: str):
        """ Runs function to reverse ID tree and then writes it to JSON file. """
        self.reverse_gen_id(id_tree)
        self.write_json(id_tree_file + '_reverse', id_tree)

    def reverse_gen_id(self, id_tree: dict):
        """ Recurses through tree of playlist IDs and converts each ID back into a name. """
        for subplaylist in id_tree.values():
            if type(subplaylist) is dict:
                self.reverse_gen_id(subplaylist)
            elif subplaylist is None:
                pass  # the key would've already been converted
            else:
                raise TypeError('expected dict, list, or None, got: ' + str(subplaylist))

        for playlist in copy(list(id_tree.keys())):
            # add key with new name but same value
            id_tree[self.playlist_name_from_id(playlist)] = id_tree[playlist]
            # pop the old pair with the key still being the ID instead of the name
            id_tree.pop(playlist)

    # === MISCELLANEOUS ===
    def print_track_names(self, tracks: list):
        """ Given a list of track IDs, prints each track name. """
        for tr in tracks:
            print(self.sp.track(tr)['name'])

    def filter_null(self, cleaning: list):
        """ Removes all None objects from a list. """
        cleaned = []
        # adds every non-Null item to new list
        for elem in cleaning:
            if elem is not None:
                cleaned.append(elem)
        # sets original list reference to cleaned list
        cleaning = cleaned
