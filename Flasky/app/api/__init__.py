from flask import Blueprint

bp = Blueprint('api', __name__)

from . import authentication, posts, comments, users, errors