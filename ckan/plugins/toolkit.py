import inspect
import os
import re
import copy

import pylons
import paste.deploy.converters as converters
import webhelpers.html.tags

__all__ = ['toolkit']


class CkanVersionException(Exception):
    ''' Exception raised if required ckan version is not available. '''
    pass


class _Toolkit(object):
    '''This class is intended to make functions/objects consistently
    available to plugins, whilst giving core CKAN developers the ability move
    code around or change underlying frameworks etc. This object allows
    us to avoid circular imports while making functions/objects
    available to plugins.

    It should not be used internally within ckan - only by extensions.

    Functions/objects should only be removed after reasonable
    deprecation notice has been given.'''

    # contents should describe the available functions/objects. We check
    # that this list matches the actual availables in the initialisation
    contents = [
        ## Imported functions/objects ##
        '_',                    # i18n translation
        'c',                    # template context
        'request',              # http request object
        'render',               # template render function
        'render_text',          # Genshi NewTextTemplate render function
        'render_snippet',       # snippet render function
        'asbool',               # converts an object to a boolean
        'asint',                # converts an object to an integer
        'aslist',               # converts an object to a list
        'literal',              # stop tags in a string being escaped
        'get_action',           # get logic action function
        'check_access',         # check logic function authorisation
        'ObjectNotFound',       # action not found exception
                                # (ckan.logic.NotFound)
        'NotAuthorized',        # action not authorized exception
        'ValidationError',      # model update validation error
        'CkanCommand',          # class for providing cli interfaces

        ## Fully defined in this file ##
        'add_template_directory',
        'add_public_directory',
        'requires_ckan_version',
        'check_ckan_version',
        'CkanVersionException',
    ]

    docstrings = {
        'asbool': 'part of paste.deploy.converters: convert strings like yes, no, true, false, 0, 1 to boolean',
        'asint': 'part of paste.deploy.converters: convert stings to integers',
        'aslist': 'part of paste.deploy.converters: convert string objects to a list',
    }

    header = '''
Plugins Toolkit
===============

To allow a safe way for extensions to interact with ckan a toolkit is
provided. We aim to keep this toolkit stable across ckan versions so
that extensions will work across diferent versions of ckan.

.. Note::

    It is advised that when writing extensions that all interaction with
    ckan is done via the toolkit so that they do not break when new
    versions of ckan are released.

Over time we will be expanding the functionality available via
this toolkit.

Example extension that registers a new helper function available to
templates via h.example_helper() ::

    import ckan.plugins as p


    class ExampleExtension(p.SingletonPlugin):

        p.implements(p.IConfigurer)
        p.implements(p.ITemplateHelpers)

        def update_config(self, config):
            # add template directory that contains our snippet
            p.toolkit.add_template_directory(config, 'templates')

        @classmethod
        def example_helper(cls, data=None):
            # render our custom snippet
            return p.toolkit.render_snippet('custom_snippet.html', data)


        def get_helpers(self):
            # register our helper function
            return {'example_helper': self.example_helper}

The following functions, classes and exceptions are provided by the toolkit.

'''


    def __init__(self):
        self._toolkit = {}

    def _initialize(self):
        ''' get the required functions/objects, store them for later
        access and check that they match the contents dict. '''

        import ckan
        import ckan.lib.base as base
        import ckan.logic as logic
        import ckan.lib.cli as cli

        # Allow class access to these modules
        self.__class__.ckan = ckan
        self.__class__.base = base

        t = self._toolkit

        # imported functions
        t['_'] = pylons.i18n._
        t['c'] = pylons.c
        t['request'] = pylons.request
        t['render_text'] = base.render_text
        t['asbool'] = converters.asbool
        t['asint'] = converters.asint
        t['aslist'] = converters.aslist
        t['literal'] = webhelpers.html.tags.literal

        t['get_action'] = logic.get_action
        t['check_access'] = logic.check_access
        t['ObjectNotFound'] = logic.NotFound  # Name change intentional
        t['NotAuthorized'] = logic.NotAuthorized
        t['ValidationError'] = logic.ValidationError

        t['CkanCommand'] = cli.CkanCommand

        # class functions
        t['render'] = self._render
        t['render_snippet'] = self._render_snippet
        t['render_text'] = self._render_text
        t['add_template_directory'] = self._add_template_directory
        t['add_public_directory'] = self._add_public_directory
        t['requires_ckan_version'] = self._requires_ckan_version
        t['check_ckan_version'] = self._check_ckan_version
        t['CkanVersionException'] = CkanVersionException

        # check contents list correct
        errors = set(t).symmetric_difference(set(self.contents))
        if errors:
            raise Exception('Plugin toolkit error %s not matching' % errors)

    # wrappers
    @classmethod
    def _render_snippet(cls, template_name, data=None):
        ''' helper for the render_snippet function
        similar to the render function. '''
        data = data or {}
        return cls.base.render_snippet(template_name, **data)

    @classmethod
    def _render(cls, template_name, data=None):
        ''' Main template render function. '''
        data = data or {}
        return cls.base.render(template_name, data)

    @classmethod
    def _render_text(cls, template_name, data=None):
        ''' Render genshi text template. '''
        data = data or {}
        return cls.base.render_text(template_name, data)

    # new functions
    @classmethod
    def _add_template_directory(cls, config, relative_path):
        ''' Function to aid adding extra template paths to the config.
        The path is relative to the file calling this function. '''
        cls._add_served_directory(config, relative_path,
                                  'extra_template_paths')

    @classmethod
    def _add_public_directory(cls, config, relative_path):
        ''' Function to aid adding extra public paths to the config.
        The path is relative to the file calling this function. '''
        cls._add_served_directory(config, relative_path, 'extra_public_paths')

    @classmethod
    def _add_served_directory(cls, config, relative_path, config_var):
        ''' Add extra public/template directories to config. '''
        assert config_var in ('extra_template_paths', 'extra_public_paths')
        # we want the filename that of the function caller but they will
        # have used one of the available helper functions
        frame, filename, line_number, function_name, lines, index =\
            inspect.getouterframes(inspect.currentframe())[2]

        this_dir = os.path.dirname(filename)
        absolute_path = os.path.join(this_dir, relative_path)
        if absolute_path not in config.get(config_var, ''):
            if config.get(config_var):
                config[config_var] += ',' + absolute_path
            else:
                config[config_var] = absolute_path

    @classmethod
    def _version_str_2_list(cls, v_str):
        ''' convert a version string into a list of ints
        eg 1.6.1b --> [1, 6, 1] '''
        v_str = re.sub(r'[^0-9.]', '', v_str)
        return [int(part) for part in v_str.split('.')]

    @classmethod
    def _check_ckan_version(cls, min_version=None, max_version=None):
        ''' Check that the ckan version is correct for the plugin. '''
        current = cls._version_str_2_list(cls.ckan.__version__)

        if min_version:
            min_required = cls._version_str_2_list(min_version)
            if current < min_required:
                return False
        if max_version:
            max_required = cls._version_str_2_list(max_version)
            if current > max_required:
                return False
        return True

    @classmethod
    def _requires_ckan_version(cls, min_version, max_version=None):
        ''' Check that the ckan version is correct for the plugin. '''

        if not cls._check_ckan_version(min_version=min_version,
                                       max_version=max_version):
            if not max_version:
                error = 'Requires ckan version %s or higher' % min_version
            else:
                error = 'Requires ckan version between %s and %s' % \
                            (min_version, max_version)
            raise cls.CkanVersionException(error)

    def __getattr__(self, name):
        ''' return the function/object requested '''
        if not self._toolkit:
            self._initialize()
        if name in self._toolkit:
            return self._toolkit[name]
        else:
            if name == '__bases__':
                return self.__class__.__bases__
            raise Exception('`%s` not found in plugins toolkit' % name)

    def _function_info(self, functions):
        ''' Take a dict of functions and output readable info '''
        import inspect
        output = []
        for function_name in sorted(functions):
            fn = functions[function_name]
            if inspect.isclass(fn) and not inspect.ismethod(fn):
                if issubclass(fn, Exception):
                    output.append('*exception* **%s**' % function_name)
                else:
                    output.append('*class* **%s**' % function_name)
                if function_name in self.docstrings:
                    output.append('  %s' % self.docstrings[function_name])
                elif fn.__doc__:
                    bits = fn.__doc__.split('\n')
                    for bit in bits:
                        output.append('  %s' % bit.strip())
                else:
                    output.append('  NO DOCSTRING PRESENT')
                output.append('\n')
                continue
            args_info = inspect.getargspec(fn)
            params = args_info.args
            num_params = len(params)
            if args_info.varargs:
                params.append('\*' + args_info.varargs)
            if args_info.keywords:
                params.append('\*\*' + args_info.keywords)
            if args_info.defaults:
                offset = num_params - len(args_info.defaults)
                for i, v in enumerate(args_info.defaults):
                    params[i + offset] = params[i + offset] + '=' + repr(v)
            # is this a classmethod if so remove the first parameter
            if inspect.ismethod(fn) and inspect.isclass(fn.__self__):
                params = params[1:]
            params = ', '.join(params)
            output.append('**%s** (*%s*)' % (function_name, params))
            # doc string
            if function_name in self.docstrings:
                output.append('  %s' % self.docstrings[function_name])
            elif fn.__doc__:
                bits = fn.__doc__.split('\n')
                for bit in bits:
                    output.append('  %s' % bit.strip())
            else:
                output.append('  NO DOCSTRING PRESENT')
            output.append('\n')
        return ('\n').join(output)

    def _document(self):
        self._initialize()
        out = self.header
        functions = {}
        functions = copy.copy(self._toolkit)
        del functions['c']
        del functions['request']
        return out + self._function_info(functions)

toolkit = _Toolkit()
del _Toolkit
