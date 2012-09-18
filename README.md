rhythmbox-echonest
==================

A [rhythmbox](http://projects.gnome.org/rhythmbox/) recommendation plugin using data from [the Echo's Nest](http://echonest.com).

Based heavily off [http://github.com/asermax/lastfm_queue](http://github.com/asermax/lastfm_queue).

(This plugin and I are not affiliated with Echo's Nest at all.)

Install
-------

For now, just cd to `~/.local/share/rhythmbox/plugins` and

    git clone https://github.com/bostonbusmap/rhythmbox-echonest.git echonest-recommender

(You may need to create the folder if it doesn't exist)

You also need an [Echo's Nest API key](http://developer.echonest.com). This should go in the API Key field in the playlist. This won't error if it's not there, I'll have to fix that eventually.

Usage
-----

This works best if you have a large-ish music collection. It creates a special source called Echo's Nest Recommendations (under Playlists on the bottom left of Rhythmbox.)

First, play something from your library. It will populate this playlist with every song by that artist and similar artists. Turn on shuffle for best results. The next song will come from this playlist, and then the playlist will refresh with new similar artists.


License and disclaimer
----------------------

I haven't figured this out yet, although it will be something open source.

Note that the Echo's Nest has their own license, available on their website. You have to agree to it to use this plugin. They also limit communication to 120 times an hour, which shouldn't normally be a problem but you might bump into this if you quickly switch between tracks.


TODO
----

- Some kind of escape button in case of too many similar artists.
- Error handling