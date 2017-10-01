import functools

import eventlet
import eventlet.wsgi
from flask import Flask, render_template, request, redirect, session, url_for
from flask_login import current_user, LoginManager, login_required
from flask_login import login_user, logout_user
from flask_session import Session
from flask_socketio import SocketIO

import SECRET
from clicker import socket_conn
from clicker import user
from clicker import auth

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'redis'
Session(app)
sio = SocketIO(app, manage_session=False)
login_manager = LoginManager()
login_manager.init_app(app)
auth = auth.Auth()


@login_manager.user_loader
def load_user(username):
    """Return user, if exists"""
    if auth.user_exists(username):
        return user.User(username)
    return None


@app.route('/')
def index():
    """No home page, redirect to login"""
    return redirect(url_for('login'))


@app.route('/game')
@login_required
def game():
    """Game screen"""
    return render_template('game.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login Users"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if auth.authenticate(username, password):
            if login_user(user.User(username)):
                return redirect(url_for('game'))
        return render_template('login.html',
                               error='Incorrect Username or Password')
    elif current_user.is_authenticated:
        return redirect(url_for('game'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout users"""
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register users"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        result = auth.register(username, password, confirm)
        if result == 'Success':
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error=result)
    return render_template('register.html')


def authenticated_only(f):
    """Check if user is authenticated on socket messages"""
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped


@sio.on('connect')
@authenticated_only
def connect():
    """Create a SockConn class on connection"""
    sock_conn = socket_conn.SockConn(request.sid, current_user.get_id())
    if not sock_conn:
        disconnect()


@sio.on('disconnect')
def disconnect():
    """On disconnect, destroy SockConn class"""
    if request.sid in socket_conn.BaseSock._sids:
        del socket_conn.BaseSock._sids[request.sid]
        del socket_conn.BaseSock._timeouts[request.sid]
    for username, sid in socket_conn.BaseSock._user_sids.copy().items():
        if sid == request.sid:
            del socket_conn.BaseSock._user_sids[username]
    if request.sid in socket_conn.BaseSock._timed_out:
        socket_conn.BaseSock._timed_out.remove(request.sid)


@sio.on('click')
@authenticated_only
def click(message):
    """Process clicks if connection exists"""
    sock_conn = socket_conn.SockConn(request.sid, current_user.get_id())
    if sock_conn:
        sock_conn.click(message)


@sio.on('update')
@authenticated_only
def update():
    """Send update if connection exists"""
    sock_conn = socket_conn.SockConn(request.sid, current_user.get_id())
    if sock_conn:
        return sock_conn.get_update()


@sio.on('upgrade')
@authenticated_only
def upgrade(json):
    """Process upgrade if connection exists"""
    sock_conn = socket_conn.SockConn(request.sid, current_user.get_id())
    if sock_conn:
        sock_conn.upgrade(json)


@sio.on('achievements')
@authenticated_only
def achievements():
    """Process achievements if connection exists"""
    sock_conn = socket_conn.SockConn(request.sid, current_user.get_id())
    if sock_conn:
        return sock_conn.achievements()


@sio.on('lottery')
@authenticated_only
def lottery(message):
    """Process lottery guess if connection exists"""
    sock_conn = socket_conn.SockConn(request.sid, current_user.get_id())
    if sock_conn:
        return sock_conn.lottery(message)


@sio.on('frenzy')
@authenticated_only
def frenzy():
    """Activate frenzy if connection exists"""
    sock_conn = socket_conn.SockConn(request.sid, current_user.get_id())
    if sock_conn:
        return sock_conn.frenzy()


if __name__ == "__main__":
    app.secret_key = SECRET.SECRET
    sio.run(app, host='0.0.0.0', port=8000, debug=True)
