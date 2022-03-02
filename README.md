# SpotifyTrees
**SpotifyTrees** is a tool written in Python that leverages the Spotify API to help people with huge intricate Spotify libraries manage their playlists; specifically tree systems of playlists containing related genres and subgenres. The point of **SpotifyTrees** is to make it easier to organize songs that apply to multiple subgenres so that you just have to add it once and the program will do the rest of the work for you.
_This is for a somewhat niche audience as not many people over-complicate their Spotify libraries like me._
Towards the right is a diagram I made to visualize the structure of my playlist tree for only EDM subgenres. As you can see it's quite complicated and you can see how something like **SpotifyTrees** becomes extremely useful in keeping up with it.<br><br>
<img align="right" src="https://github.com/GeorgeD88/SpotifyTrees/blob/main/edm_genre_map.png" alt="Genre Map" width="400">
## License
**SpotifyTrees** is free software, distributed under the terms of the [GNU General Public License, version 3](https://www.gnu.org/licenses/gpl-3.0.html).
## What I Learned
* Spotify API and Spotipy wrapper
* Remote development over SSH
* Tree traversal algorithms
* Compartmentalizing code
* Lots of debugging and developing algorithms
## How it Works
The way it works is you define a tree of playlists in `ex_genre_tree.json` in a way that the songs in every child node/playlist will be added to its root playlist. For example, you might have a few different Metal playlists such as Heavy Metal, Death Metal, Black Metal, etc. and you want them all to be combined in a universal Metal playlist.<br>
You would define this as:
```json
{
    "Metal" {
        "Heavy Metal": null,
        "Death Metal": null,
        "Black Metal": null
    }
}
```
Notice that if a playlist doesn't have any children playlists (leaf nodes), then we pair it with `null`.
_Note that your tree would usually be a lot more complicated._
## How to Run
Before touching any files, you need to trim `ex_` from any of the file names that start with it. The `ex_` is there to differentiate the repo versions of the files from my personal versions, as these files contain personalized or sensitive data.<br>
Once you remove the `ex_` from the file names, it's time to fill out each file with the necessary data; which is explained below.<br>
### creds.py
This file stores the credentials for our Spotify API. You can create a Spotify app on your [Spotify developer dashboard](https://developer.spotify.com/dashboard/applications) if you haven't already created it. Once you've created your Spotify app, copy the client ID and client secret from the app page to the appropriate variables in the file, as well as add a redirect URI.
### genre_tree.json
This file stores the tree of playlist names that describe the way your playlists relate to each other. Remember that the songs from every child playlist/subtree get added to the parent playlists, so make sure you don't mess up the order and fill up the wrong playlists. Below is a simple example:
```json
{
    "root playlist": {
        "playlist": {
            "leaf playlist": null
        }
    }
}
```
_IMPORTANT: make sure you don't have any playlists in your library with the same name as any of the playlists you enter in this file, as the program might grab the ID for a different playlist than you had intended and add to that instead._
### time_checked.json
This file is very important as it stores the time the program was last run. This is so that every time you rerun the program, it only updates newly added songs. The file already contains the date 1/1/2000 to make it check every song in your tree since before their playlist creation date (because it's the first run so we want make sure everything is in place). So no need to touch anything in this file as it's all set up. _Unless any of the playlists in the tree that you want checked have songs before that date, then you'll need to change the value to any day before the first song was added._
### quick_update.py
Finally we have the only file you'll have to care about after setup. This file is already written with all the function calls needed to update your playlist tree. For your first run, you'll have to uncomment the commented out line as it generates the tree of playlist IDs from the tree of playlist names file. You want to make sure the variable `tree_filename` (without the file extension) matches the name you have for you genre tree if you renamed it. After the first run of the file, the ID tree will be generated and you can comment that line back out. From then on, whenever you want to quickly update your playlist tree, all you have to do is simply run the file.