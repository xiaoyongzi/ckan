import datetime


import core
import meta
import types
import sqlalchemy as sa

__all__ = ['Setting']

setting_table = meta.Table('setting', meta.metadata,
                     meta.Column('id', sa.types.UnicodeText,
                                  primary_key=True,
                                  default=types.make_uuid),
                     meta.Column('key', sa.types.UnicodeText),
                     meta.Column('value', sa.types.UnicodeText),
                     )

class Setting(core.DomainObject):

    @classmethod
    def get_values(cls, keys):
        pass


meta.mapper(Setting, setting_table)
