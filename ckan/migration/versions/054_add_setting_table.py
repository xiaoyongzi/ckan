from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):
    metadata = MetaData()
    metadata.bind = migrate_engine
    migrate_engine.execute('''
        CREATE TABLE setting (
        	id text NOT NULL,
        	key text,
        	value text,
        	owner text,
        	updated timestamp without time zone
        );

        ALTER TABLE setting
	    ADD CONSTRAINT setting_pkey PRIMARY KEY (id);
    ''')