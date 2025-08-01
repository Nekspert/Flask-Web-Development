from flask import request, jsonify, current_app, url_for, g

from . import bp
from .decorators import permission_required
from .. import db
from ..models import Comment, Post, Permissions


@bp.route('/comments/')
def get_comments():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    prev = None
    next = None
    if pagination.has_prev:
        prev = url_for('.get_comments', page=page - 1)
    if pagination.has_next:
        next = url_for('.get_comments', page=page + 1)
    return jsonify({'comments': [comment.to_json() for comment in comments],
                    'prev': prev,
                    'next': next,
                    'count': pagination.total})


@bp.route('/comments/<int:id>')
def get_comment(id):
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())


@bp.route('/posts/<int:id>/comments/')
def get_post_comments(id):
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.filter_by(post_id=post.id).order_by(Comment.timestamp.desc()).paginate(
        page=page,
        per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    prev = None
    next = None
    if pagination.has_prev:
        prev = url_for('.get_post_comments', page=page - 1)
    if pagination.has_next:
        next = url_for('.get_post_comments', page=page + 1)
    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total})


@bp.route('/posts/<int:id>/comments/', methods=['POST'])
@permission_required(Permissions.COMMENT.value)
def new_post_comment(id):
    post = Post.query.get_or_404(id)
    comment = Comment.from_json(request.json)
    comment.author = g.current_user
    comment.post = post
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_json()), 201, \
        {'Location': url_for('api.get_comment', id=comment.id)}
