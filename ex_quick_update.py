from orgo import Orgo

orgo = Orgo()
tree_filename = 'TREE_FILENAME'
# orgo.utils.gen_id_tree(orgo.utils.read_json(tree_filename), orgo.datapipe.playlists_name_id_pair(), tree_filename)
tree_ids = orgo.utils.read_json(tree_filename + '_ids')
orgo.update_playlist_tree(tree_ids)
