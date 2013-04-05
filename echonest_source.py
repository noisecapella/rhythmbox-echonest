import os
from gi.repository import GObject, RB, Peas, Gtk, GLib, Gio, GConf, Gdk, GdkPixbuf
import json
import urllib, urllib2
from gtk_persistence import GtkPersistence
import random

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
        self.scale_artists = builder.get_object("scale_artists")
        gtkPersistence = GtkPersistence(gconf)
        window.foreach(gtkPersistence.apply_persistence, None)


