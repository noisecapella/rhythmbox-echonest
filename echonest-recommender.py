import os
from gi.repository import GObject, RB, Peas, Gtk, GLib, Gio, GConf
import json
import urllib, urllib2

GCONF_PREFIX = '/apps/rhythmbox/plugins/echonest-recommender'
GCONF_MIN_FAMILIARITY = "min-familiarity"
GCONF_MAX_FAMILIARITY = "max-familiarity"
GCONF_APIKEY = "apikey"
GCONF_UNIQUE_ARTIST = "unique-artist"

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

        self.similar_artists_map = {}

        

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

    def populate_similar_artists(self, first_artist):
        first_artist_sanitized = self.sanitize(first_artist)

        self.qm = RB.RhythmDBQueryModel.new_empty(self.db)

        for row in self.object.props.library_source.props.base_query_model:
            entry = row[0]
            artist = entry.get_string(RB.RhythmDBPropType.ARTIST)
            if self.sanitize(artist) in self.similar_artists_map[first_artist_sanitized] or self.sanitize(artist) == first_artist_sanitized:
                self.qm.add_entry(entry, -1)
        
        self.echonest_source.props.query_model = self.qm
        self.echonest_source.get_entry_view().set_model(self.qm)

        
    def get_similar_artists(self, first_artist):
        url = "http://developer.echonest.com/api/v4/artist/similar?api_key={0}&name={1}&format=json&results=100&start=0".format(this.echonest_source.apikey, urllib.quote(first_artist.encode("utf8")))
        
        first_artist_sanitized = self.sanitize(first_artist)
        if first_artist_sanitized not in self.similar_artists_map:
            response = urllib2.urlopen(url)
            raw_data = response.read()
            similar_artists_json = json.loads(raw_data)
            similar_artists = [each["name"].encode("utf8") for each in similar_artists_json["response"]["artists"]]
            m = {}
            for each in similar_artists:
                m[self.sanitize(each)] = each
            self.similar_artists_map[first_artist_sanitized] = m

        self.populate_similar_artists(first_artist)

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

    def save_state(self, widget, callback_data=None):
        #TODO: save only one widget's information
        self.gconf.set_float(GCONF_PREFIX + "/" + GCONF_MIN_FAMILIARITY, self.min_familiarity.get_value())
        self.gconf.set_float(GCONF_PREFIX + "/" + GCONF_MAX_FAMILIARITY, self.max_familiarity.get_value())
        self.gconf.set_bool(GCONF_PREFIX + "/" + GCONF_UNIQUE_ARTIST, self.unique_artist.get_active())
        self.gconf.set_string(GCONF_PREFIX + "/" + GCONF_APIKEY, self.apikey.get_text())
        

    def initialize_ui(self, glade_file, gconf):
        top_grid = self.get_children()[0]

        shell = self.props.shell
        self.gconf = gconf

        builder = Gtk.Builder()
        builder.add_from_file(glade_file)

        window = builder.get_object("box1")
        top_grid.insert_row(0)
        top_grid.attach(window, 0,0,1,1)
        self.show_all()

        self.min_familiarity = builder.get_object("min_familiarity")
        self.min_familiarity.set_range(0, 1)
        self.min_familiarity.set_value(0.5)
        self.max_familiarity = builder.get_object("max_familiarity")
        self.max_familiarity.set_range(0, 1)
        self.max_familiarity.set_value(0.25)
        self.unique_artist = builder.get_object("unique_artist")
        self.apikey = builder.get_object("apikey_entry")
        
        apikey_value = gconf.get_string(GCONF_PREFIX + "/" + GCONF_APIKEY)
        if apikey_value:
            self.apikey.set_text(apikey_value)
        self.apikey.connect('changed', self.save_state)

        min_familiarity_value = gconf.get_float(GCONF_PREFIX + "/" + GCONF_MIN_FAMILIARITY)
        if min_familiarity_value:
            self.min_familiarity.set_value(min_familiarity_value)
        self.min_familiarity.connect('change-value', self.save_state)

        max_familiarity_value = gconf.get_float(GCONF_PREFIX + "/" + GCONF_MAX_FAMILIARITY)
        if max_familiarity_value:
            self.max_familiarity.set_value(max_familiarity_value)
        self.max_familiarity.connect('change-value', self.save_state)

        unique_artist_value = gconf.get_bool(GCONF_PREFIX + "/" + GCONF_UNIQUE_ARTIST)
        if unique_artist_value:
            self.unique_artist.set_active(unique_artist_value)
        self.unique_artist.connect('toggled', self.save_state)



GObject.type_register(EchoNestSource)
