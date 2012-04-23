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
                     meta.Column('owner', sa.types.UnicodeText),
                     meta.Column('updated', sa.types.DateTime, default=datetime.datetime.now)
                )

class Setting(core.DomainObject):

    @classmethod
    def get_values(cls, keys):
        query = meta.Session.query(Setting).\
                filter(Setting.key.in_(keys))
        return [ (s.key, s.value,) for s in query.all() ]

    @classmethod
    def set_value(cls, key, value, user):
        setting = meta.Session.query(cls).\
                    filter(cls.key == key).first()
        if setting:
            setting.value = value
            setting.owner = user
            setting.updated = datetime.datetime.now()
        else:
            setting = Setting( key=key, value=value,
                                updated=datetime.datetime.now(),
                                owner=user  )
        meta.Session.add( setting )
        meta.Session.commit()

meta.mapper(Setting, setting_table)
