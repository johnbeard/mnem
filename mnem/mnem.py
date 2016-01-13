#! /usr/bin/env python

import os
# provide a default named log for package-wide use
import logging

logging.basicConfig(level=logging.ERROR)

PLUGIN_DIRS = ["plugins"]

from yapsy.PluginManager import PluginManager

class MnemError(Exception):
    pass

class MnemoryNotFoundError(MnemError):

    def __init__(self, mnemoryKey):
        self.key = mnemoryKey

    def __str__(self):
        return self.key

    def getMnemoryKey(self):
        return self.key

class Mnem():

    def __init__(self):
        self.mnemories = {}

    def load_plugins(self):

        # Build the manager
        simplePluginManager = PluginManager()
        # Tell it the default place(s) where to find plugins
        simplePluginManager.setPluginPlaces(PLUGIN_DIRS)
        # Load all plugins
        simplePluginManager.collectPlugins()

        # Activate all loaded plugins
        for plugin in simplePluginManager.getAllPlugins():
            #print("Importing plugin: %s" % plugin.plugin_object.get_name())

            mnemories = plugin.plugin_object.report_mnemories()
            #print("  Providing: %s" % mnemories)

            for m in mnemories:

                def getKey(mnemory):

                    if mnemory.defaultAlias:
                        return mnemory.defaultAlias

                    return self.key

                # TODO: allow to override aliases by configs?
                self.mnemories[getKey(m)] = m

    def search(self, key, query, locale=None):

        if not key in self.mnemories:
            return None

        #instantiate the search engine
        m = self.mnemories[key](locale)
        return m.submitSearch(query)

    def complete(self, key, query, completion=None, locale=None):

        try:
            #instantiate the search engine
            m = self.mnemories[key](locale)
        except KeyError:
            raise MnemoryNotFoundError(key)

        return m.submitForSuggestions(completion, query)
