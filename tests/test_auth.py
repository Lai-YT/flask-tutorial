from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from flask import g, session

from flaskr.db import get_db

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient
    from conftest import AuthActions


def test_register_page_render_successfully(client: 'FlaskClient'):
    assert client.get('/auth/register').status_code == HTTPStatus.OK


def test_register_page_redirect_to_login_page_as_registration_succeeded(
        client: 'FlaskClient'):
    response = _post_register_with_username_and_password(client, 'a', 'a')
    assert response.headers['Location'] == '/auth/login'


def test_user_stored_in_database_after_registration(
        client: 'FlaskClient', app: 'Flask'):
    _post_register_with_username_and_password(client, 'a', 'a')

    with app.app_context():
        user_data = get_db().execute(
            "SELECT * FROM user WHERE username = 'a'"
        ).fetchone()

    assert user_data is not None


@pytest.mark.parametrize(
    argnames=('username', 'password', 'message'),
    argvalues=(
        ('', '', b'Username is required.'),  # username takes the priority
        ('', 'a', b'Username is required.'),
        ('a', '', b'Password is required.'),
        ('test', 'test', b'already registered')))
def test_register_validate_input(
        client: 'FlaskClient', username: str, password: str, message: str):
    response = _post_register_with_username_and_password(
        client, username, password)
    assert message in response.data


def _post_register_with_username_and_password(
        client: 'FlaskClient', username: str, password: str):
    return client.post(
        '/auth/register',
        data={'username': username, 'password': password}
    )


def test_login_page_render_successfully(client: 'FlaskClient'):
    assert client.get('/auth/login').status_code == HTTPStatus.OK


def test_login_page_redirect_to_root_page_as_login_succeeded(
        auth: 'AuthActions'):
    response = auth.login('test', 'test')
    assert response.headers['Location'] == '/'


def test_login(client: 'FlaskClient', auth: 'AuthActions'):
    auth.login(username='test', password='test')

    with client:
        client.get('/')

        assert session['user_id'] == 1
        assert g.user['username'] == 'test'


@pytest.mark.parametrize(
    argnames=('username', 'password', 'message'),
    argvalues=(
        ('a', 'a', b'Incorrect username'),  # username takes the priority
        ('a', 'test', b'Incorrect username.'),
        ('test', 'a', b'Incorrect password')))
def test_login_validate_input(
        auth: 'AuthActions', username: str, password: str, message: str):
    response = auth.login(username, password)
    assert message in response.data


def test_user_id_removed_from_session_after_logout(client: 'FlaskClient', auth: 'AuthActions'):
    auth.login('test', 'test')

    with client:
        auth.logout()

        assert 'user_id' not in session
