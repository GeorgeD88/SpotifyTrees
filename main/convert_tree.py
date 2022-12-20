from datapipe import Datapipe
from constants import *
from utils import Utils
from creds import *
import pprint

""" Script to convert Spotify tree of names into tree of IDs. """

if __name__ == "__main__":
    dp = Datapipe(CLIENT_ID, CLIENT_SECRET, SPOTIPY_REDIRECT_URI, SCOPES)
    sp = dp.sp
    ut = Utils(dp.sp)
    pp = pprint.PrettyPrinter().pprint

    name_tree_filename = "edm_tree222"  # TODO: FILL HERE

    # === Convert name tree to ID tree ===
    # print('loading name tree from json...')
    # name_tree = ut.read_json(name_tree_filename)  # load name tree
    # print('generating playlist name-ID pairs...')
    # name_id_pairs = dp.playlists_name_id_pair()  # generate playlist name-ID pairs
    # print('generating playlist ID tree...')
    # ut.convert_name_tree(name_tree, name_id_pairs, name_tree_filename + '222')

    # === Convert ID tree to link tree ===
    print('loading ID tree from json...')
    name_tree = ut.read_json(name_tree_filename + '_ids')  # load name tree
    print('generating playlist link tree...')
    ut.convert_link_tree(name_tree, name_tree_filename)
