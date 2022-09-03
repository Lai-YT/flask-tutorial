from typing import TYPE_CHECKING, Optional

from flask import (Blueprint, flash, g, redirect, render_template, request,
                   url_for)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

if TYPE_CHECKING:  # pragma: no cover
    from sqlite3 import Row

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    """Show all the posts."""
    db = get_db()
    posts = db.execute('''
        SELECT p.id, title, body, created, author_id, username
            FROM post p JOIN user u ON p.author_id = u.id
            ORDER BY created DESC
    ''').fetchall()
    return render_template('blog/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        error = ''
        if not title:
            error = 'Title is required.'

        if error:
            flash(error)
        else:
            with get_db() as db:
                db.execute(
                    'INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)',
                    (title, body, g.user['id'])
                ),
            return redirect(url_for('blog.index'))
    return render_template('blog/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id: int):
    post = _get_post_by_id(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        error = ''
        if not title:
            error = 'Title is required.'

        if error:
            flash(error)
        else:
            with get_db() as db:
                db.execute('UPDATE post SET title = ?, body = ? WHERE id = ?',
                           (title, body, id))
            return redirect(url_for('blog.index'))
    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id: int):
    _get_post_by_id(id)
    with get_db() as db:
        db.execute('DELETE FROM post WHERE id = ?', (id,))
    return redirect(url_for('blog.index'))


def _get_post_by_id(id: int, check_author=True):
    post: Optional['Row'] = get_db().execute('''
        SELECT p.id, title, body, created, author_id, username
            FROM post p JOIN user u ON p.author_id = u.id
            WHERE p.id = ?
    ''', (id,)).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")
    if check_author and post['author_id'] != g.user['id']:
        abort(403)
    return post
