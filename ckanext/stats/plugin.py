from logging import getLogger

import ckan.plugins as p

log = getLogger(__name__)

# we need to store the config. We do this in StatsPlugin.update_config()
stored_config = None
# place to store cache config status
cache_enabled = False

class StatsPlugin(p.SingletonPlugin):
    '''Stats plugin.'''

    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IConfigurable, inherit=True)

    def after_map(self, map):
        map.connect('stats', '/stats',
            controller='ckanext.stats.controller:StatsController',
            action='index')
        map.connect('stats_action', '/stats/{action}',
            controller='ckanext.stats.controller:StatsController')
        return map

    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_public_directory(config, 'public')

    def configure(self, config):
        # store the config for later use
        global stored_config
        stored_config = config

        global cache_enabled
        cache_enabled = p.toolkit.asbool(
            config.get('ckanext.stats.cache_enabled', 'True'))
