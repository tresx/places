import functools
from flask import (Blueprint, Flask, flash, g, redirect, render_template,
                   request, session, url_for, make_response)
from itsdangerous import URLSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from places.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        cur = get_db().cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        g.user = cur.fetchone()


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cur = conn.cursor()
        error = ('Username is required.' if not username else
                 'Password is required.' if not password else None)
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone() is not None:
            error = f'User {username} is already registered.'
        if error is None:
            cur.execute(
                'INSERT INTO users (username, password) VALUES (%s, %s)',
                (username, generate_password_hash(password)))
            conn.commit()
            session['username'] = username
            flash('Account creation successful! Please log in below.')
            return redirect(url_for('auth.login'))
        flash(error)
    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cur = conn.cursor()
        error = None
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        flash(error)
    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
