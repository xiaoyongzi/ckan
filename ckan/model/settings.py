import datetime

from meta import *
from core import *
from package import *
from types import make_uuid
from user import User

__all__ = ['Setting']

setting_table = Table('setting', metadata,
                     Column('id', UnicodeText, primary_key=True, default=make_uuid),
                     Column('key', UnicodeText),
                     Column('value', UnicodeText),
                     )

class Setting(DomainObject):
    pass

mapper(Setting, setting_table)
