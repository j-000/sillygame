from functools import wraps
from flask import request, render_template, flash, jsonify
from models import User


def only_admins(f):
  @wraps(f)
  def wrapper(*args, **kwargs):
    auth_token = request.cookies.get('token')
    if not auth_token:
      auth_header = request.headers.get('Authorization')
      auth_token = auth_header.split()[1]
    user = User.decode_auth_token(auth_token)
    if not user.is_admin():
      return jsonify(message='This is a restricted area. Keep out.', success=False)
    return f(*args, **kwargs)
  return wrapper

def jwt_required(f):
  @wraps(f)
  def wrapper(*args, **kwargs):
    auth_token = request.cookies.get('token')
    if not auth_token:
      auth_header = request.headers.get('Authorization')
      if not auth_header:
        return jsonify(message='No authorization header defined. Log in.', success=False)
      try:
        auth_token = auth_header.split()[1]
      except:
        return jsonify(message='No token found in authorization header.', success=False)
    user = User.decode_auth_token(auth_token)
    if not user:
      return jsonify(message='Invalid or expired token.', success=False)
    return f(*args, **kwargs, user=user)
  return wrapper