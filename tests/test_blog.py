from http import HTTPStatus
from typing import TYPE_CHECKING, Optional

import pytest

from flaskr.db import get_db

if TYPE_CHECKING:
    from sqlite3 import Row
    from flask import Flask
    from flask.testing import FlaskClient
    from conftest import AuthActions


def test_index_page_show_login_and_register_option_before_logged_in(
        client: 'FlaskClient'):
    response = client.get('/')

    assert b'Log In' in response.data
    assert b'Register' in response.data


def test_index_page_show_logout_option_after_logged_in(
        client: 'FlaskClient', auth: 'AuthActions'):
    auth.login('test', 'test')

    response = client.get('/')

    assert b'Log Out' in response.data


def test_index_page_show_post_before_logged_in(client: 'FlaskClient'):
    response = client.get('/')

    assert b'test title' in response.data
    assert b'by test on 2022-09-02' in response.data
    assert b'test\nbody' in response.data


def test_post_not_editable_before_logged_in(client: 'FlaskClient'):
    response = client.get('/')
    assert b'Edit' not in response.data


def test_self_post_editable_after_logged_in(
        client: 'FlaskClient', auth: 'AuthActions'):
    auth.login('test', 'test')

    response = client.get('/')

    assert b'Edit' in response.data
    assert b'href="/1/update"' in response.data


def test_other_post_not_editable_even_logged_in(
        client: 'FlaskClient', auth: 'AuthActions'):
    auth.login('other', 'other')

    response = client.get('/')

    assert b'Edit' not in response.data
    assert client.post('/1/update').status_code == HTTPStatus.FORBIDDEN
    assert client.post('/1/delete').status_code == HTTPStatus.FORBIDDEN


@pytest.mark.parametrize('path', ('/create', '/1/update', '/1/delete'))
def test_login_required_before_create_update_delete(client: 'FlaskClient', path: str):
    response = client.post(path)
    assert response.headers['Location'] == '/auth/login'


@pytest.mark.parametrize('path', ('/10/update', '/10/delete'))
def test_cannot_access_not_exist_post(
        client: 'FlaskClient', auth: 'AuthActions', path: str):
    auth.login('test', 'test')

    response = client.post(path)

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_can_create_after_logged_in(client: 'FlaskClient', auth: 'AuthActions'):
    auth.login('test', 'test')

    response = client.get('create')

    assert response.status_code == HTTPStatus.OK


def test_new_post_store_in_database_after_create(
        client: 'FlaskClient', auth: 'AuthActions', app: 'Flask'):
    auth.login('test', 'test')

    client.post('/create', data={'title': 'created', 'body': ''})

    with app.app_context():
        row: Optional['Row'] = get_db().execute(
            'SELECT COUNT(id) as post_count FROM post').fetchone()
    assert row is not None and row['post_count'] == 2


def test_can_update_after_login(client: 'FlaskClient', auth: 'AuthActions'):
    auth.login('test', 'test')

    response = client.get('1/update')

    assert response.status_code == HTTPStatus.OK


def test_post_update_in_database_after_update(
        client: 'FlaskClient', auth: 'AuthActions', app: 'Flask'):
    auth.login('test', 'test')

    client.post('/1/update', data={'title': 'updated', 'body': ''})

    with app.app_context():
        post: Optional['Row'] = get_db().execute(
            'SELECT * FROM post WHERE id = 1').fetchone()
    assert post is not None and post['title'] == 'updated'


@pytest.mark.parametrize('path', ('/create', '/1/update'))
def test_create_update_title_cannot_left_empty(
        client: 'FlaskClient', auth: 'AuthActions', path: str):
    auth.login('test', 'test')

    response = client.post(path, data={'title': '', 'body': ''})

    assert b'Title is required.' in response.data


def test_redirect_to_index_page_after_delete(
        client: 'FlaskClient', auth: 'AuthActions'):
    auth.login('test', 'test')

    response = client.post('/1/delete')

    assert response.headers['Location'] == '/'


def test_post_delete_from_database_after_delete(
        client: 'FlaskClient', auth: 'AuthActions', app: 'Flask'):
    auth.login('test', 'test')

    client.post('/1/delete')

    with app.app_context():
        post: Optional['Row'] = get_db().execute(
            'SELECT 8 FROM post WHERE id = 1').fetchone()
    assert post is None
