from datetime import datetime, date
from sqlalchemy import Column, Integer, String, ForeignKey, Table, Date, Boolean
from sqlalchemy.orm import declarative_base, relationship, backref
from server import db, app
import jwt
from time import time
from werkzeug.security import generate_password_hash, check_password_hash
from random import choice


Base = declarative_base()


user_games_association_table = Table(
    'user_games_association_table', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('game_id', Integer, ForeignKey('games.id'))
)


class Game(Base):
    __tablename__ = 'games'

    query = db.query_property()
    id = Column(Integer, primary_key=True)
    players = relationship('User', secondary=user_games_association_table, back_populates='games')
    prize = Column(String(200))
    prize_image = Column(String(200))
    begin_date = Column(Date)
    end_date = Column(Date)
    started_timestamp = Column(Date)
    ended_timestamp = Column(Date)
    winner = Column(Integer)
    started = Column(Boolean, default=False)
    ended = Column(Boolean, default=False)
    coins = relationship('Coin')

    def __str__(self):
        return f'< Game {self.id} />'

    def __repr__(self):
        return self.__str__()

    def __init__(self, prize, prize_image, startdate, enddate):
        self.prize = prize
        self.prize_image = prize_image
        d,m,y = startdate.split('-')
        self.begin_date = date(int(y), int(m), int(d))
        d,m,y = enddate.split('-')
        self.end_date = date(int(y), int(m), int(d))
        db.add(self)
        db.commit()
    
    def add_player(self, player):
        if self.started:
            if player in self.players:
                return False, 'You are already in the game.'
            self.players.append(player)
            db.add(self)
            db.commit()
            return True, ''
        return False, 'Game is not live.'

    def start_game(self):
        if self.winner or self.ended:
            return False, 'Game already ended.'
        self.started = True
        self.started_timestamp = datetime.utcnow()
        db.add(self)
        db.commit()
        return True, None
    
    def end_game(self):
        if not self.started:
            return False, 'Game not started.'
        if self.ended:
            return False, 'Game already ended.'
        self.ended = True
        self.ended_timestamp = datetime.utcnow()
        db.add(self)
        db.commit()
        return True, None

    def evaluate_winner(self):
        if self.players and not self.winner:
            winner = choice(self.players)
            self.winner = winner.id
            db.add(self)
            db.commit()
            return True, None
        return False, 'No players in game or winner already set.'

    def update_image(self, filename):
        self.prize_image = filename
        db.add(self)
        db.commit()

    def get_days_until_end(self):
        return (self.end_date - date.today()).days

    @staticmethod
    def get_previous_winner():
        previous_game = Game.get_previous_game()
        if previous_game:
            winner = User.query.get(previous_game.winner)
            return winner
        return None

    @staticmethod
    def get_previous_game():
        completed_games = Game.query.filter_by(started=True, ended=True).all()
        sorted_games = sorted(completed_games, key=lambda g: g.ended_timestamp, reverse=True)
        previous_game = sorted_games[0] if sorted_games else None
        return previous_game

    @staticmethod
    def get_current_live_game():
        current_game = Game.query.filter_by(
            started=True,
            ended=False
        ).first()
        return current_game



class User(Base):
    __tablename__ = 'users'

    query = db.query_property()
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    email = Column(String(50))
    password = Column(String(300))
    games = relationship('Game', secondary=user_games_association_table, back_populates='players')
    coins = relationship('Coin', back_populates='owner')
    _is_admin = Column(Boolean, default=False)

    def __str__(self):
        return f'< User #{self.id} | {self.name} />'

    def __repr__(self):
        return f'< User #{self.id} | {self.name} />'

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = generate_password_hash(password=password)
        db.add(self)
        db.commit()
    
    def get_win_count(self):
        games_won = list(filter(lambda g: g.winner == self.id, self.games))
        win_count = len(games_won)
        return win_count

    @staticmethod
    def decode_auth_token(token):
        try:
            tk = jwt.decode(token, app.config.get('SECRET_KEY'), algorithms=['HS256'])
        except (jwt.ExpiredSignatureError, Exception):
            return None
        user = User.query.filter_by(email=tk.get('email')).first()
        if user:
            return user
        return False

    def get_auth_token(self, expires_in=3600):
        token = jwt.encode({'email': self.email, 'id' : self.id , 'exp': time() + expires_in}, 
            app.config['SECRET_KEY'], algorithm='HS256').encode('utf-8')
        return token.decode('utf-8')
    
    def verify_password(self, pwd):
        return check_password_hash(self.password, pwd)

    def is_admin(self):
        return self._is_admin
    
    def make_admin(self):
        self._is_admin = True
        db.add(self)
        db.commit()
    
    def get_rare_coins_count(self):
        rare_coins = list(filter(lambda c: c.is_rare, self.coins))
        return len(rare_coins)

    def get_normal_coins_count(self):
        normal_coins = list(filter(lambda c: not c.is_rare, self.coins))
        return len(normal_coins)

    def grab_coin(self, coin):
        if coin.owner:
            return False
        if coin.update_game_id():
            self.coins.append(coin)
            db.add(self)
            db.commit()
            return True
        return False


class Coin(Base):
    __tablename__ = 'coins'

    query = db.query_property()
    id = Column(Integer, primary_key=True)
    is_rare = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    game_id = Column(Integer, ForeignKey('games.id'), nullable=True)
    owner = relationship('User', back_populates='coins')

    def __init__(self):
        db.add(self)
        db.commit()

    def __str__(self):
        o = ' - '
        r = ''
        if self.owner:
            o = self.owner.name
        if self.is_rare:
            r = 'R'
        return f'< {r} Coin #{self.id} | owner: {o}>'
    
    def __repr__(self):
        return self.__str__()

    def update_game_id(self):
        game = Game.get_current_live_game()
        if not game:
            return False
        self.game_id = game.id
        db.add(self)
        db.commit()
        return True

    @staticmethod
    def get_random_coin():
        coin = choice(Coin.query.filter_by(owner=None).all())
        return coin