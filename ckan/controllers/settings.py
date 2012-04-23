from pylons.i18n import set_lang
import sqlalchemy.exc

import ckan.authz as authz
import ckan.lib.navl.dictization_functions as dictfunc
import ckan.logic as logic
import ckan.logic.action as action
import ckan.model as model

from ckan.lib.base import *
from ckan.lib.helpers import url_for


def _ensure_hex(key, data, errors, context):
    value = data.get(key)

    def is_hex(value):
        v = ''.join(c for c in value if c != '#')
        try:
            x = int(v, 16)
        except:
            return False
        data[key] = v
        return True

    if not value or not is_hex(value):
        data.pop(key, None)
        errors[key] = _("Value must be a hexadecimal number")
        raise dictfunc.StopOnError

class SettingsController(BaseController):

    def __before__(self, action, **env):
        BaseController.__before__(self, action, **env)
        if not authz.Authorizer.is_sysadmin(c.user):
            abort(401, _('Not authorized to see this page'))


    def index(self):
        data, errors, error_summary = {}, {}, {}
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author }
        fields = ['name', 'image_url',
                  'tagline', 'css_header',
                  'css_footer', 'css_background']

        success = False
        if request.method == 'POST':
            td = logic.tuplize_dict( logic.parse_params(request.params) )
            unflattened = dictfunc.unflatten( td )
            data = logic.clean_dict( unflattened )

            schema = logic.schema.default_settings_schema(_ensure_hex)
            data, errors = dictfunc.validate(data, schema)
            if errors:
                e = logic.ValidationError(errors, action.error_summary(errors))
                errors = e.error_dict
                error_summary = e.error_summary
            else:
                for f in fields:
                    model.Setting.set_value( f, data.get(f, ""), c.user )
                    success = True
        else:
            data = dict(model.Setting.get_values(fields))

        extras = { "data" : data, "error_summary" : error_summary,
                   "errors" : errors, "success" : success}
        self._setup_template_variables()
        return render('settings/index.html',extra_vars=extras)

    def _setup_template_variables(self):
        pass