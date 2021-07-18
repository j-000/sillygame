from flask import Flask
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={"/": {"origins": "*"}})
engine = create_engine('sqlite:///data.db', convert_unicode=True, connect_args={'check_same_thread': False})
db = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)