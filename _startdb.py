from server import engine, db
from models import User, Base, Game


def main():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    u = User(
        name='Ana',
        email='a@a.com',
        password='joao'
    )
    u.make_admin()

    u = User(
        name='Joao',
        email='j@a.com',
        password='joao'
    )
      

if __name__ == '__main__':
    main()