import sqlite3
from typing import TYPE_CHECKING

import click
from flask import current_app, g

if TYPE_CHECKING:
    from sqlite3 import Connection
    from flask import Flask


def init_app(app: 'Flask'):
    app.cli.add_command(init_db_command)
    app.teardown_appcontext(close_db)


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf-8'))


def get_db() -> 'Connection':
    if not _is_connection_created():
        _connect_db()
    return g.db


def close_db(e=None):
    if _is_connection_created():
        db = g.pop('db')
        db.close()
    assert not _is_connection_created()


def _is_connection_created():
    return 'db' in g


def _connect_db():
    g.db = sqlite3.connect(
        current_app.config['DATABASE'],
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    g.db.row_factory = sqlite3.Row
