import pytest
import requests
from models import User
from random import choice
from server import db


# python -m pytest -v -s -W ignore::DeprecationWarning
API = 'http://127.0.0.1:5000/api'


def token(admin):
  email = 'j@a.com'
  if admin:
    email = 'a@a.com'
  r = requests.post(f'{API}/login', json={'email': email, 'password': 'joao'})
  token = r.json().get('token')
  return token

def test_jwt_required_decorator():
  r = requests.get(f'{API}/login', headers={})
  assert r.json() == {'message': 'No authorization header defined. Log in.', 'success': False}

  r2 = requests.get(f'{API}/login', headers={'Authorization':'invalid'})
  assert r2.json() == {'message': 'No token found in authorization header.', 'success': False}

  r3 = requests.get(f'{API}/login', headers={'Authorization': 'Bearer invalid_token'})
  assert r3.json() == {'message': 'Invalid or expired token.', 'success': False}

def test_only_admins_decorator():
  r = requests.put(f'{API}/login', headers={'Authorization': f'Bearer {token(admin=False)}'})
  assert r.json() == {"message": "This is a restricted area. Keep out.","success": False}

  r = requests.put(f'{API}/login', headers={'Authorization': f'Bearer {token(admin=True)}'})
  assert r.json() == {"success": True}

def test_login():
  r = requests.post(f'{API}/login', json={'email': 'a@a.com', 'password': 'joao'})
  assert r.json().get('success') == True
  assert r.cookies.get('token') == r.json().get('token')

def test_logout():
  r = requests.delete(f'{API}/login', headers={'Cookie': f'token={token(False)}'})
  assert r.json() == {'success': True}
  assert 'token' not in r.cookies.keys()

def test_signup():
  u = User.query.filter_by(email='t@t.com').first()
  if u:
    db.delete(u)
    db.commit()

  r = requests.post(f'{API}/signup', json={'name': 'TEST', 'email': 't@t.com', 'password': 'fakepassword123'})
  assert r.json() == {'success': True, 'message': 'User created.'}

  r2 = requests.post(f'{API}/signup', json={'name': 'TEST', 'password': 'fakepassword123'})
  assert r2.json() == {'success': False, 'message': 'Missing parameters.'}

  r4 = requests.post(f'{API}/signup', json={'name': 'TEST', 'email': 't@t.com', 'password': 'fakepassword123'})
  assert r4.json() == {'success': False, 'message': 'Email registered.'}