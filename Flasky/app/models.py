import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import current_app, request
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from sqlalchemy import DateTime
from werkzeug.security import generate_password_hash, check_password_hash

from . import db, login_manager


class Permissions(Enum):
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


@login_manager.user_loader
def user_load(user_id):
    return User.query.get(int(user_id))


class Role(db.Model):
    __tablename__ = 'roles'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True)
    default: so.Mapped[bool] = so.mapped_column(default=False, index=True)
    permissions: so.Mapped[int] = so.mapped_column()

    users: so.DynamicMapped[Optional['User']] = so.relationship('User', back_populates='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def add_permission(self, perm: int):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm: int):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm: int):
        return self.permissions & perm == perm

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permissions.FOLLOW.value, Permissions.WRITE.value, Permissions.COMMENT.value],
            'Moderator': [Permissions.FOLLOW.value, Permissions.WRITE.value, Permissions.COMMENT.value,
                          Permissions.MODERATE.value],
            'Administrator': [Permissions.FOLLOW.value, Permissions.WRITE.value, Permissions.COMMENT.value,
                              Permissions.MODERATE.value, Permissions.ADMIN.value]
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = role.name == default_role
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return f'<Role "{self.name}">'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True, index=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True, index=True)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(128))
    confirmed: so.Mapped[bool] = so.mapped_column(default=False)

    name: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64))
    location: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.Text())
    moment_since: so.Mapped[datetime] = so.mapped_column(DateTime(timezone=True),
                                                         default=lambda: datetime.now(tz=timezone.utc))
    last_seen: so.Mapped[datetime] = so.mapped_column(DateTime(timezone=True),
                                                      default=lambda: datetime.now(tz=timezone.utc))

    avatar_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(32))

    role_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey('roles.id'))
    role: so.Mapped[Optional[Role]] = so.relationship(Role, back_populates='users')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.__set_role()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()
        db.session.commit()

    def __set_role(self):
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self) -> str:
        s = URLSafeTimedSerializer(secret_key=current_app.config['SECRET_KEY'])
        return s.dumps({'confirm': self.id})

    def confirm(self, token: str | bytes, expiration: int = 3600) -> bool:
        s = URLSafeTimedSerializer(secret_key=current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode(), max_age=expiration)
        except SignatureExpired:
            return False
        except BadSignature:
            return False
        except Exception:
            return False

        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self) -> str:
        s = URLSafeTimedSerializer(secret_key=current_app.config['SECRET_KEY'])
        return s.dumps({'reset': self.id})

    @staticmethod
    def reset_password(token: str | bytes, new_password: str, expiration: int = 3600) -> bool:
        s = URLSafeTimedSerializer(secret_key=current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode(), max_age=expiration)
        except SignatureExpired:
            return False
        except BadSignature:
            return False
        except Exception:
            return False

        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email: str) -> str:
        s = URLSafeTimedSerializer(secret_key=current_app.config['SECRET_KEY'])
        return s.dumps({
            'change_email': self.id, 'new_email': new_email
        })

    def change_email(self, token: str | bytes, expiration: int = 3600) -> bool:
        s = URLSafeTimedSerializer(secret_key=current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode(), max_age=expiration)
        except SignatureExpired:
            return False
        except BadSignature:
            return False
        except Exception:
            return False

        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        db.session.flush()
        self.__set_role()
        return True

    def can(self, perm: int) -> bool:
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self) -> bool:
        return self.can(Permissions.ADMIN.value)

    def ping(self):
        self.last_seen = datetime.now(timezone.utc)
        db.session.add(self)
        db.session.commit()

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode()).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'

        hash = self.avatar_hash or self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def __repr__(self):
        return f'<User "{self.username}">'


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions) -> bool:
        return False

    def is_administrator(self) -> bool:
        return False


login_manager.anonymous_user = AnonymousUser
