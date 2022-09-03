from typing import TYPE_CHECKING

from flaskr import create_app

if TYPE_CHECKING:
    from flask.testing import FlaskClient


def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_hello(client: 'FlaskClient'):
    response = client.get('/hello')
    assert response.data == b'Hello, World!'
