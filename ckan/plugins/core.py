"""
Provides plugin services to the CKAN
"""

import logging
from inspect import isclass
from itertools import chain
from operator import itemgetter
from pkg_resources import iter_entry_points

from pyutilib.component.core import PluginGlobals, implements
from pyutilib.component.core import ExtensionPoint
from pyutilib.component.core import SingletonPlugin as _pca_SingletonPlugin
from pyutilib.component.core import Plugin as _pca_Plugin

from pylons import config

from ckan.plugins.interfaces import IPluginObserver

__all__ = [
    'PluginImplementations', 'implements',
    'PluginNotFoundException', 'Plugin', 'SingletonPlugin',
    'load', 'load_all', 'unload', 'unload_all',
    'reset'
]

log = logging.getLogger(__name__)

# Entry point group.
PLUGINS_ENTRY_POINT_GROUP = "ckan.plugins"

# Entry point group for system plugins (those that are part of core ckan and do
# not need to be explicitly enabled by the user)
SYSTEM_PLUGINS_ENTRY_POINT_GROUP = "ckan.system_plugins"

# _plugins_info and _plugins_index are used in ordering plugins
_plugins_info = {}
_plugins_index = 0


class PluginImplementations(ExtensionPoint):
    ''' This is a cusomised version of pyutilib ExtensionPoint that
    returns the plugins in the order specified by the ckan config.

    Usage::

        >>> plugins = PluginImplementations(IMapper)
        ... # plugins is a list of plugins implementing IMapper

    '''

    def extensions(self, all=False, key=None):
        plugins = super(PluginImplementations, self) \
            .extensions(all=all, key=key)
        ordered = []
        for plugin in plugins:
            ordered.append([plugin, _plugins_info[plugin.__class__]])
        ordered = [x[0] for x in sorted(ordered, key=itemgetter(1, 0))]
        return ordered


class PluginNotFoundException(Exception):
    """
    Raised when a requested plugin cannot be found.
    """


class Plugin(_pca_Plugin):
    """
    Base class for plugins which require multiple instances.

    Unless you need multiple instances of your plugin object you should
    probably use SingletonPlugin.
    """


class SingletonPlugin(_pca_SingletonPlugin):
    """
    Base class for plugins which are singletons (ie most of them)

    One singleton instance of this class will be created when the plugin is
    loaded. Subsequent calls to the class constructor will always return the
    same singleton instance.
    """


def _get_service(plugin):
    """
    Return a service (ie an instance of a plugin class).

    :param plugin: any of: the name of a plugin entry point; a plugin class; an
        instantiated plugin object.
    :return: the service object
    """

    if isinstance(plugin, basestring):
        try:
            name = plugin
            (plugin,) = iter_entry_points(
                group=PLUGINS_ENTRY_POINT_GROUP,
                name=name
            )
        except ValueError:
            raise PluginNotFoundException(plugin)

        return plugin.load()(name=name)

    elif isinstance(plugin, _pca_Plugin):
        return plugin

    elif isclass(plugin) and issubclass(plugin, _pca_Plugin):
        return plugin()

    else:
        raise TypeError("Expected a plugin name, class or instance", plugin)


def load_all(config):
    """
    Load all plugins listed in the 'ckan.plugins' config directive.
    """

    global _plugins_info
    _plugins_info = {}
    global _plugins_index
    _plugins_index = 0

    plugins = chain(
        find_system_plugins(),
        find_user_plugins(config)
    )

    # PCA default behaviour is to activate SingletonPlugins at import time. We
    # only want to activate those listed in the config, so clear
    # everything then activate only those we want.
    unload_all()

    for plugin in plugins:
        load(plugin)


def reset():
    """
    Clear and reload all configured plugins
    """
    load_all(config)


def load(plugin):
    """
    Load a single plugin, given a plugin name, class or instance
    """
    observers = PluginImplementations(IPluginObserver)
    for observer_plugin in observers:
        observer_plugin.before_load(plugin)
    service = _get_service(plugin)
    service.activate()
    for observer_plugin in observers:
        observer_plugin.after_load(service)
    return service


def unload_all():
    """
    Unload (deactivate) all loaded plugins
    """
    for env in PluginGlobals.env_registry.values():
        for service in env.services.copy():
            unload(service)


def unload(plugin):
    """
    Unload a single plugin, given a plugin name, class or instance
    """
    observers = PluginImplementations(IPluginObserver)
    service = _get_service(plugin)
    for observer_plugin in observers:
        observer_plugin.before_unload(service)

    service.deactivate()

    for observer_plugin in observers:
        observer_plugin.after_unload(service)

    return service


def find_user_plugins(config):
    """
    Return all plugins specified by the user in the 'ckan.plugins' config
    directive.
    """
    global _plugins_index
    global _plugins_info

    plugins = []
    for name in config.get('ckan.plugins', '').split():
        entry_points = list(
            iter_entry_points(group=PLUGINS_ENTRY_POINT_GROUP, name=name)
        )
        if not entry_points:
            raise PluginNotFoundException(name)
        loaded_plugins = (ep.load() for ep in entry_points)
        for x in loaded_plugins:
            plugins.append(x)
            _plugins_info[x] = _plugins_index
        _plugins_index += 1
    return plugins


def find_system_plugins():
    """
    Return all plugins in the ckan.system_plugins entry point group.

    These are essential for operation and therefore cannot be enabled/disabled
    through the configuration file.
    """
    global _plugins_index
    global _plugins_info

    plugins = []
    entry_points = iter_entry_points(group=SYSTEM_PLUGINS_ENTRY_POINT_GROUP)
    loaded_plugins = (ep.load() for ep in entry_points)
    for x in loaded_plugins:
        plugins.append(x)
        _plugins_info[x] = _plugins_index
        _plugins_index += 1
    return plugins
