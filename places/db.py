import psycopg2

import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    """Return postgres connection object."""
    if 'db' not in g:
        g.db = psycopg2.connect(current_app.config['DATABASE'])
    return g.db


def close_db(e=None):
    """Close database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialise database from schema.sql file."""
    cur = get_db().cursor()
    cur.execute(open('schema.sql', 'r').read())


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialised the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
