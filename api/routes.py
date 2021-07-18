from random import choice
import re
from models import User, Game, Coin
from flask import jsonify, request, make_response, url_for
from flask.views import MethodView
from decorators import jwt_required, only_admins
from helper_functions import paginate, safe_int
from .serializers import user_serializer, game_serializer, coin_serializer


class CoinsPool(MethodView):
  @jwt_required
  def get(self, user):
    random_coin = choice(Coin.query.filter_by(owner=None).all())
    return jsonify(coin_serializer.dump(random_coin))
  
  @jwt_required
  def post(self, user):
    coins_string = request.json.get('coins')
    coins_ids = coins_string.split('.')
    coins_lost = []

    for id in coins_ids:
      try:
        id = int(id)
      except Exception:
        continue
      coin = Coin.query.get(id)
      if coin:
        success = user.grab_coin(coin)
        if not success:
          coins_lost.append(str(id))
      else:
        return jsonify({'success': False})
    current_game = Game.get_current_live_game()
    current_game_id = None
    if current_game:
      current_game_id = current_game.id
    coins_grabbed = len(list(filter(lambda c: c.game_id == current_game_id, user.coins)))
    response = {'success': True, 'coins_grabbed': coins_grabbed, 'coins_lost_message': ''}
    if coins_lost:
      coins_lost = ', '.join(coins_lost)
      response['coins_lost_message'] = f'Coins {coins_lost} have not been saved!'
    return jsonify(response)


class UsersGamesList(MethodView):
  @jwt_required
  def get(self, user_id, user):
    if user.is_admin():
      user_games = User.query.get(user_id).games
      return jsonify(game_serializer.dump(user_games, many=True))
    return jsonify(game_serializer.dump(user.games, many=True))


class LiveGame(MethodView):
  @jwt_required
  def get(self, user):
    game = Game.get_current_live_game()
    if not game:
      return jsonify({'success': True, 'message': 'No game currently running.', 'no_game': True})
    response = game_serializer.dump(game)
    joined_game = user in game.players
    response['joined_game'] = joined_game
    return jsonify(response)

  @jwt_required
  def post(self, user):
    game = Game.get_current_live_game()
    if not game:
      return jsonify({'success': True, 'message': 'No game currently running.'})
    action_result, message = game.add_player(user)
    return jsonify({'success': action_result, 'message': message})


class CoinsList(MethodView):
  @jwt_required
  @only_admins
  def get(self, user):
    return jsonify(paginate(
      results=Coin.query.all(),
      serializer=coin_serializer,
      url=url_for('coins_list', _external=True),
      start=safe_int(request.args.get('start', 1)),
      limit=safe_int(request.args.get('limit', 5))
    ))


class CoinsDetail(MethodView):
  @jwt_required
  @only_admins
  def get(self, coin_id, user):
    coin = Coin.query.get(safe_int(coin_id))
    return jsonify(coin_serializer.dump(coin))


class GamesList(MethodView):
  @jwt_required
  @only_admins
  def get(self, user):    
    return jsonify(paginate(
      results=Game.query.all(),
      serializer=game_serializer,
      url=url_for('games_list', _external=True),
      start=safe_int(request.args.get('start', 1)),
      limit=safe_int(request.args.get('limit', 5))
    ))

  @jwt_required
  @only_admins
  def post(self, user):
    prize = request.json.get('prize')
    startdate = request.json.get('startdate')
    enddate = request.json.get('enddate')
    if not all([prize, startdate, enddate]):
      return jsonify({'success': False, 'message': 'Missing parameters.'})
    new_game = Game(
      prize=prize,
      prize_image='',
      startdate=startdate,
      enddate=enddate
    )
    return jsonify(game_serializer.dump(new_game))


class GamesDetail(MethodView):
  @jwt_required
  @only_admins
  def get(self, game_id, user):    
    game = Game.query.get(safe_int(game_id))
    return jsonify(game_serializer.dump(game))

  @jwt_required
  @only_admins
  def post(self, game_id, user):
    game = Game.query.get(safe_int(game_id))
    action = request.json.get('action')
    ALLOWED_ACTIONS = {
      'start': game.start_game,
      'finish': game.end_game,
      'evaluateWinner': game.evaluate_winner
    }
    if action not in ALLOWED_ACTIONS:
      return jsonify({'success': False, 'message': 'Invalid action.'})
    perform_action = ALLOWED_ACTIONS[action]
    action_success, message = perform_action()
    if not action_success:
      return jsonify({'success': False, 'message': message})
    return jsonify({'success': True, 'message': 'Game updated.' })


class UsersDetail(MethodView):

  @jwt_required
  def get(self, user_id, user):
    if user.is_admin():
      requested_user = User.query.get(safe_int(user_id))
      if requested_user:
        return jsonify(user_serializer.dump(requested_user))
    return jsonify(user_serializer.dump(user))


class UsersList(MethodView):

  @jwt_required
  @only_admins
  def get(self, user):
    return jsonify(paginate(
      results=User.query.all(),
      serializer=user_serializer,
      url=url_for('users_list', _external=True),
      start=safe_int(request.args.get('start', 1)),
      limit=safe_int(request.args.get('limit', 5))
    ))


class Signup(MethodView):

  def post(self):
    if not request.json:
      return jsonify({'success': False, 'message': 'Missing json.'})
    name = request.json.get('name')
    email = request.json.get('email')
    password = request.json.get('password')
    if not all([name, email, password]):
      return jsonify({'success': False, 'message': 'Missing parameters.'})
    exists = User.query.filter_by(email=email).first()
    if exists:
      return jsonify({'success': False, 'message': 'Email registered.'})
    User(name, email, password)
    return jsonify({'success': True, 'message': 'User created.'})


class Login(MethodView):

  @jwt_required
  def get(self, user):
    return jsonify({'success': True})

  def post(self):
    if not request.json:
      return jsonify({'success': False, 'message': 'Missing json.'})
    email = request.json.get('email')
    password = request.json.get('password')
    if not email or not password:
      return jsonify({'success': False, 'message': 'Missing email/password fields.'})
    user = User.query.filter_by(email=email).first()
    if not user:
      return jsonify({'success': False, 'message': 'User is not registered.'})
    if user.verify_password(password):
      token = user.get_auth_token()
      response = make_response(jsonify({'success': True, 'token': token, 'user_id': user.id}))
      response.set_cookie('token', token)
      return response
    return jsonify({'success': False, 'message': 'Login failed.'})
      
  @jwt_required
  @only_admins
  def put(self, user):
    """
    Route used to test @only_admins decorator
    """
    return jsonify({'success': True})
  
  @jwt_required
  def delete(self, user):
    response = make_response(jsonify({'success': True}))
    response.delete_cookie('token')
    return response

  