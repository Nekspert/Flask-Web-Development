from flask import jsonify, request, g, url_for

from . import bp
from .decorators import permission_required
from .errors import forbidden
from .. import db
from ..models import Post, Permissions


@bp.route('/posts/')
def get_posts():
    posts = Post.query.all()
    return jsonify({'posts': [post.to_json() for post in posts]})


@bp.route('/posts/<int:id>')
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())


@bp.route('/posts/', methods=['POST'])
@permission_required(Permissions.WRITE.value)
def new_post():
    post = Post.from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json()), 201, {'Location': url_for('api.get_post', id=post.id)}


@bp.route('/posts/<int:id>', methods=['PUT'])
@permission_required(Permissions.WRITE.value)
def edit_post(id):
    post = Post.query.get_or_404(id)
    if not g.current_user == post.author and not g.current_user.can(Permissions.ADMIN.value):
        return forbidden('Insufficient permissions')
    post.body = request.json.get('body', post.body)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json())
