from datapipe import Datapipe
from datetime import datetime
from extra import Extra
from orgo import Orgo
from creds import *
import spotipy


REGIONS = "rap_artists_regions"
SUBSUBS = "rap_subsubs"


class Rap(Orgo):

    def __init__(self):
        super().__init__()

    def pull_artists_from_regions(self):
        """ Pulls all the artists from the region playlists. """

        regions = self.utils.read_json(REGIONS)
        regions_artists = {}

        for plist in regions.keys():
            regions_artists[plist] = list(self.datapipe.get_playlist_artists(plist))

        self.utils.write_json(REGIONS, regions_artists)

rap = Rap()
rap_plist = "6oUhr2yEXhOvPprCNRjs03"
# rap.get_playlist_track_details(rap_plist)
rap.pull_artists_from_regions()
