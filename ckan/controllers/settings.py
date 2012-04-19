import random

from pylons.i18n import set_lang
import sqlalchemy.exc

import ckan.authz as authz

import ckan.logic as logic
from ckan.lib.base import *
from ckan.lib.helpers import url_for


class SettingsController(BaseController):
    repo = model.repo

    def __before__(self, action, **env):
        BaseController.__before__(self, action, **env)
        if not authz.Authorizer.is_sysadmin(c.user):
            abort(401, _('Not authorized to see this page'))

    def index(self):
        return render('settings/index.html', cache_force=True)

