"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

__author__ = 'Hernan E. Grecco <hernan.grecco@gmail.com>'
__license__ = 'MIT License/X11 license'

import logging
import inspect
import imp

from collections import defaultdict

def call_on_register(plugin_name):
    """ Decorator to relate a plugin method to the event of another plugin
         being registered
            plugin_name -- the name of the plugin or an iterable with plugin names
    """
    def __outer(f):
        def __inner(*args, **kwargs):
            return f(*args, **kwargs)
        if isinstace(plugin_name,  'str'):
            plugin_name = (plugin_name,  )
        __inner._call_on_register = plugin_name
    return __outer

def call_on_unregister(plugin_name):
    """ Decorator to relate a plugin method to the event of another plugin
         being unregistered
            plugin_name -- the name of the plugin or an iterable with plugin names
    """
    def __outer(f):
        def __inner(*args, **kwargs):
            return f(*args, **kwargs)
        if isinstace(plugin_name,  'str'):
            plugin_name = (plugin_name,  )
        __inner._call_on_unregister = plugin_name
    return __outer

class Plugin(object):
    """ A base class for plugins.
    """

    def __init__(self,  config = {}):
        self.config = config
        self.__plugin_dict = None

    def on_register(self):
        pass

    def on_unregister(self):
        pass

    def _register_calls(self):
        for name, action in inspect.getmembers(self):
            if inspect.ismethod(action) and hasattr(action, '_call_on_register'):
                for related in action._call_on_register:
                    if related in self.__plugin_dict:
                        action(related)
                    self.__plugin_dict._call_on_register[related].add((self, action))
            if inspect.ismethod(action) and hasattr(action, '_call_on_unregister'):
                for related in action._call_on_unregister:
                    if related in self.__plugin_dict:
                        action(related)
                    self.__plugin_dict._call_on_unregister[related].add((self, action))

    def _get_dict(self):
        return self.__plugin_dict

    def _set_dict(self, value):
        self.__plugin_dict = value
        self._register_calls()

    plugin_dict = property(fget = _get_dict, fset = _set_dict)


def default_plugin_factory(aclass, config):
    """ The default factory for Plugin.
    """
    return aclass(config)


class PluginDict(dict):
    """ A dictionary class to hold plugins.
    """

    def __init__(self, plugin_base_class = Plugin, default_factory = default_plugin_factory, default_package = 'plugins'):
        """ Initialize dictionary
                plugin_base_class -- class from which plugins must derive (default Plugin)
                default_factory   -- method to instantiate a plugin object (default default_plugin_factory)
                default_package   -- string specifying where to look for plugins (default 'plugins')
        """
        super(PluginDict, self).__init__()
        self._plugin_base_class = plugin_base_class
        self._default_factory = default_factory
        self._default_package = default_package
        self.__call_on_register = defaultdict(set)
        self.__call_on_unregister = defaultdict(set)
        __import__(default_package)
        self.__imported = set()
        self.__imported.add(default_package)

    def __getitem__(self, key):
        """ Get a Plugin from the dictionary.
        """
        return super(PluginDict, self).__getitem__(key)

    def __setitem__(self, key, value):
        """ Add a Plugin to the dictionary an call initializers.
        """
        if not isinstance(value, self._plugin_base_class):
            raise NotAPluginError(value.__name__)

        value.plugin_dict = self
        value.on_register()
        for event in self.__call_on_register[key]:
            event[1](value)

        return super(PluginDict, self).__setitem__(key, value)

    def __delitem__(self, key):
        """ Call plugin.on_unregister and then remove it form the dictionary
        """
        if key in self:
            current = super(PluginDict, self).__getitem__(key)
            current.on_unregister()
            for event in self.__call_on_unregister[key]:
                event[1](current)
            self._unregister_event(key)
            current.plugin_dict = None
            logging.info("%s unregistered" % key)
        else:
            logging.warning("Plugin not in dict %s." % key)

        super(PluginDict, self).__delitem__(key)

    def register(self, name, config = {}, module = '__default__', package = '__default__'):
        """ Loads and register a plugin
                name    -- plugin name (name of the class)
                config  -- extra configuration (to be handled to the plugin)
                package -- where the plugin is declared
        """
        try:
            if name in self:
                return
            if isinstance(name,  self._plugin_base_class):
                plugin = name
                name = name.__class__.__name__
                self[name] = plugin
            elif isinstance(name,  str):
                if package == '__default__':
                    package = self._default_package
                elif not package in self.__imported:
                    __import__(package)
                    self.__imported.add(package)
                    logging.debug('Imported package %s' % package)
                if module == '__default__':
                    module = name

                imported = __import__("%s.%s" % (package, module), fromlist = name)
                self[name] = self._default_factory(getattr(imported, name),  config)

            return True

        except Exception,  e:
            logging.error('Error while registering plugin %s: %s' % (name,  e))

    def register_many(self, include = '__all__', exclude = set(), config = dict()):
        """ Register multiple plugins

                include -- plugins names to register (default __init__.__all__)
                exclude -- plugins names to ignored (default empty set)
                config  -- dict plugin_name:config (default empty dict)
        """

        if not include:
            include = __all__

        for plugin in set(include).difference(set(exclude)):
            self.register(plugin, config.get(plugin, {}))

    def reload(self, name, config = {}):
        """ Reload a registered plugins.
        """
        config = getattr(self[name], 'config',  {})
        module = __import__(self[name].__module__, fromlist = name)
        del self[name]
        reload(module)
        self.register(name, config)

    def reload_all(self):
        """ Reload all registered plugins.
        """

        for plugin in self.keys():
            self.reload(plugin)

    def _unregister_event(self, plugin):
        """ Unregister events associated with a plugin
        """
        for v in self.__call_on_register.values():
            v = set(filter(lambda x: x[0] != plugin, v))
        for v in self.__call_on_unregister.values():
            v = set(filter(lambda x: x[0] != plugin, v))

    def get_modules(self):
            return [__import__(self[name].__module__, fromlist = name) for name in self.keys()]

class NotAPluginError(Exception):
    """Exception raised when the object added to PluginDict is
    not a Plugin

    Attributes:
        classname -- name of the class
    """

    def __init__(self, classname):
        self.classname = classname
