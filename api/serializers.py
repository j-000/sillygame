from flask.helpers import url_for
from flask_marshmallow.sqla import HyperlinkRelated
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from flask_marshmallow import base_fields
from models import User, Game, Coin


class CoinSer(SQLAlchemyAutoSchema):
    class Meta:
        model = Coin
    owned = base_fields.Function(lambda coin: True if coin.owner else False)


class GameSer(SQLAlchemyAutoSchema):
    class Meta:
        model = Game
    players_count = base_fields.Function(lambda game: len(game.players))
    days_to_finish = base_fields.Function(lambda game: game.get_days_until_end())
    prize_image = base_fields.Function(lambda game: url_for('static', filename=game.prize_image, _external=True))


class UserSer(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        exclude = ['password', '_is_admin']
    is_admin = base_fields.Function(lambda user: user.is_admin())
    normal_coins = base_fields.Function(lambda user: user.get_normal_coins_count())
    rare_coins = base_fields.Function(lambda user: user.get_rare_coins_count())
    games_played = base_fields.Function(lambda user: len(user.games))
    games_won = base_fields.Function(lambda user: user.get_win_count())


user_serializer = UserSer()
game_serializer = GameSer()
coin_serializer = CoinSer()