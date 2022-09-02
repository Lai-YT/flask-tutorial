import sqlite3
from typing import TYPE_CHECKING

import pytest

from flaskr.db import get_db

if TYPE_CHECKING:
    from click.testing import Result
    from flask import Flask
    from flask.testing import FlaskCliRunner
    from pytest import MonkeyPatch


def test_db_connection_gotten_during_a_request_is_the_same(app: 'Flask'):
    with app.app_context():
        db = get_db()

        assert db is get_db()


def test_db_closed_automatically_at_the_end_of_request(app: 'Flask'):
    with app.app_context():
        db = get_db()

    with pytest.raises(sqlite3.ProgrammingError, match='closed'):
        db.execute('SELECT 1')


def test_init_db_command_called_with_cli(runner: 'FlaskCliRunner',
                                         monkeypatch: 'MonkeyPatch'):
    class Recorder:
        called = False

    def fake_init_db():
        Recorder.called = True
    monkeypatch.setattr('flaskr.db.init_db', fake_init_db)

    result: Result = runner.invoke(args=('init-db',))

    assert 'Initialized' in result.output
    assert Recorder.called
