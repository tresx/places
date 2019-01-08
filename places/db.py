import click
from flask import current_app, g
from flask.cli import with_appcontext
import os
import psycopg2
from psycopg2.extras import DictCursor


def get_db():
    """Return postgres connection object."""
    if 'db' not in g:
        g.db = psycopg2.connect(dsn=current_app.config['DATABASE'],
                                cursor_factory=DictCursor)
    return g.db


def close_db(e=None):
    """Close database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialise database from schema.sql file."""

    with open(
            os.path.join(os.path.dirname(__file__), 'schema.sql'), 'rb') as f:
        _data_sql = f.read().decode('utf-8')
        with get_db() as conn:
            conn.cursor().execute(_data_sql)
        conn.close()


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialised the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
