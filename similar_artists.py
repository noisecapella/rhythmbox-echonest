from twisted.internet.defer import inlineCallbacks, returnValue
import os
from gi.repository import GObject, RB, Peas, Gtk, GLib, Gio, GConf, Gdk, GdkPixbuf
import json
import urllib, urllib2
from gtk_persistence import GtkPersistence
import random

from twisted.web import client

from sanitize import sanitize

class SimilarArtists:
    def __init__(self):
        self.similar_artists_map = {}

    @inlineCallbacks
    def get_similar_artists(self, first_artist, apikey, min_familiarity, max_familiarity):
        """Obtain similar artists, either from cache or from internet. Then call populate_artists with results"""
        url = "http://developer.echonest.com/api/v4/artist/similar?api_key={0}&name={1}&format=json&results=100&start=0&min_familiarity={2}&max_familiarity={3}"
        formatted_url = url.format(urllib.quote(apikey),
                                   urllib.quote(first_artist.encode("utf8")),
                                   min_familiarity,
                                   max_familiarity)

        if formatted_url not in self.similar_artists_map:
            raw_data = yield client.getPage(formatted_url)
            similar_artists_json = json.loads(raw_data)
            response = similar_artists_json["response"]
            if "artists" in response:
                similar_artists = [each["name"].encode("utf8") for each in response["artists"]]
            else:
                print "Warning: artist '%s' not found" % first_artist
                similar_artists = []
            m = {}
            for each in similar_artists:
                m[sanitize(each)] = each
            self.similar_artists_map[formatted_url] = m

        returnValue((formatted_url, self.similar_artists_map[formatted_url]))


@inlineCallbacks
def main():
    try:
        import sys
        if len(sys.argv) >= 2:
            artist = sys.argv[1]

        if len(sys.argv) == 4:
            minimum = float(sys.argv[2])
            maximum = float(sys.argv[3])
        else:
            minimum = 0.0
            maximum = 1.0

        similar_artists = SimilarArtists()
        url, results = yield similar_artists.get_similar_artists(artist, "6PRGK3W5TCN30FPI0", minimum, maximum)
        print sorted(results.values())
    finally:
        reactor.stop()
if __name__ == "__main__":
    from twisted.internet import reactor
    reactor.callLater(0, main)
    reactor.run()
