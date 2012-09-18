import os
from gi.repository import GObject, RB, Peas, Gtk, GLib, Gio, GConf, Gdk, GdkPixbuf
import json
import urllib, urllib2
from gtk_persistence import GtkPersistence

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
        self.similar_artists_map = {}

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

    def set_entry(self, entry):
        if entry == self.current_entry or not entry:
            return

        self.current_entry = entry

        title = unicode(entry.get_string(RB.RhythmDBPropType.TITLE ), 'utf-8')
        artist = unicode(entry.get_string(RB.RhythmDBPropType.ARTIST ), 'utf-8')
        self.get_similar_artists(artist)

    def sanitize(self, s):
        return s.lower().replace(" ", "").replace("'", "")

    def populate_similar_artists(self, first_artist, url):
        first_artist_sanitized = self.sanitize(first_artist)

        self.qm = RB.RhythmDBQueryModel.new_empty(self.db)

        for row in self.object.props.library_source.props.base_query_model:
            entry = row[0]
            artist = entry.get_string(RB.RhythmDBPropType.ARTIST)
            if self.sanitize(artist) in self.similar_artists_map[url] or self.sanitize(artist) == first_artist_sanitized:
                self.qm.add_entry(entry, -1)
        
        self.echonest_source.props.query_model = self.qm
        self.echonest_source.get_entry_view().set_model(self.qm)

        
    def get_similar_artists(self, first_artist):
        url = "http://developer.echonest.com/api/v4/artist/similar?api_key={0}&name={1}&format=json&results=100&start=0&min_familiarity={2}&max_familiarity={3}".format(urllib.quote(self.echonest_source.apikey.get_text()), urllib.quote(first_artist.encode("utf8")), self.echonest_source.min_familiarity.get_value(), self.echonest_source.max_familiarity.get_value())
        
        if url not in self.similar_artists_map:
            response = urllib2.urlopen(url)
            raw_data = response.read()
            similar_artists_json = json.loads(raw_data)
            similar_artists = [each["name"].encode("utf8") for each in similar_artists_json["response"]["artists"]]
            m = {}
            for each in similar_artists:
                m[self.sanitize(each)] = each
            self.similar_artists_map[url] = m

        self.populate_similar_artists(first_artist, url)

    def find_file(self, filename):
        # from https://github.com/luqmana/rhythmbox-plugins/blob/master/equalizer/equalizer.py
	info = self.plugin_info
        data_dir = info.get_data_dir()
        path = os.path.join(data_dir, filename)

        if os.path.exists(path):
            return path

        return RB.file(filename)        

class EchoNestSource(RB.BrowserSource):
    def __init__(self):
        RB.BrowserSource.__init__(self, name=_("Echo's Nest Recommendations"))

    def initialize_ui(self, glade_file, gconf):
        top_grid = self.get_children()[0]

        shell = self.props.shell

        builder = Gtk.Builder()
        builder.add_from_file(glade_file)

        window = builder.get_object("box1")
        top_grid.insert_row(0)
        top_grid.attach(window, 0,0,1,1)
        self.show_all()
        
        self.min_familiarity = builder.get_object("min_familiarity")
        self.min_familiarity.set_range(0, 1)
        self.min_familiarity.set_increments(0.05, 0.05)
        self.min_familiarity.set_value(0)

        self.max_familiarity = builder.get_object("max_familiarity")
        self.max_familiarity.set_range(0, 1)
        self.max_familiarity.set_increments(0.05, 0.05)
        self.max_familiarity.set_value(1)

        self.apikey = builder.get_object("apikey_entry")
        self.unique_artist = builder.get_object("unique_artist")

        gtkPersistence = GtkPersistence(gconf)
        window.foreach(gtkPersistence.apply_persistence, None)




GObject.type_register(EchoNestSource)
