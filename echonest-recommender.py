from gi.repository import GObject, RB, Peas
class EchonestRecommenderPlugin (GObject.Object, Peas.Activatable):
    __gtype_name__ = 'echonest-recommender'
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        GObject.GObject.__init__(self)

    def do_activate(self):
        shell = self.object
        print "Hello, world"

    def do_deactivate(self):
        del self.string
