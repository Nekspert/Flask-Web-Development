from flask import url_for, redirect, render_template, flash, current_app, request
from flask_login import current_user, login_required

from . import bp
from .forms import EditProfileForm, EditProfileAdminForm
from .. import db
from ..decorators import admin_required, permission_required
from ..models import User, Role, Post, Permissions, Follow


@bp.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('profile/user.html', user=user, posts=posts,
                           pagination=pagination)


@bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('profile/edit_profile.html', form=form)


@bp.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id: int):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('profile/edit_profile.html', form=form, user=user)


@bp.route('/follow/<username>')
@login_required
@permission_required(Permissions.FOLLOW.value)
def follow(username: str):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash('You already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(f'You are now following {username}.')
    return redirect(url_for('.user', username=username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username: str):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        flash('You already unfollowing this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You are not following {username} anymore.')
    return redirect(url_for('.user', username=username))


@bp.route('/followers/<username>')
def followers(username: str):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = Follow.query.filter_by(followed_id=user.id).paginate(page=page,
                                                                      per_page=current_app.config[
                                                                          'FLASKY_FOLLOWERS_PER_PAGE'],
                                                                      error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('profile/followers.html', user=user, title='Followers of',
                           endpoint='.followers', pagination=pagination, follows=follows)


@bp.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = Follow.query.filter_by(follower_id=user.id).paginate(page=page,
                                                                      per_page=current_app.config[
                                                                          'FLASKY_FOLLOWERS_PER_PAGE'],
                                                                      error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('profile/followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)
