from flask.helpers import url_for
from flask.json import jsonify
from werkzeug.utils import secure_filename, send_from_directory
from api.routes import (
    CoinsDetail, CoinsList, GamesDetail, 
    LiveGame, Login, Signup, UsersDetail, 
    UsersList, GamesList, UsersGamesList, 
    CoinsPool
)
from flask import request, render_template, redirect, make_response
from server import app
from models import Coin, User, Game
from config import ProdConfig, DevConfig, os
from decorators import jwt_required, only_admins
from api.serializers import user_serializer, coin_serializer


PRODUCTION, DEVELOPMENT = 'production', 'development'
API_ROUTE = '/api'


if os.environ.get('FLASK_ENV') == PRODUCTION:
    app.config.from_object(ProdConfig)
elif os.environ.get('FLASK_ENV') == DEVELOPMENT:
    app.config.from_object(DevConfig)
else:
    raise NotImplementedError('** FLASK_ENV NOT SET! **')


@app.context_processor
def global_context():
    """
    Note:
    When login in, via api or web, a cookie 'token' is set.
    This function runs AFTER @jwt_required, so we can assume
    the token is present.
    """
    token = request.cookies.get('token')
    user = User.decode_auth_token(token=token)
    if user:
        return dict(logged_user=user)
    return dict(logged_user=False)


app.add_url_rule('/api/login', view_func=Login.as_view(name='api_login'))
app.add_url_rule('/api/signup', view_func=Signup.as_view(name='api_signup'))
app.add_url_rule('/api/users', view_func=UsersList.as_view(name='users_list'))
app.add_url_rule('/api/users/<int:user_id>', view_func=UsersDetail.as_view(name='users_detail'))
app.add_url_rule('/api/users/<int:user_id>/games', view_func=UsersGamesList.as_view(name='user_games'))
app.add_url_rule('/api/games', view_func=GamesList.as_view(name='games_list'))
app.add_url_rule('/api/games/live', view_func=LiveGame.as_view(name='live_game'))
app.add_url_rule('/api/games/<int:game_id>', view_func=GamesDetail.as_view(name='games_detail'))
app.add_url_rule('/api/coins', view_func=CoinsList.as_view(name='coins_list'))
app.add_url_rule('/api/coins/pool', view_func=CoinsPool.as_view(name='coins_pool'))
app.add_url_rule('/api/coins/<int:coin_id>', view_func=CoinsDetail.as_view(name='coins_detail'))



@app.route('/')
def home():
    current_game = Game.get_current_live_game()
    previous_winner = Game.get_previous_winner()    
    previous_game = Game.get_previous_game()
    return render_template('home.html', 
        current_game=current_game, 
        previous_winner=previous_winner, 
        previous_game=previous_game)

@app.route('/profile')
@jwt_required
def profile(user):
    return render_template('protected/profile.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
@jwt_required
def logout(user):
    response = make_response(redirect('/'))
    response.delete_cookie('token')
    return response

@app.route('/play')
@jwt_required
def play(user):
    current_game_on = Game.get_current_live_game()
    if not current_game_on:
        return redirect(url_for('profile'))
    return render_template('protected/play.html')

@app.route('/_game_index')
@jwt_required
def gameindex(user):
    return render_template('protected/game_index.html')

@app.route('/games/won')
@jwt_required
def games_won(user):
    return render_template('protected/games_won.html')


@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  response.headers.add('Access-Control-Allow-Credentials', 'true')
  return response

################
# Admin Routes #
################

@app.route('/admin')
@jwt_required
@only_admins
def admin_dashboard(user):
    return render_template('protected/admin/dashboard.html')

@app.route('/admin/users')
@jwt_required
@only_admins
def admin_users(user):
    return render_template('protected/admin/admin_users.html')

@app.route('/admin/users/<int:user_id>')
@jwt_required
@only_admins
def admin_user(user_id, user):
    return render_template('protected/admin/user_detail.html')

@app.route('/admin/games')
@jwt_required
@only_admins
def admin_games(user):
    return render_template('protected/admin/admin_games.html')

@app.route('/admin/games/<int:game_id>', methods=['GET', 'POST'])
@jwt_required
@only_admins
def admin_game(game_id, user):
    if request.method == 'POST':
        if 'prizeimage' in request.files:
            file = request.files.get('prizeimage')
            filename = secure_filename(file.filename)
            if not file or not filename:
                return render_template('protected/admin/game_detail.html')
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            game = Game.query.get(int(game_id))
            game.update_image(filename)
    return render_template('protected/admin/game_detail.html')



####################################
# Game static endpoints workaround #
####################################

@app.route('/style.css')
@app.route('/scripts/supportcheck.js')
@app.route('/scripts/offlineclient.js')
@app.route('/scripts/main.js')
@app.route('/scripts/register-sw.js')
@app.route('/appmanifest.json')
@app.route('/icons/icon-256.png')
@app.route('/scripts/c3runtime.js')
@app.route('/scripts/dispatchworker.js')
@app.route('/scripts/jobworker.js')
@app.route('/data.json')
@app.route('/images/shared-0-sheet0.png')
@app.route('/images/shared-0-sheet1.png')
@app.route('/sw.js')
@app.route('/offline.json')
@app.route('/icons/loading-logo.png')
@app.route('/icons/icon-16.png')
@app.route('/icons/icon-32.png')
@app.route('/icons/icon-64.png')
@app.route('/icons/icon-128.png')
@app.route('/icons/icon-256.png')
@app.route('/icons/icon-512.png')
def game_files():
    print(request.path)
    files = {
        '/icons/loading-logo.png': 'game_statics/icons/loading-logo.png',
        '/icons/icon-16.png':'game_statics/icons/icon-16.png',
        '/icons/icon-32.png':'game_statics/icons/icon-32.png',
        '/icons/icon-64.png':'game_statics/icons/icon-64.png',
        '/icons/icon-128.png':'game_statics/icons/icon-128.png',
        '/icons/icon-256.png':'game_statics/icons/icon-256.png',
        '/icons/icon-512.png':'game_statics/icons/icon-512.png',
        '/style.css': 'game_statics/style.css',
        '/sw.js': 'game_statics/sw.js',
        '/offline.json': 'game_statics/offline.json',
        '/images/shared-0-sheet0.png': 'game_statics/images/shared-0-sheet0.png',
        '/images/shared-0-sheet1.png':'game_statics/images/shared-0-sheet1.png',
        '/data.json': 'game_statics/data.json',
        '/scripts/c3runtime.js': 'game_statics/scripts/c3runtime.js',
        '/scripts/dispatchworker.js': 'game_statics/scripts/dispatchworker.js',
        '/scripts/jobworker.js': 'game_statics/scripts/jobworker.js',
        '/icons/icon-256.png': 'game_statics/icons/icon-256.png',
        '/appmanifest.json': 'game_statics/appmanifest.json',
        '/scripts/supportcheck.js': 'game_statics/scripts/supportcheck.js',
        '/scripts/offlineclient.js': 'game_statics/scripts/offlineclient.js',
        '/scripts/main.js': 'game_statics/scripts/main.js',
        '/scripts/register-sw.js': 'game_statics/scripts/register-sw.js',
    }
    url = files[request.path]
    response = make_response(app.send_static_file(url))
    if request.path.endswith('.js'):
        response.mimetype = 'application/javascript'
    return response




if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')
