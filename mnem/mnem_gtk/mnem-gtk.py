'''
Created on 26 Feb 2016

@author: John Beard
'''

from mnem_rest_client import client

import signal
import sys

from gi import require_version

require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GdkPixbuf
from gi.repository import GObject

from gi.repository import Pango

import webbrowser

import threading

class MnemEntryBoxModel(object):
    '''
    Class to represent the model for the entry box area of the UI
    '''

    def __init__(self, listener):
        self.entered = ''
        self.searchkey = ''
        self.listener = listener

    def setEntered(self, entered):
        self.entered = entered
        self.listener.changed()

class MnemEntryBox(object):
    '''
    UI for the entry box area
    '''

    def __init__(self, mainapp):
        self.mainapp = mainapp

        self.model = MnemEntryBoxModel(self)

        self.box = Gtk.VBox()

        self.main_input = Gtk.Entry()
        self.entry_change_sigid = self.main_input.connect(
            'changed', self.search_changed)

        self.box.pack_start(
            self.main_input, expand=True, fill=True, padding=0)

    def changed(self):
        '''
        Callback from the model on change
        '''
        print('changed')

    def get_entry_text(self):
        return self.main_input.get_text()

    def set_key_query(self, key, query):

        self.main_input.disconnect(self.entry_change_sigid)
        self.main_input.set_text("%s %s" % (key, query))
        self.entry_change_sigid = self.main_input.connect(
            'changed', self.search_changed)

        # self.main_input.set_position(-1)  # end
        self.main_input.select_region(-1, -1)

    def search_changed(self, entry):

        search = entry.get_text()

        self.mainapp.do_search(search)

class MnemResultListModel(object):

    NONE_SELECTED = -1

    def __init__(self, mainapp):
        self.listener = None
        self.mainapp = mainapp
        self.results = []

        self.reset()

    def reset(self):
        self.focussed = self.NONE_SELECTED

    def set_results(self, results):
        self.results = results
        self.listener.result_model_changed()

    def confirm_entry(self):

        try:
            self.perform_main_action(self.results[self.focussed])
        except IndexError:
            pass


    def perform_main_action(self, res):

        if res['url']:
            webbrowser.open(res['url'], new=2, autoraise=True)

    def select_next(self):

        old_foc = self.focussed

        self.focussed += 1

        if self.focussed >= len(self.results):
            self.focussed = 0

        self.listener.change_selected(old_foc, self.focussed)

    def select_prev(self):

        old_foc = self.focussed

        self.focussed -= 1

        # if no focus or last, go to the end
        if self.focussed < 0:
            self.focussed = len(self.results) - 1

        self.listener.change_selected(old_foc, self.focussed)

    def keyword_selected(self, keyword):
        '''
        Pass onto the main app
        '''
        self.mainapp.keyword_selected(keyword)


class ResultContainer(Gtk.HBox):

    def __init__(self, result, selected_listener):
        super(ResultContainer, self).__init__(
            name="result"
        )

        self.selected_listener = selected_listener
        self.set_homogeneous(False)

        try:
            self.url = result["url"]
        except KeyError:
            self.url = None

        self.keyword = result["keyword"]

        keyword = Gtk.Label(result["keyword"])
        keyword.set_justify(Gtk.Justification.LEFT)

        self.pack_start(keyword, expand=False, fill=True, padding=0)

        if self.url:
            urlLabel = Gtk.Label(self.url)
            urlLabel.set_justify(Gtk.Justification.LEFT)
            urlLabel.set_ellipsize(Pango.EllipsizeMode.MIDDLE)

            self.pack_end(urlLabel, expand=False, fill=True, padding=100)

        # self.set_can_focus(True)

        # self.connect("focus-in-event", self.on_focus)

    def select(self, selected):

        if selected:
            self.get_style_context().add_class(Gtk.STYLE_CLASS_HIGHLIGHT)
            self.selected_listener.keyword_selected(self.keyword)
        else:
            self.get_style_context().remove_class(Gtk.STYLE_CLASS_HIGHLIGHT)


class ResultListBox(object):

    def __init__(self, model):
        super(ResultListBox, self).__init__()

        self.model = model
        self.result_conts = []
        self.box = Gtk.VBox()
        self.box.show()

        self.model.listener = self

    def _clear(self):

        for r in self.result_conts:
            r.destroy()

        self.result_conts = []

    def result_model_changed(self):

        self._clear()

        for res in self.model.results:
            res_cont = ResultContainer(res, self.model)

            self.result_conts.append(res_cont)

            self.box.pack_start(res_cont, expand=False, fill=False, padding=0)

        self.box.show_all()

    def change_selected(self, old, new):

        try:
            self.result_conts[old].select(False)
        except IndexError:
            pass

        self.result_conts[new].select(True)


class MnemAppWindow(Gtk.Window):

    def __init__(self, client):
        super(MnemAppWindow, self).__init__(name="Mnem")

        self.client = client
        self.connect("destroy", self.stop)

        style_provider = Gtk.CssProvider()

        css = """
#result.selected{
    background-color: #77f;
}
"""

        style_provider.load_from_data(bytes(css.encode()))

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.create_layout()

        self.show_all()

        self.get_window().set_decorations(Gdk.WMDecoration.BORDER)

    def bind_signals(self):
        signal.signal(signal.SIGINT, self.signal_stop_received)  # 9
        signal.signal(signal.SIGTERM, self.signal_stop_received)  # 15

    def signal_stop_received(self, *args):
        self.stop()

    def signal_stop_received(self, *args):
        self.stop()

    def start(self):
        self.bind_signals()

        # https://bugzilla.gnome.org/show_bug.cgi?id=622084
        # so don't just use Gtk.main()
        try:
            GLib.MainLoop().run()
        except KeyboardInterrupt:
            pass

    def stop(self, *args):
        GLib.MainLoop().quit()
        sys.exit(0)

    def create_layout(self):

        self.main_box = Gtk.VBox()

        self.entry_box = MnemEntryBox(self)
        self.main_box.add(self.entry_box.box)

        self.result_model = MnemResultListModel(self)
        self.result_box = ResultListBox(self.result_model)
        self.main_box.add(self.result_box.box)

        self.add(self.main_box)

        self.connect('key-press-event', self.key_press)

    def key_press(self, widget, event):

        shift = event.state & Gdk.ModifierType.SHIFT_MASK

        if event.keyval == Gdk.KEY_Tab or event.keyval == Gdk.KEY_ISO_Left_Tab:

            if event.keyval == Gdk.KEY_ISO_Left_Tab:
                self.handle_cycle(False)
            else:
                self.handle_cycle(not shift)

        elif event.keyval == Gdk.KEY_Down or event.keyval == Gdk.KEY_Up:
            self.handle_cycle(event.keyval == Gdk.KEY_Down)

        elif event.keyval == Gdk.KEY_Return:
            self.handle_enter()

        elif event.keyval == Gdk.KEY_Escape:
            self.iconify()

    def handle_cycle(self, forward):
        if forward:
            self.result_model.select_next()
        else:
            self.result_model.select_prev()

    def handle_enter(self):
        self.result_model.confirm_entry()

    def keyword_selected(self, keyword):

        text = self.entry_box.get_entry_text()

        key, query = self._get_key_query(text)

        self.entry_box.set_key_query(key, keyword)

    def _get_key_query(self, text):

        parts = text.split(" ", 1)

        if not parts:
            return

        if len(parts) == 1:
            key = "Default"  # TODO
            query = parts[0]
        else:
            key = parts[0]
            query = parts[1]

        return key, query

    def do_search(self, search):

        key, query = self._get_key_query(search)

        self.perform_search(key, query)

    def perform_search(self, key, query):

        # TODO
        key_map = {
            "g": ("google", 'uk'),
            "a": ("amazon", 'uk'),
            "f": ("farnell", 'uk'),
            "(": ("baidu", None),
            "yd": ("youdao", None),
            "w": ("wikipedia", 'en'),
            'm': ('mdbg', None)
        }

        try:
            key, locale = key_map[key]
        except KeyError:
            key = self.client.cfg.get('complete', 'default', fallback='google')
            locale = None

        srch_thd = SearchRequestThread(self.client, key, locale, 'complete', query, self.handle_results)
        srch_thd.start()

    def handle_results(self, comps):

        print(comps)

        if "completions" not in comps:
            return

        self.result_model.set_results(comps["completions"])


class MnemGtk(object):
    '''
    GTK frontend for the Mnem REST client
    '''

    def __init__(self):
        '''
        Constructor
        '''
        port = 27183
        url = "http://localhost:%d" % (port)

        self.client = client.MnemRestClient(url)

        self.client.connect()

        self.window = MnemAppWindow(self.client)

        # enter the GUI loop
        self.window.start()

class SearchRequestThread(threading.Thread):
    '''
    Thread to go off and execute a request, which might take some time
    '''

    def __init__(self, client, key, locale, reqtype, query, handler, *args, **kwargs):
        self.client = client
        self.key = key
        self.locale = locale
        self.reqtype = reqtype
        self.query = query
        self.handler = handler

        super(SearchRequestThread, self).__init__(*args, **kwargs)

    def run(self):

        res = self.client.getCompletions(self.key, self.locale, self.reqtype, self.query)
        # res = {'completions': [{'url': 'https://yahoo.com/search?p=dictionary', 'keyword': 'dictionary'}, {'url': 'https://yahoo.com/search?p=domino%27s%20pizza', 'keyword': "domino's pizza"}, {'url': 'https://yahoo.com/search?p=discover%20card%20login', 'keyword': 'discover card login'}, {'url': 'https://yahoo.com/search?p=drudge%20report%202016', 'keyword': 'drudge report 2016'}, {'url': 'https://yahoo.com/search?p=delta', 'keyword': 'delta'}, {'url': 'https://yahoo.com/search?p=directv', 'keyword': 'directv'}, {'url': 'https://yahoo.com/search?p=driving%20directions', 'keyword': 'driving directions'}, {'url': 'https://yahoo.com/search?p=dish%20network', 'keyword': 'dish network'}, {'url': 'https://yahoo.com/search?p=dmv', 'keyword': 'dmv'}, {'url': 'https://yahoo.com/search?p=drudge%20report', 'keyword': 'drudge report'}]}

        self.handler(res)


if __name__ == "__main__":

    print("Mnem GTK")

    mnemGtk = MnemGtk()
