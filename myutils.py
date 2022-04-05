from datetime import datetime, timedelta
from copy import copy
import spotipy
import json


class MyUtils:

    def __init__(self, sp: spotipy.Spotify) -> None:
        self.sp = sp

    def generate_scope_string(self, list_of_scopes: list) -> str:
        """ Given list of scopes, returns a string of all of them concatenated together for auth purposes. """
        scope_string = ''
        for scp in list_of_scopes:
            scope_string += scp + ' '
        print(scope_string := scope_string[:-1])
        return scope_string

    def print_track_names(self, tracks: list):
        """ Given a list of track IDs, prints each track name. """
        for tr in tracks:
            print(self.sp.track(tr)['name'])

    def filter_null(self, cleaning: list):
        """ Removes all None objects from a list. """
        try:
            while True:
                cleaning.remove(None)  # removes None
        except ValueError:
            return

    # ===== AUTO RESULTS =====
    def auto_results(self, nest_func, results: dict):
        """ Automatically pages through data from API call. """
        nest_func()

        while results['next']:
            results = self.sp.next(results)
            nest_func()

    def auto_results_lite(self, nest_func, results: dict):
        """ Automatically pages through data from API call, w/o initial call & only does paging part. """
        while results['next']:
            results = self.sp.next(results)
            nest_func()

    # ===== JSON READ/WRITE =====
    def read_json(self, filename: str) -> dict:
        """ Given a filename (without .json), loads data from JSON file and returns it. """
        with open(filename + '.json', 'r') as in_file:
            data = json.load(in_file)

        return data

    def write_json(self, filename: str, data: dict, indent: int = 4):
        """ Given a filename (without .json) and dict, writes dict to JSON file. """
        with open(filename + '.json', 'w+') as out_file:
            json.dump(data, out_file, indent=indent)

    # ===== ISOSTRING STUFF =====
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

    # ===== TIME RECORDING =====
    def get_time_checked(self, filename: str = 'time_checked') -> datetime:
        """ Returns the time checked from the JSON file. """
        time_string = self.read_json(filename)[filename]
        return self.convert_from_isostring(time_string)

    def record_time_checked(self, time_checked: datetime, filename: str = 'time_checked'):
        """ Records the time checked into the JSON file. """
        time_string = self.convert_to_isostring(time_checked)
        self.write_json(filename, {filename: time_string})

    # ===== LIST TOOLS =====
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

    # ===== PLAYLIST NAME/ID CONVERSION =====
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

    # ===== ID EXTRACTION FROM LINK =====
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

    # ===== ID TREE GENERATION =====
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

    # ===== ID TREE REVERSAL ===== (for checking if ID tree is right)
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

# ===== TREE TRAVERSAL =====
"""
NOTE: This would be a big refactoring task but
I think I should try to make a tree traversal function
that can stand on its own and then call it wherever
there is need to traverse a tree.
FIXME: The challenge that comes to mind is that most of these
functions using traversal need to do stuff within the traversal
(hence during the function call) which isn't really possible (I think).
"""
