

from gi.repository import GObject, RB, Peas, Gtk, GLib
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
        self.echonest_source = GObject.new(EchoNestSource, entry_type = self.entry_type, shell = shell, pixbuf=None, plugin=self)
        shell.register_entry_type_for_source(self.echonest_source, self.entry_type)
        shell.append_display_page(self.echonest_source, playlist_group)

        self.echonest_source.initialize()

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
        self.qm = RB.RhythmDBQueryModel.new_empty(self.db)

        self.qm.add_entry(self.current_entry, -1)

        self.echonest_source.props.query_model = self.qm
        self.echonest_source.get_entry_view().set_model(self.qm)
        

class EchoNestSource(RB.BrowserSource):
    def __init__(self):
        RB.BrowserSource.__init__(self, name=_("Echo's Nest Recommendations"))

    def initialize(self):
        top_grid = self.get_children()[0]

        shell = self.props.shell

        vbox = Gtk.VBox()
        vbox.set_homogeneous(False)
        top_grid.insert_row(0)
        top_grid.attach(vbox, 0,0,1,1)
        self.show_all()


GObject.type_register(EchoNestSource)
