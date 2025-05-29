from flask import render_template, redirect, url_for, request, current_app, flash, abort
from flask_login import current_user, login_required

from . import bp
from .forms import PostForm
from .services import is_safe_url
from .. import db
from ..models import Permissions, Post


@bp.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permissions.WRITE.value) and form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,
                           pagination=pagination)


@bp.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    return render_template('post.html', posts=[post])


@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permissions.ADMIN.value):
        abort(403)
    form = PostForm()
    next_page = request.args.get('next')
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('The post has been updated.')
        if next_page and is_safe_url(next_page):
            return redirect(next_page)
        else:
            return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form, next=next_page)
