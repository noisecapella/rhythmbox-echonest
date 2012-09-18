from gi.repository import GObject, RB, Peas, Gtk, GLib, Gio, GConf
GCONF_PREFIX = '/apps/rhythmbox/plugins/echonest-recommender'

class GtkPersistence:
    def __init__(self, gconf):
        self.gconf = gconf
        
    def apply_persistence(self, obj, callback_data=None):
        """Iterates through GTK objects. For applicable Gtk object types,
        loads persisted data and sets state for that object,
        then sets callback to record any change to object"""
        if isinstance(obj, Gtk.Container):
            obj.foreach(self.apply_persistence, None)
        elif isinstance(obj, Gtk.Entry):
            value = self.gconf.get_string(GCONF_PREFIX + "/" + obj.get_name())
            if value:
                obj.set_text(value)
            obj.connect('changed', self.save_state_entry)
        elif isinstance(obj, Gtk.Range):
            value = self.gconf.get_float(GCONF_PREFIX + "/" + obj.get_name())
            if value:
                obj.set_value(value)
            obj.connect('value-changed', self.save_state_range)
        elif isinstance(obj, Gtk.ToggleButton):
            value = self.gconf.get_bool(GCONF_PREFIX + "/" + obj.get_name())
            if value:
                obj.set_active(value)
            obj.connect('toggled', self.save_state_togglebutton)


    def save_state_entry(self, widget, callback_data=None):
        self.gconf.set_string(GCONF_PREFIX + "/" + widget.get_name(), widget.get_text())
    def save_state_range(self, widget, callback_data=None):
        self.gconf.set_float(GCONF_PREFIX + "/" + widget.get_name(), widget.get_value())
    def save_state_togglebutton(self, widget, callback_data=None):
        self.gconf.set_bool(GCONF_PREFIX + "/" + widget.get_name(), widget.get_active())
