# SpotifyTrees
**SpotifyTrees** is a tool written in Python that helps people with huge intricate Spotify libraries manage their playlists; specifically tree systems of playlists containing related genres and subgenres. The point of **SpotifyTrees** is to make it easier to organize songs that apply to multiple subgenres so that you just have to add it once and the program will do the rest of the work for you.<br>
_This is for a somewhat niche aaudience as not many people over-complicte their Spotify libraries like me._
## How it Works
The way it works is you define a tree of playlists in `ex_genre_tree.json` in a way that the songs in every child node/playlist will be added to its root playlist. For example you might have a few different metal playlists such as Heavy Metal, Death Metal, Black Metal, etc. and you want them all to add to a universal Metal playlist.<br>
You would define this as:<br>
```json
{
    "Metal" {
        "Death Metal": null,
        "Heavy Metal": null,
        "Black Metal": null
    }
}
```
Notice we had each of the child playlists pair with `null`, that's because if a playlist doesn't have any children (leaf node) then we pair it with `null`.
## How to Run