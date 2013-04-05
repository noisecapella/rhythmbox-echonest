def maybeInstallReactor():
    import sys
    try:
        from twisted.internet import gtk3reactor # s/2/3 if you're using gtk3
        reactor = gtk3reactor.install()
        reactor.startRunning()
        reactor._simulate()
        return reactor
    except:
        try:
            from twisted.internet import gtk2reactor
            reactor = gtk2reactor.install()
            reactor.startRunning()
            reactor._simulate()
            return reactor
        except:
            print "This plugin requires twisted to be installed"
            exit(-1)
    

reactor = maybeInstallReactor()

from sanitize import sanitize

import os
from gi.repository import GObject, RB, Peas, Gtk, GLib, Gio, GConf, Gdk, GdkPixbuf
import json
import urllib, urllib2
from gtk_persistence import GtkPersistence
import random

from twisted.web import client
from twisted.internet.defer import inlineCallbacks, returnValue

from similar_artists import SimilarArtists

class EchonestRecommenderPlugin (GObject.Object, Peas.Activatable):
    __gtype_name = 'echonest-recommender'
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        GObject.GObject.__init__(self)
        

    def do_activate(self):
        shell = self.object
        sp = shell.props.shell_player
        self.db = shell.get_property('db')
        self.qm = RB.RhythmDBQueryModel.new_empty(self.db)
        self.pec_id = sp.connect('playing-song-changed', self.playing_entry_changed)
        self.pc_id = sp.connect('playing-changed', self.playing_changed)
        self.sc_id = sp.connect('playing-source-changed', self.source_changed)
        self.current_entry = None

        self.entry_type = RB.RhythmDBEntryType()
        playlist_group = RB.DisplayPageGroup.get_by_id("playlists")
        self.echonest_source = GObject.new(EchoNestSource,
                                           entry_type = self.entry_type,
                                           shell = shell,
                                           pixbuf=None, 
                                           plugin=self)
        shell.register_entry_type_for_source(self.echonest_source, self.entry_type)
        shell.append_display_page(self.echonest_source, playlist_group)

        self.lookup_query_model = self.echonest_source.props.query_model
        
        glade_file = self.find_file("source.glade")
        gconf = GConf.Client.get_default()
        self.echonest_source.initialize_ui(glade_file, gconf)

        # a mapping of a url to similar artist data from that url.
        # similar artist data is a mapping of sanitized_artist -> artist
        self.similar_artists_obj = SimilarArtists()

        self.initialize_icon()

    def initialize_icon(self):
        what, width, height = Gtk.icon_size_lookup(Gtk.IconSize.LARGE_TOOLBAR)
        icon = GdkPixbuf.Pixbuf.new_from_file_at_size(self.find_file("icon.gif"), width, height)
        
        
        self.echonest_source.set_property("pixbuf", icon)

    def do_deactivate(self):
        shell = self.object
        self.db = None
        sp = shell.props.shell_player
        sp.disconnect(self.pec_id)
        sp.disconnect(self.pc_id)
        sp.disconnect(self.sc_id)
        

        self.echonest_source.delete_thyself()
        del self.echonest_source

    def playing_changed(self, sp, playing):
        self.set_entry(sp.get_playing_entry())

    def playing_entry_changed(self, sp, entry):
        self.set_entry(entry)

    def source_changed(self, sp, source):
        if not source:
            return

    def populate_query_model(self, first_artist, similar_artists):
        """Iterate through library and populate our playlist with similar artists"""
        first_artist_sanitized = sanitize(first_artist)

        self.qm = RB.RhythmDBQueryModel.new_empty(self.db)

        lst = []
        for row in self.object.props.library_source.props.base_query_model:
            entry = row[0]
            artist = unicode(entry.get_string(RB.RhythmDBPropType.ARTIST), 'utf-8')

            if sanitize(artist) == first_artist_sanitized:
                if self.echonest_source.unique_artist.get_active() == True:
                    # skip this artist
                    pass
                else:
                    lst.append(entry)
            elif sanitize(artist) in similar_artists:
                lst.append(entry)

        if self.echonest_source.scale_artists.get_active():
            lst = self.scale(lst)

        for entry in lst:
            self.qm.add_entry(entry, -1)
        
        self.echonest_source.props.query_model = self.qm
        self.echonest_source.get_entry_view().set_model(self.qm)

    def scale(self, lst):
        """Return a new lst which removes entries for each artist such that
        every artist has a similar number of tracks"""
        if not lst:
            return lst

        m = {}
        for entry in lst:
            artist = unicode(entry.get_string(RB.RhythmDBPropType.ARTIST), 'utf-8')
            sanitized_artist = sanitize(artist)
            if sanitized_artist not in m:
                m[sanitized_artist] = []
            m[sanitized_artist].append(entry)

        # calculate average number of songs per artist, with a minimum of 1
        avg_songs = max(1, int(float(len(lst)) / len(m.keys())))
        
        ret = []
        for sanitized_artist, sub_lst in m.iteritems():
            for i in xrange(avg_songs):
                index = int(random.random()*len(sub_lst))
                ret.append(sub_lst[index])
        return ret
        

    def set_entry(self, entry):
        """This is called whenever the current song changes"""
        if entry == self.current_entry or not entry:
            return

        self.current_entry = entry

        title = unicode(entry.get_string(RB.RhythmDBPropType.TITLE ), 'utf-8')
        artist = unicode(entry.get_string(RB.RhythmDBPropType.ARTIST ), 'utf-8')

        reactor.callLater(0, self.update_similar_artists, artist)

    @inlineCallbacks
    def update_similar_artists(self, artist):
        print "EXECUTING"
        url, similar_artists = yield self.similar_artists_obj.get_similar_artists(artist,
                                                                                  self.echonest_source.apikey.get_text(),
                                                                                  self.echonest_source.min_familiarity.get_value(),
                                                                                  self.echonest_source.max_familiarity.get_value())
        self.populate_query_model(artist, similar_artists)


    def find_file(self, filename):
        # from https://github.com/luqmana/rhythmbox-plugins/blob/master/equalizer/equalizer.py
	info = self.plugin_info
        data_dir = info.get_data_dir()
        path = os.path.join(data_dir, filename)

        if os.path.exists(path):
            return path

        return RB.file(filename)        


from echonest_source import EchoNestSource
GObject.type_register(EchoNestSource)
