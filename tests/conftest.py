import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flaskr import create_app
from flaskr.db import get_db, init_db

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient

_data_sql = (Path(__file__).parent / 'data.sql').read_text('utf-8')


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()

    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
    })

    with app.app_context():
        init_db()
        get_db().executescript(_data_sql)

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app: 'Flask'):
    return app.test_client()


@pytest.fixture
def runner(app: 'Flask'):
    return app.test_cli_runner()


@pytest.fixture
def auth(client: 'FlaskClient'):
    return AuthActions(client)


class AuthActions:
    def __init__(self, client: 'FlaskClient') -> None:
        self._client = client

    def login(self, username: str, password: str):
        return self._client.post(
            '/auth/login',
            data={'username': username, 'password': password}
        )

    def logout(self):
        return self._client.get('/auth/logout')
