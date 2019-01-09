import functools
import secrets

from flask import (abort, Blueprint, current_app, Flask, flash, g, redirect,
                   render_template, request, session, url_for, make_response)
from itsdangerous import URLSafeSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from places.db import get_db
from places.email import send_email

bp = Blueprint('auth', __name__, url_prefix='/auth')


def send_password_reset_email(user_email):
    serialiser = URLSafeSerializer(current_app.config['SECRET_KEY'])
    url = url_for(
        'auth.new_password',
        token=serialiser.dumps(user_email, salt='reset-password'),
        _external=True
    )
    text = f'Please use the URL below to reset your password:\n{url}'
    send_email(subject='Reset your password',
               recipients=[user_email],
               text_body=text)


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        cur = get_db().cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        g.user = cur.fetchone()


@bp.before_app_request
def csrf_protect():
    # Ignore csrf protection during testing
    if current_app.testing:
        pass
    elif request.method == 'POST':
        token = session.pop('_csrf_token', None)
        if not token or token != request.form['_csrf_token']:
            abort(403)


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_urlsafe()
    return session['_csrf_token']


bp.add_app_template_global(generate_csrf_token, name='csrf_token')


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
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        cur = conn.cursor()
        error = ('Email is required.' if not email else
                 'Password is required.' if not password else None)
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone() is not None:
            error = f'User {email} is already registered.'
        if error is None:
            cur.execute(
                'INSERT INTO users (email, password) VALUES (%s, %s)',
                (email, generate_password_hash(password)))
            conn.commit()
            session['email'] = email
            flash('Account creation successful! Please log in below.')
            return redirect(url_for('auth.login'))
        flash(error)
    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        cur = conn.cursor()
        error = None
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        if user is None:
            error = 'Incorrect email.'
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
    flash('You are now logged out.')
    return redirect(url_for('index'))


@bp.route('/reset_password', methods=('GET', 'POST'))
def reset_password():
    """Reset password route, accessed from link on login page."""
    if request.method == 'POST':
        email = request.form['email']
        send_password_reset_email(email)
        flash('Password reset email sent! Please check your inbox.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html')


@bp.route('/new_password', methods=('GET', 'POST',))
def new_password(token=None):
    """New password route, accessed from password reset email."""
    if request.method == 'POST':
        # New password form submitted, update pw in database and redirect
        # to login
        email = session['email']
        password = request.form['password']
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        error = ('Password is required.' if not password else
                 f'User {email} not found.' if not user else None)
        if error:
            flash(error)
        else:
            cur.execute(
                'UPDATE users SET password = %s WHERE id = %s',
                (generate_password_hash(password), user['id']))
            conn.commit()
            flash('Password succesfully updated!')
        return redirect(url_for('auth.login'))

    # Otherwise, check token and render form
    try:
        serialiser = URLSafeSerializer(current_app.config['SECRET_KEY'])
        email = serialiser.loads(request.args['token'], salt='reset-password')
    except:
        flash('The reset password link is invalid or has expired.')
        return redirect(url_for('auth.login'))
    cur = get_db().cursor()
    cur.execute("SELECT id, email FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    if not user:
        flash(f'User {email} not found.')
        return redirect(url_for('auth.login'))
    session['email'] = user['email']
    flash('Please enter your new password below.')
    return render_template('auth/new_password.html')
