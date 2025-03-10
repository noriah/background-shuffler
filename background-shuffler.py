#!/usr/bin/python

# Copyright (c) 2015 noriah vix@noriah.dev
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from gi.repository import Gio
from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from threading import Timer
import subprocess
import json
import signal
from os import listdir
import random
# import gtk.glade
import sys
import os
from xdg.DesktopEntry import DesktopEntry

bg_types = ('.png', '.jpg')

def file_filter(file_name):
    for i in bg_types:
        if file_name.lower().endswith(i):
            return True
    return False

random.seed()

class Shuffler:

    def __init__(self):

        self.indicator = Indicator(self)

        self.settings = Settings(self)

        self.bg_settings = Gio.Settings.new('org.gnome.desktop.background')

        if self.settings.background_folder is '':
            self.settings.set_background_folder(os.path.join(os.environ['HOME'], 'Pictures'))

        if self.settings.background_folder[-1] != "/" :
            self.settings.set_background_folder(self.settings.background_folder + '/')

        if self.settings.autostart:
            self.enable_autostart('activate')
        else:
            self.disable_autostart('activate')

        self.bg_timer = None
        # self.bg_list = list()

        self.update_bg_list()
        self.timer_shuffle()

    def user_call_shuffle(self, item):
        self.bg_timer.cancel()
        self.timer_shuffle()

    def shuffle(self):
        self.current_bg_index += 1
        if self.current_bg_index > len(self.bg_list):
            self.current_bg_index = 0
        self.bg_settings.set_string('picture-uri', "file://"
            + self.settings.background_folder
            + self.bg_list[self.current_bg_index])

    def timer_shuffle(self):
        # if self.bg_timer is None:
        self.bg_timer = Timer(self.settings.display_time, self.timer_shuffle)

        self.shuffle()
        self.bg_timer.start()

    def update_bg_list(self):
        self.current_bg_index = 0
        self.bg_list = []
        self.bg_list = listdir(self.settings.background_folder)
        self.bg_list = filter(file_filter, self.bg_list)
        random.shuffle(self.bg_list)
        random.shuffle(self.bg_list)
        random.shuffle(self.bg_list)

    def refresh_bg_list(self, item):
        self.update_bg_list()
        self.user_call_shuffle("activate")
        # self.timer_shuffle()

    def pause_shuffle(self, item):
        pass

    def unpause_shuffle(self, item):
        pass

    def enable_autostart(self, item):
        self.indicator.item_disable_autostart.show()
        self.indicator.item_enable_autostart.hide()
        self.create_autostarter()

    def disable_autostart(self, item):
        self.indicator.item_enable_autostart.show()
        self.indicator.item_disable_autostart.hide()
        self.delete_autostarter()


    def open_background_folder(self, item):
        try:
            subprocess.Popen(['xdg-open', self.settings.background_folder])
        except OSError:
            pass

    def open_background(self, item):
        try:
            subprocess.Popen(['xdg-open', self.settings.background_folder
                + self.bg_list[self.current_bg_index]])
        except OSError:
            pass

    def reload_settings(self, item):
        self.settings.load_settings()
        self.refresh_bg_list(item)
        if self.settings.autostart:
            self.enable_autostart(item)
        else:
            self.disable_autostart(item)

    def open_settings_file(self, item):
        try:
            subprocess.Popen(['xdg-open', self.settings.filename])
        except OSError:
            pass

    def open_preferences(self, item):
        pass

    #autostart code copied from AWN
    def get_autostart_file_path(self):
        autostart_dir = os.path.join(os.environ['HOME'], '.config',
                                     'autostart')
        return os.path.join(autostart_dir, 'background-shuffler.desktop')

    def create_autostarter(self):
        autostart_file = self.get_autostart_file_path()
        autostart_dir = os.path.dirname(autostart_file)

        if not os.path.isdir(autostart_dir):
            #create autostart dir
            try:
                os.mkdir(autostart_dir)
            except Exeption, e:
                print "creation of autostart dir failed, please make it yourself: %s" % autostart_dir
                raise e

        if not os.path.isfile(autostart_file):
            #create autostart entry
            starter_item = DesktopEntry(autostart_file)
            starter_item.set('Name', 'Background Shuffler applet')
            starter_item.set('Exec', 'background-shuffler.py')
            starter_item.set('Icon', 'background-shuffler-panel')
            starter_item.set('X-GNOME-Autostart-enabled', 'true')
            starter_item.write()
            self.settings.set_autostart(True)

    def delete_autostarter(self):
        autostart_file = self.get_autostart_file_path()
        if os.path.isfile(autostart_file):
            os.remove(autostart_file)
            self.settings.set_autostart(False)

    def quit(self, item):
        self.bg_timer.cancel()
        gtk.main_quit()
        sys.exit(0)

    def run(self):
        gtk.main()


class Indicator:

    def __init__(self, main):
        self.main = main
        self.setup_indicator()

    def setup_indicator(self):
        self.indicator = appindicator.Indicator.new(
            "background-shuffler-indicator",
            "bg-shuffler-panel",
            appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)

        # self.indicator.set_icon("pamac-tray-no-update")

        self.indicator.set_menu(self.setup_menu())

    def setup_menu(self):
        menu = gtk.Menu()

        item = gtk.MenuItem("Next Background")
        item.connect("activate", self.main.user_call_shuffle)
        item.show()
        menu.append(item)

        # self.item_pause = gtk.MenuItem("Pause Background")
        # self.item_pause.connect("activate", self.main.pause_shuffle)
        # self.item_pause.show()
        # menu.append(self.item_pause)

        # self.item_unpause = gtk.MenuItem("Unpause Background")
        # self.item_unpause.connect("activate", self.main.unpause_shuffle)
        # self.item_unpause.hide()
        # menu.append(self.item_unpause)

        item = gtk.SeparatorMenuItem()
        item.show()
        menu.append(item)

        item = gtk.MenuItem("Refresh Background List")
        item.connect("activate", self.main.refresh_bg_list)
        item.show()
        menu.append(item)

        item = gtk.MenuItem("Open Backgrounds Folder")
        item.connect("activate", self.main.open_background_folder)
        item.show()
        menu.append(item)

        item = gtk.MenuItem("Open Background")
        item.connect("activate", self.main.open_background)
        item.show()
        menu.append(item)

        item = gtk.SeparatorMenuItem()
        item.show()
        menu.append(item)

        item = gtk.MenuItem("Reload Settings")
        item.connect("activate", self.main.reload_settings)
        item.show()
        menu.append(item)

        item = gtk.MenuItem("Open Settings File")
        item.connect("activate", self.main.open_settings_file)
        item.show()
        menu.append(item)

        # item = gtk.MenuItem("Preferences")
        # item.connect("activate", self.main.open_preferences)
        # item.show()
        # menu.append(item)

        item = gtk.SeparatorMenuItem()
        item.show()
        menu.append(item)

        self.item_enable_autostart = gtk.MenuItem("Enable Autostart")
        self.item_enable_autostart.connect("activate", self.main.enable_autostart)
        self.item_enable_autostart.show()
        menu.append(self.item_enable_autostart)

        self.item_disable_autostart = gtk.MenuItem("Disable Autostart")
        self.item_disable_autostart.connect("activate", self.main.disable_autostart)
        self.item_disable_autostart.hide()
        menu.append(self.item_disable_autostart)


        item = gtk.SeparatorMenuItem()
        item.show()
        menu.append(item)

        item = gtk.MenuItem("Quit")
        item.connect("activate", self.main.quit)
        item.show()
        menu.append(item)

        return menu

    def main(self):
        gtk.main()

# class Preferences:

#     def __init__(self, main):
#         self.main = main
#         self.gladefile = os.path.join(os.path.dirname(os.path.dirname(
#             os.path.realpath(__file__))), "background-shuffler/preferences.glade")
#         self.wTree = gtk.glade.XML(self.gladefile)

#         self.window = self.wTree.get_widget("window1")


class Settings:

    def __init__(self, main):
        self.main = main
        self.filename = os.path.join(os.environ['HOME'], '.bg-shuffler')

        self.settings_data = {
            "autostart": False,
            "background_folder": '',
            "display_time": 600,
            "reshow_time": 600}

        if not os.path.isfile(self.filename):
            self.save_settings()
        else:
            self.load_settings()

    def set_autostart(self, b):
        self.settings_data["autostart"] = b
        self.save_settings()
        self.autostart = b

    def set_background_folder(self, f):
        self.settings_data["background_folder"] = f
        self.save_settings()
        self.background_folder = f

    def set_display_time(self, t):
        self.settings_data["display_time"] = t
        self.save_settings()
        self.display_time = t

    def set_reshow_time(self, t):
        self.settings_data["reshow_time"] = t
        self.save_settings()
        self.reshow_time = t

    def load_settings(self):
        with open(self.filename) as infile:
            self.settings_data = json.load(infile)

        self.autostart = self.settings_data["autostart"]
        self.background_folder = self.settings_data["background_folder"]
        self.display_time = self.settings_data["display_time"]
        self.reshow_time = self.settings_data["reshow_time"]

    def save_settings(self):
        with open(self.filename, 'w') as outfile:
            json.dump(self.settings_data, outfile, indent = 2)
            
    def main(self):
        gtk.main()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    try:
        app = Shuffler()
        app.run()
    except KeyboardInterrupt:
        app.quit("yup")
        sys.exit(0)

