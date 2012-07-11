import os
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.plugins as libplugins

class ExampleIGroupFormPlugin(plugins.SingletonPlugin,
        libplugins.DefaultGroupForm):
    plugins.implements(plugins.IGroupForm)
    '''An example CKAN plugin that adds a 'group type' option to the group form
    when creating or updating groups. The option is a drop-down list with three
    possible values to choose from.

    '''
    def group_types(self):
        # Tell CKAN which types of group this plugin handles.
        # Whenever a group with one of the below returned types is being used,
        # CKAN will call this plugin.
        return ('type 1', 'type 2', 'type 3')

    def is_fallback(self):
        # Here we return True to tell CKAN to use this plugin as the default
        # for handling a group when no other plugin's group_types() method has
        # matched the group's type. Returning True here ensures that this
        # plugin is used when a new group is being created.
        return True

    def group_form(self):
        # Return the path to the template that CKAN should use for the form
        # when creating or updating groups. This overrides CKAN's default form
        # template with the one from this extension.
        here = os.path.dirname(__file__)
        path = os.path.join(here, 'new_group_form.html')
        return path

    def setup_template_variables(self, context, data_dict):
        libplugins.DefaultGroupForm.setup_template_variables(self, context,
                data_dict)
        # Here we add the possible group types to the template context before
        # the group form is rendered. The form uses these types to create the
        # Group Type dropdown list.
        toolkit.c.group_types = ('type 1', 'type 2', 'type 3')
