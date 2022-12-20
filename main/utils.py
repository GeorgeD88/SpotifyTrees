# Spotify API
import spotipy

# Other
from datetime import datetime, timedelta
from collections.abc import Generator
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
        scope_string = scope_string[:-1]  # trims extra space
        return scope_string

    # === PAGE ALL RESULTS === FIXME: these don't work correctly for some reason, ask Samer about them
    # TODO: implement it where you also do the list definition and extending here, and only pass the inner list you make at each extension

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

    # === ID/NAME/etc. TREE GENERATION ===
    def convert_name_tree(self, name_tree: dict, name_id_pairs: dict, id_tree_file: str):
        """ Wrapper function that generates ID tree then writes it to a JSON file. """
        self.generate_id_tree_inplace(name_tree, name_id_pairs)
        self.write_json(id_tree_file + '_ids', name_tree)

    def generate_id_tree_inplace(self, sp_tree: dict, name_id_pairs: dict):
        """ Recurses through tree of playlist names and converts each name into an ID (converts inplace). """
        # post order traversal, because we recurse the children first then convert the roots
        for children in sp_tree.values():
            if isinstance(children, dict) is True:
                self.generate_id_tree_inplace(children, name_id_pairs)
            elif children is None:
                # TODO: figure out why this runs
                pass  # child doesn't exist/is a leaf
            else:
                raise TypeError('expected dict, list, or None, got: ' + str(children))

        # converts every playlist root in the forest from name to ID
        for playlist in copy(list(sp_tree.keys())):
            # adds same value with new key (ID) then deletes old key (name)
            new_key = name_id_pairs[playlist]  # get new key (ID)
            sp_tree[new_key] = sp_tree[playlist]  # add new
            sp_tree.pop(playlist)  # pop old

    def reverse_id_tree(self, id_tree: dict, id_tree_file: str):
        """ Runs function to reverse ID tree and then writes it to JSON file. """
        self.generate_name_tree_inplace(id_tree)
        self.write_json(id_tree_file + '_reverse', id_tree)

    def generate_name_tree_inplace(self, sp_tree: dict):
        """ Recurses through tree of playlist IDs and converts each ID back into a name.
        (for testing if the generate ID tree is correct) """
        for children in sp_tree.values():
            if type(children) is dict:
                self.generate_name_tree_inplace(children)
            elif children is None:
                pass  # the key would've already been converted
            else:
                raise TypeError('expected dict, list, or None, got: ' + str(children))

        # converts every playlist root in the forest from ID to name
        for playlist in copy(list(sp_tree.keys())):
            # adds same value with new key (name) then deletes old key (ID)
            new_key = self.playlist_name_from_id(playlist)  # gets new key (name)
            sp_tree[new_key] = sp_tree[playlist]  # add new
            sp_tree.pop(playlist)  # pop old

    def convert_link_tree(self, id_tree: dict, link_tree_file: str):
        """ Wrapper function that generates ID tree then writes it to a JSON file. """
        self.generate_link_tree_inplace(id_tree)
        self.write_json(link_tree_file + '_links', id_tree)

    def generate_link_tree_inplace(self, sp_tree: dict):
        """ Converts playlist IDs into links (converts inplace). """
        # post order traversal, because we recurse the children first then convert the roots
        for children in sp_tree.values():
            if isinstance(children, dict) is True:
                self.generate_link_tree_inplace(children)
            elif children is None:
                # TODO: test this, not exactly sure how this would work
                pass  # child doesn't exist/is a leaf
            else:
                raise TypeError('expected dict, list, or None, got: ' + str(children))

        # converts every playlist root in the forest from name to ID
        for playlist in copy(list(sp_tree.keys())):
            # adds same value with new key (ID) then deletes old key (name)
            new_key = self.build_playlist_url(playlist)  # build playlist URL
            sp_tree[new_key] = sp_tree[playlist]  # add new
            sp_tree.pop(playlist)  # pop old

    # === PLAYLIST NAME/ID CONVERSION ===
    def playlist_name_from_id(self, playlist_id: str) -> str:
        """ Given the playlist ID, returns the playlist name. """
        return self.sp.playlist(playlist_id)['name']

    def playlist_id_from_name(self, playlist_name: str) -> str:
        """ COSTLY!! Given the playlist name, returns the playlist ID. """
        results = self.sp.current_user_playlists()  # gets all of user's playlists

        # Continuously traverses the playlists until the playlist whose names matches is found and returns its ID.
        for pl in results['items']:
            if pl['name'] == playlist_name:
                return pl['id']

        # can't use auto_results() because using return statement
        while results['next']:
            results = self.sp.next(results)
            for pl in results['items']:
                if pl['name'] == playlist_name:
                    return pl['id']

        # if the name wasn't found during the traversal, then it wasn't found so return None
        return None

    # === LINK & ID CONVERSION ===
    def extract_id_link(self, link: str) -> str:
        """ Extracts the ID from a Spotify link and returns the ID. """
        id_garble = link.split('/')[4]  # splits link at slashes and grabs the last bit (ID + query)
        return id_garble.split('?')[0]  # splits garble at ? and returns first part only (ID)

    def extract_many_id_link(self, links: list[str]) -> list[str]:
        """ Extracts the IDs from a list of Spotify links. """
        extracted_ids = []
        for l in links:
            extracted_ids.append(self.extract_id_link(l))
        return extracted_ids

    def build_playlist_url(self, playlist_id: str) -> str:
        """ Builds Spotify playlist URL with given playlist ID. """
        return 'https://open.spotify.com/playlist/' + playlist_id

    # === JSON READ/WRITE ===
    def read_json(self, filename: str) -> dict:
        """ Given a filename (without .json), loads data from JSON file and returns it. """
        with open(filename + '.json', 'r') as in_file:
            data = json.load(in_file)
        return data

    def write_json(self, filename: str, data: dict, indent: int = 4):
        """ Given a filename (without .json) and dict, dumps dict to JSON file. """
        with open(filename + '.json', 'w+') as out_file:
            json.dump(data, out_file, indent=indent)

    # === ISOSTRING STUFF ===
    def convert_from_isostring(self, isostring: str) -> datetime:
        """ Converts ISO string to datetime object. """
        # return datetime.strptime(isostring, "%Y-%m-%dT%H:%M:%SZ")
        return datetime.fromisoformat(isostring[:-1])  # ISO 8601

    def convert_to_isostring(self, datetime_obj: datetime) -> str:
        """ Converts datetime object to ISO string. """
        # rounds the milliseconds to the nearest second
        if datetime_obj.microsecond >= 500000:
            datetime_obj += timedelta(seconds=1)
        datetime_obj = datetime_obj.replace(microsecond=0)  # then trims off milliseconds

        return datetime.strftime(datetime_obj, "%Y-%m-%dT%H:%M:%SZ")

    # === LIST TOOLS ===
    def filter_items(self, orig_list: list, to_filter: set) -> list:
        """ Returns a list without the items in the avoiding list (inplace). """
        def filter_func(item):
            return item not in to_filter
        return list(filter(filter_func, orig_list))

    def extend_nodupes(self, orig_list: list, extension: list):
        """ Performs the list.extend() on the list itself (by reference) but avoids duplicates. """
        orig_list.extend(self.filter_items(extension, orig_list))

    def divide_chunks(self, track_list: list, chunk_size: int) -> Generator[list]:
        """ Splits given list into chunks of given chunk size and yields them. """
        for i in range(0, len(track_list), chunk_size):
            yield track_list[i:i + chunk_size]

    # === MISCELLANEOUS ===
    def print_track_names(self, tracks: list):
        """ Given a list of track IDs, prints each track name. """
        for tr in tracks:
            print(self.sp.track(tr)['name'])

    def filter_null(self, cleaning: list) -> list:
        """ Removes all None values from the given list. """
        cleaned = [item for item in cleaning if item is not None]
        return cleaned
