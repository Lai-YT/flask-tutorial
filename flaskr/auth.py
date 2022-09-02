import functools
from sqlite3 import IntegrityError
from typing import Callable, Optional

from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        validator = _UsernamePasswordValidator()
        validator.validate(username, password)
        if validator.passed():
            db = get_db()
            try:
                db.execute(
                    'INSERT INTO user (username, password) VALUES (?, ?)',
                    (username, generate_password_hash(password))
                )
                db.commit()
            except IntegrityError:
                flash(f'User {username} is already registered.')
            else:
                return redirect(url_for('auth.login'))
        else:
            flash(validator.error)
    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()
        error = ''
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if not error:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        flash(error)
    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id: Optional[int] = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view: Callable):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view


class _UsernamePasswordValidator:
    def __init__(self) -> None:
        self._error: str = ''

    def validate(self, username: str, password: str) -> None:
        self._error = ''
        if not username:
            self._error = 'Username is required.'
        elif not password:
            self._error = 'Password is required.'

    def passed(self) -> bool:
        return not self._error

    @property
    def error(self) -> str:
        return self._error
