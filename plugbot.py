"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

__author__ = 'Hernan E. Grecco <hernan.grecco@gmail.com>'
__license__ = 'MIT License/X11 license'

import logging

from optparse import OptionParser
from xml.etree import ElementTree as ET

from pluginbase import PluginDict,  Plugin

class BotPlugin(Plugin):

    def _set_dict(self, value):
        if value is None:
            self.bot.unregister_commands(self)
        else:
            self.bot = value.bot
            super(BotPlugin,  self)._set_dict(value)
            self.bot.register_commands(self)

    plugin_dict = property(fget = Plugin._get_dict, fset = _set_dict)

class PlugBot(object):
    """ Base class for bots that are pluggable
        Requires to be coinherited with a class that has the following commands:
        - send_message
        - add_event_handler
        as defined in SleekXMPP
    """

    def __init__(self, default_package = 'plugins'):
        self.cmd_plugins = PluginDict(plugin_base_class = BotPlugin, default_package = default_package)
        self.cmd_plugins.bot = self

        PlugBot.start(self)

    def register_cmd_plugins(self):
        """ Registers all bot plugins required by botconfig.
        """
        plugins = self.botconfig.findall('plugins/bot/plugin')
        if plugins:
            for plugin in plugins:
                loaded = self.cmd_plugins.register(plugin.attrib['name'], plugin.find('config'))
                if loaded:
                    logging.info("Registering plugin %s OK" % (plugin.attrib['name']))
                else:
                    logging.info("Registering plugin %s FAILED." % (plugin.attrib['name']))

    def stop(self):
        logging.info("Stopping PlugBot")
        for plugin in self.cmd_plugins.keys():
            del self.cmd_plugins[plugin]

    def start(self):
        logging.info("Starting PlugBot")
        self.register_cmd_plugins()

    def reset(self):
        """  Reset commandbot commands to its initial state
        """
        PlugBot.stop(self)
        PlugBot.start(self)
